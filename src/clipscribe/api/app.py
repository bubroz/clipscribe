from __future__ import annotations

from typing import Optional, Dict, Any, List, Set, Awaitable, Callable, Iterable, cast
import os
import json
import time
import uuid
import asyncio
import hashlib
import logging
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI, Header, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)
from starlette.responses import Response
from rq import Queue
import redis
from redis import Redis as RedisClient
# from clipscribe.config.settings import Settings  # Not needed for API
from .estimator import estimate_job
from .monitoring import get_metrics_collector, get_alert_manager, get_health_checker, setup_default_alerts
from .retry_manager import get_retry_manager


class SubmitByUrl(BaseModel):
    url: str
    options: Optional[Dict[str, Any]] = None


class SubmitByGcsUri(BaseModel):
    gcs_uri: str
    options: Optional[Dict[str, Any]] = None


class Job(BaseModel):
    job_id: str
    state: str
    progress: Dict[str, int] = Field(
        default_factory=lambda: {"current_chunk": 0, "total_chunks": 0}
    )
    cost_to_date_usd: float = 0.0
    schema_version: str = "1.0.0"
    manifest_url: Optional[str] = None
    created_at: str = Field(
        default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    )
    updated_at: str = Field(
        default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    )
    error: Optional[str] = None


class PresignRequest(BaseModel):
    filename: str
    content_type: str


class PresignResponse(BaseModel):
    upload_url: str
    gcs_uri: str


def _request_id() -> str:
    return uuid.uuid4().hex


def _error(
    code: str, message: str, status: int = 400, retry_after_seconds: Optional[int] = None
) -> JSONResponse:
    payload: Dict[str, Any] = {"code": code, "message": message}
    if retry_after_seconds is not None:
        payload["retry_after_seconds"] = retry_after_seconds
    headers = {"X-Request-ID": _request_id()}
    if status == 429 and retry_after_seconds is not None:
        headers["Retry-After"] = str(retry_after_seconds)
    return JSONResponse(status_code=status, content=payload, headers=headers)


app = FastAPI(title="ClipScribe API v1", version="1.0.0")

# Basic CORS for staging/dev; configure via env CORS_ALLOW_ORIGINS="https://*.repl.co,https://localhost:3000"
origins_raw = os.getenv("CORS_ALLOW_ORIGINS", "")
allowed_origins = [o.strip() for o in origins_raw.split(",") if o.strip()]
if allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "Retry-After"],
    )

# Redis queue and counters
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

redis_conn: Optional[RedisClient] = None
job_queue: Optional[Queue] = None
try:
    redis_conn = redis.from_url(redis_url)
    job_queue = Queue("clipscribe", connection=redis_conn)
except Exception:
    pass


@app.middleware("http")
async def add_request_id_header(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response = await call_next(request)
    if "X-Request-ID" not in response.headers:
        response.headers["X-Request-ID"] = _request_id()
    return response


# ---- In-memory state (Milestone B dev scaffold) ----
jobs_by_id: Dict[str, Job] = {}
idempotency_to_job: Dict[str, str] = {}
fingerprint_to_job: Dict[str, str] = {}
job_events: Dict[str, asyncio.Queue[str]] = {}
jobs_lock = asyncio.Lock()
processing_jobs: Set[str] = set()


# ---- Redis helpers ----
def _redis_available() -> bool:
    return redis_conn is not None


def _r_set(key: str, value: str, ex: Optional[int] = None) -> None:
    conn = redis_conn
    if conn is None:
        return
    conn.set(key, value, ex=ex)


def _r_get(key: str) -> Optional[str]:
    conn = redis_conn
    if conn is None:
        return None
    raw = cast(object, conn.get(key))
    try:
        if isinstance(raw, (bytes, bytearray)):
            return bytes(raw).decode("utf-8")
        if isinstance(raw, str):
            return raw
        return None
    except Exception:
        return None


def _r_sadd(key: str, member: str) -> None:
    conn = redis_conn
    if conn is None:
        return
    conn.sadd(key, member)


def _r_srem(key: str, member: str) -> None:
    conn = redis_conn
    if conn is None:
        return
    conn.srem(key, member)


def _r_scard(key: str) -> int:
    conn = redis_conn
    if conn is None:
        return 0
    try:
        count_raw = cast(object, conn.scard(key))
        if isinstance(count_raw, int):
            return count_raw
        # best effort cast for odd client return types
        return int(cast(Any, count_raw))
    except Exception:
        return 0


def _save_job(job: Job) -> None:
    jobs_by_id[job.job_id] = job
    if _redis_available():
        _r_set(f"cs:job:{job.job_id}", json.dumps(job.model_dump()))


def _load_job(job_id: str) -> Optional[Job]:
    j = jobs_by_id.get(job_id)
    if j:
        return j
    raw = _r_get(f"cs:job:{job_id}")
    if raw:
        try:
            data = json.loads(raw)
            return Job(**data)
        except Exception:
            return None
    return None


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ---- Metrics helpers (minimal Prometheus-style counters via Redis) ----
def _metrics_inc(name: str, amount: int = 1) -> None:
    conn = redis_conn
    if conn is None:
        return
    try:
        conn.incrby(f"cs:metrics:{name}", amount)
    except Exception:
        pass


def _metrics_dump() -> str:
    lines: List[str] = []
    conn = redis_conn
    if conn is not None:
        try:
            keys = cast(Iterable[bytes], conn.keys("cs:metrics:*"))
            for k in keys:
                v_raw = cast(object, conn.get(k))
                try:
                    if isinstance(v_raw, int):
                        val = v_raw
                    elif isinstance(v_raw, (bytes, bytearray)):
                        val = int(bytes(v_raw))
                    elif v_raw is None:
                        val = 0
                    else:
                        val = int(cast(Any, v_raw))
                except Exception:
                    val = 0
                metric = (
                    k.decode("utf-8").replace("cs:metrics:", "")
                    if isinstance(k, (bytes, bytearray))
                    else str(k)
                )
                lines.append(f"clipscribe_{metric}_total {val}")
        except Exception:
            pass
    return "\n".join(lines) + "\n"


def _validate_token(authorization: Optional[str]) -> Optional[str]:
    """Validate bearer token and return token ID if valid."""
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    token = parts[1]
    
    # Check if token exists in Redis
    conn = redis_conn
    if conn:
        token_key = f"cs:token:{token}"
        if conn.exists(token_key):
            # Token is valid, return its ID
            return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
    
    # For development/testing, accept specific tokens from environment
    valid_tokens = os.getenv("VALID_TOKENS", "").split(",")
    if token in valid_tokens and valid_tokens != ['']:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
    
    return None

def _token_id_from_auth(authorization: Optional[str]) -> Optional[str]:
    """Extract token ID from authorization header (for backwards compatibility)."""
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        tok = parts[1]
        return hashlib.sha256(tok.encode("utf-8")).hexdigest()[:16]
    return None


def _seconds_until_end_of_day_utc() -> int:
    now = datetime.now(timezone.utc)
    end = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int((end - now).total_seconds())


# ---- Sliding-window RPM (Redis Sorted Set) ----
def _rpm_allow(token_id: str, max_rpm: int, window_secs: int = 60) -> bool:
    conn = redis_conn
    if conn is None:
        return True
    try:
        key = f"cs:rpm:{token_id}"
        now_ms = int(time.time() * 1000)
        cutoff_ms = now_ms - (window_secs * 1000)
        pipe = conn.pipeline()
        # remove old
        pipe.zremrangebyscore(key, 0, cutoff_ms)
        # add current
        pipe.zadd(key, {str(now_ms): now_ms})
        # count
        pipe.zcard(key)
        # set TTL to keep key small
        pipe.expire(key, window_secs)
        _, _, count, _ = pipe.execute()
        return int(count) <= max_rpm
    except Exception:
        return True


def _fingerprint_from_body(body: Dict[str, Any]) -> str:
    if "gcs_uri" in body:
        return f"gcs:{body['gcs_uri']}|opts:{json.dumps(body.get('options') or {}, sort_keys=True)}"
    if "url" in body:
        return f"url:{body['url']}|opts:{json.dumps(body.get('options') or {}, sort_keys=True)}"
    return uuid.uuid4().hex


async def _enqueue_job_processing(job: Job, source: Dict[str, Any]) -> None:
    """Enqueue job to Cloud Tasks for processing."""
    try:
        from .task_queue import get_task_queue_manager
        
        # Prepare payload for worker
        payload = {
            "job_id": job.job_id,
            "url": source.get("url"),
            "gcs_uri": source.get("gcs_uri"),
            "options": source.get("options", {})
        }
        
        # Estimate duration for queue routing
        estimated_duration = 0
        if "url" in source:
            try:
                from .estimator import estimate_from_url
                estimated_duration, _ = estimate_from_url(source["url"])
            except Exception:
                estimated_duration = 600  # Default 10 minutes
        
        logger.info(f"Enqueuing job {job.job_id} (estimated {estimated_duration}s)")
        
        # Enqueue to Cloud Tasks
        task_manager = get_task_queue_manager()
        task_name = await asyncio.to_thread(
            task_manager.enqueue_job,
            job.job_id,
            payload,
            estimated_duration
        )
        
        if task_name:
            # Update job state
            job.state = "QUEUED"
            job.updated_at = _now_iso()
            if redis_conn:
                # Store task name in a separate key to avoid type conflicts
                redis_conn.set(f"cs:job:{job.job_id}:task_name", task_name)
            _save_job(job)
            logger.info(f"Job {job.job_id} enqueued successfully: {task_name}")
        else:
            # Failed to enqueue
            job.state = "FAILED"
            job.error = "Failed to enqueue to Cloud Tasks"
            job.updated_at = _now_iso()
            _save_job(job)
            _r_srem("cs:active_jobs", job.job_id)
            logger.error(f"Failed to enqueue job {job.job_id}")
        
    except Exception as e:
        logger.error(f"Failed to process job {job.job_id}: {e}")
        job.state = "FAILED"
        job.error = f"Failed to enqueue: {str(e)}"
        job.updated_at = _now_iso()
        _save_job(job)
        _r_srem("cs:active_jobs", job.job_id)


def _ensure_processing(job: Job, source: Dict[str, Any]) -> None:
    if job.state in {"COMPLETED", "FAILED", "CANCELED"}:
        return
    # Only enqueue if job is still in QUEUED state
    if job.state == "QUEUED":
        asyncio.create_task(_enqueue_job_processing(job, source))


@app.post("/v1/admin/pause")
async def pause_api(authorization: Optional[str] = Header(default=None, alias="Authorization")):
    # In a real application, you would protect this with a secure admin key
    if not authorization:
        return _error("unauthorized", "Missing or invalid admin token", status=401)

    _r_set("cs:api:paused", "1", ex=3600)  # Pauses for 1 hour
    return {"status": "API processing is now paused for one hour."}

@app.post("/v1/admin/resume")
async def resume_api(authorization: Optional[str] = Header(default=None, alias="Authorization")):
    # In a real application, you would protect this with a secure admin key
    if not authorization:
        return _error("unauthorized", "Missing or invalid admin token", status=401)
    
    conn = redis_conn
    if conn:
        conn.delete("cs:api:paused")
    return {"status": "API processing is now resumed."}

@app.post("/v1/admin/tokens")
async def create_token(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    body: Dict[str, Any] = {}
):
    """Create a new beta access token."""
    # In production, this should require admin authentication
    if not authorization or "admin" not in authorization.lower():
        return _error("unauthorized", "Admin access required", status=401)
    
    import secrets
    
    # Generate token
    tier = body.get("tier", "beta")
    email = body.get("email", "")
    token = f"{tier[:3]}_{secrets.token_urlsafe(16)}"
    
    # Store in Redis
    if redis_conn:
        token_key = f"cs:token:{token}"
        redis_conn.hset(token_key, mapping={
            "email": email,
            "tier": tier,
            "created": _now_iso(),
            "monthly_limit": 50,  # Beta limit
            "videos_used": 0,
            "status": "active"
        })
        # Token expires in 30 days for beta
        redis_conn.expire(token_key, 30 * 24 * 3600)
    
    return {
        "token": token,
        "tier": tier,
        "email": email,
        "expires_in_days": 30
    }


@app.post("/v1/jobs", response_model=None, status_code=202)
async def create_job(
    req: Request,
    body: Dict[str, Any],
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> JSONResponse | Job:
    # Validate token
    token_id = _validate_token(authorization)
    if not token_id:
        return _error("invalid_input", "Missing or invalid bearer token", status=401)

    # Check if the API is paused
    if _r_get("cs:api:paused") == "1":
        return _error("service_unavailable", "The API is temporarily paused for maintenance.", status=503, retry_after_seconds=300)

    if not ("url" in body or "gcs_uri" in body):
        return _error("invalid_input", "Provide either url or gcs_uri", status=400)

    # Per-token RPM & daily budget counters (Redis) with reservation-based budgeting
    # token_id already validated above
    if token_id and _redis_available():
        # RPM (sliding-window)
        max_rpm = int(os.getenv("TOKEN_MAX_RPM", "60"))
        if not _rpm_allow(token_id, max_rpm, 60):
            _metrics_inc("rpm_rejects")
            return _error(
                "rate_limited", "Per-token RPM exceeded", status=429, retry_after_seconds=10
            )
        # Daily requests cap
        day_key = f"cs:lim:{token_id}:day:{datetime.utcnow().strftime('%Y%m%d')}"
        day_count = int(cast(Any, redis_conn.incr(day_key))) if redis_conn else 0
        if redis_conn and day_count == 1:
            redis_conn.expire(day_key, _seconds_until_end_of_day_utc())
        max_daily = int(os.getenv("TOKEN_MAX_DAILY_REQUESTS", "2000"))
        if day_count > max_daily:
            _metrics_inc("daily_request_rejects")
            return _error(
                "rate_limited", "Daily request quota exceeded", status=429, retry_after_seconds=3600
            )

        # USD budget reservation based on real estimate
        estimate = estimate_job(body, None)  # Settings not needed for estimation
        est_cost = float(estimate.get("estimated_cost_usd", 0.01))
        max_usd = float(os.getenv("TOKEN_DAILY_BUDGET_USD", "5.0"))
        budget_key = f"cs:budget:{token_id}:{datetime.utcnow().strftime('%Y%m%d')}"
        # Simple atomic reserve using MULTI/EXEC (Lua would be ideal; kept simple here)
        pipe = redis_conn.pipeline() if redis_conn else None
        current = None
        if pipe is not None:
            pipe.get(budget_key)
            current = pipe.execute()[0]
        try:
            cur_spend = float(current) if current is not None else 0.0
        except Exception:
            cur_spend = 0.0
        if cur_spend + est_cost > max_usd:
            retry = _seconds_until_end_of_day_utc()
            _metrics_inc("budget_rejects")
            return _error(
                "budget_exceeded", "Daily budget exceeded", status=429, retry_after_seconds=retry
            )
        # Reserve
        try:
            if redis_conn is not None:
                redis_conn.incrbyfloat(budget_key, est_cost)
                if current is None:
                    redis_conn.expire(budget_key, _seconds_until_end_of_day_utc())
            _metrics_inc("budget_reserves")
        except Exception:
            pass

    # Simple admission control: throttle if too many active jobs (Redis-backed)
    active_jobs = _r_scard("cs:active_jobs")
    throttle_limit = int(os.getenv("ADMISSION_ACTIVE_LIMIT", "100"))
    if active_jobs >= throttle_limit:
        return _error("rate_limited", "Too many active jobs", status=429, retry_after_seconds=10)

    fp = _fingerprint_from_body(body)
    async with jobs_lock:
        if idempotency_key:
            existing_id = _r_get(f"cs:idmp:{idempotency_key}") or idempotency_to_job.get(
                idempotency_key
            )
            if existing_id:
                j = _load_job(existing_id)
                if j:
                    _ensure_processing(j, body)
                    return j
        existing_fp_id = _r_get(f"cs:fp:{fp}") or fingerprint_to_job.get(fp)
        if existing_fp_id:
            j = _load_job(existing_fp_id)
            if j:
                _ensure_processing(j, body)
                return j

        job_id = uuid.uuid4().hex
        bucket = os.getenv("GCS_BUCKET", "mock-bucket")
        manifest_url = f"https://storage.googleapis.com/{bucket}/jobs/{job_id}/manifest.json"
        job = Job(job_id=job_id, state="QUEUED", manifest_url=manifest_url)
        _save_job(job)
        fingerprint_to_job[fp] = job_id
        _r_set(f"cs:fp:{fp}", job_id, ex=7 * 24 * 3600)
        if idempotency_key:
            idempotency_to_job[idempotency_key] = job_id
            _r_set(f"cs:idmp:{idempotency_key}", job_id, ex=24 * 3600)
        _r_sadd("cs:active_jobs", job_id)

    # Enqueue job for processing
    asyncio.create_task(_enqueue_job_processing(job, body))
    return job


@app.get("/v1/jobs/{job_id}", response_model=None)
async def get_job(
    job_id: str, authorization: Optional[str] = Header(default=None, alias="Authorization")
) -> JSONResponse | Job:
    if not authorization:
        return _error("invalid_input", "Missing or invalid bearer token", status=401)
    # Mock status
    job = _load_job(job_id)
    if not job:
        return _error("invalid_input", "Job not found", status=404)
    return job


@app.get("/v1/jobs/{job_id}/events", response_model=None)
async def get_job_events(
    job_id: str, authorization: Optional[str] = Header(default=None, alias="Authorization")
):
    if not authorization:
        return _error("invalid_input", "Missing or invalid bearer token", status=401)
    q = job_events.setdefault(job_id, asyncio.Queue())

    async def stream() -> Any:
        # If job exists, push current state snapshot first
        job = jobs_by_id.get(job_id)
        if job:
            yield "event: status\n" + f'data: {{"state":"{job.state}"}}\n\n'
            yield "event: progress\n" + f"data: {json.dumps(job.progress)}\n\n"
        while True:
            msg = await q.get()
            yield msg

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/v1/status", response_model=None)
async def get_status(authorization: Optional[str] = Header(default=None, alias="Authorization")):
    if not authorization:
        return _error("invalid_input", "Missing or invalid bearer token", status=401)
    return {"status": "healthy"}


@app.get("/v1/jobs/{job_id}/artifacts", response_model=None)
async def list_artifacts(
    job_id: str, authorization: Optional[str] = Header(default=None, alias="Authorization")
):
    if not authorization:
        return _error("invalid_input", "Missing or invalid bearer token", status=401)
    bucket = os.getenv("GCS_BUCKET")
    artifacts: List[Dict[str, Any]] = []
    if bucket:
        try:
            from google.cloud import storage  # type: ignore

            client = storage.Client()
            prefix = f"jobs/{job_id}/"
            for blob in client.list_blobs(bucket, prefix=prefix):
                name = getattr(blob, "name", "")
                if not name or name.endswith("/"):
                    continue
                kind = "manifest_json" if name.endswith("manifest.json") else "file"
                size_bytes = int(getattr(blob, "size", 0) or 0)
                public_url = f"https://storage.googleapis.com/{bucket}/{name}"
                url = None
                requires_auth = True
                try:
                    # Prefer signed URL when service account has signing capability
                    url = blob.generate_signed_url(version="v4", expiration=900, method="GET")
                    requires_auth = False
                except Exception:
                    # Fall back to public URL (will 403 for anonymous); still return entry for clients using creds
                    url = public_url
                artifacts.append(
                    {
                        "id": os.path.basename(name),
                        "kind": kind,
                        "size_bytes": size_bytes,
                        "url": url,
                        "requires_auth": requires_auth,
                    }
                )
        except Exception as e:
            print(f"[warn] listing artifacts failed for gs://{bucket}/jobs/{job_id}/: {e}")
    return {"job_id": job_id, "artifacts": artifacts}


@app.get("/v1/estimate", response_model=None)
async def estimate(
    url: Optional[str] = None,
    gcs_uri: Optional[str] = None,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> JSONResponse | Dict[str, Any]:
    if not authorization:
        return _error("invalid_input", "Missing or invalid bearer token", status=401)
    # Simple placeholder estimate: fixed duration and cost, propose flash
    return {
        "estimated_cost_usd": 0.035,
        "estimated_duration_seconds": 120,
        "proposed_model": "flash",
        "admission": "allowed",
        "reason": "Within plan caps",
    }


@app.post("/v1/uploads/presign", response_model=None)
async def presign_upload(
    req: PresignRequest, authorization: Optional[str] = Header(default=None, alias="Authorization")
) -> PresignResponse | JSONResponse:
    if not authorization:
        return _error("invalid_input", "Missing or invalid bearer token", status=401)

    bucket = os.getenv("GCS_BUCKET")
    if bucket:
        try:
            from google.cloud import storage  # type: ignore

            client = storage.Client()
            # Path: tmp/<uuid>/<filename>
            object_path = f"uploads/{uuid.uuid4().hex}/{req.filename}"
            blob = client.bucket(bucket).blob(object_path)
            upload_url = blob.generate_signed_url(
                version="v4",
                expiration=900,  # 15 minutes
                method="PUT",
                content_type=req.content_type,
            )
            gcs_uri = f"gs://{bucket}/{object_path}"
            return PresignResponse(upload_url=upload_url, gcs_uri=gcs_uri)
        except Exception:
            # Fall through to mock if signing fails
            pass

    # Mock fallback
    bucket = bucket or "mock-bucket"
    upload_url = f"https://storage.googleapis.com/{bucket}/uploads/{uuid.uuid4().hex}?signature=mock"
    gcs_uri = f"gs://{bucket}/uploads/{uuid.uuid4().hex}/{req.filename}"
    return PresignResponse(upload_url=upload_url, gcs_uri=gcs_uri)


def run() -> None:
    import uvicorn

    uvicorn.run(
        "clipscribe.api.app:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(str(os.getenv("PORT", "8080"))),
        reload=bool(os.getenv("UVICORN_RELOAD", "false").lower() == "true"),
    )


@app.get("/metrics")
async def metrics() -> Response:
    # Minimal text exposition for quick scraping
    content = _metrics_dump()
    from fastapi.responses import PlainTextResponse

    return PlainTextResponse(content)


# ---- Monitoring Endpoints ----
@app.get("/v1/health")
async def health_check():
    """Comprehensive health check for the API service."""
    try:
        # Check Redis connectivity
        if redis_conn:
            redis_conn.ping()

        # Check GCS access if configured
        gcs_status = "not_configured"
        bucket = os.getenv("GCS_BUCKET")
        if bucket:
            try:
                from google.cloud import storage
                client = storage.Client()
                client.bucket(bucket).reload()
                gcs_status = "healthy"
            except Exception:
                gcs_status = "unhealthy"

        # Check queue availability
        queue_status = "healthy" if job_queue else "not_configured"

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "redis": True if redis_conn else False,
            "gcs": gcs_status,
            "queue": queue_status,
            "version": "1.0.0"
        }

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@app.get("/v1/monitoring/metrics")
async def get_monitoring_metrics():
    """Get comprehensive monitoring metrics."""
    try:
        metrics_collector = get_metrics_collector(redis_conn)
        alert_manager = get_alert_manager(redis_conn)

        # Collect current metrics
        metrics_collector.collect_system_metrics()
        metrics_collector.collect_application_metrics(redis_conn)

        # Get active alerts
        alerts = alert_manager.get_active_alerts()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system_metrics": {
                "cpu_usage_percent": metrics_collector.get_metric("cpu_usage_percent"),
                "memory_usage_percent": metrics_collector.get_metric("memory_usage_percent"),
                "disk_usage_percent": metrics_collector.get_metric("disk_usage_percent")
            },
            "application_metrics": {
                "active_jobs": _r_scard("cs:active_jobs"),
                "queue_backlog": _r_scard("cs:queue:short") + _r_scard("cs:queue:long")
            },
            "alerts": {
                "active_count": len(alerts),
                "critical_count": len([a for a in alerts if a.get('severity') == 'critical']),
                "active_alerts": alerts[:10]  # Limit to 10 most recent
            }
        }

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to get monitoring metrics: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@app.get("/v1/monitoring/alerts")
async def get_alerts():
    """Get current active alerts."""
    try:
        alert_manager = get_alert_manager(redis_conn)
        alerts = alert_manager.get_active_alerts()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "active_alerts": alerts,
            "total_count": len(alerts),
            "critical_count": len([a for a in alerts if a.get('severity') == 'critical'])
        }

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to get alerts: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "active_alerts": [],
            "total_count": 0
        }


@app.get("/v1/monitoring/queue-status")
async def get_queue_status():
    """Get detailed queue status for monitoring."""
    try:
        short_queue_len = _r_scard("cs:queue:short")
        long_queue_len = _r_scard("cs:queue:long")
        active_jobs = _r_scard("cs:active_jobs")

        # Get job states distribution
        job_states = {}
        if redis_conn:
            try:
                pattern = "cs:job:*"
                for key in redis_conn.scan_iter(pattern):
                    state = redis_conn.hget(key, "state")
                    if state:
                        state_str = state.decode()
                        job_states[state_str] = job_states.get(state_str, 0) + 1
            except:
                pass

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "queues": {
                "short": short_queue_len,
                "long": long_queue_len,
                "total": short_queue_len + long_queue_len
            },
            "active_jobs": active_jobs,
            "job_states": job_states,
            "redis_available": True
        }

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to get queue status: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "redis_available": False
        }


@app.get("/v1/monitoring/dead-letter-queue")
async def get_dead_letter_queue(limit: int = 20):
    """Get contents of dead letter queue."""
    try:
        retry_manager = get_retry_manager(redis_conn)
        dead_letters = retry_manager.get_dead_letter_queue(limit)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "dead_letters": dead_letters,
            "total_count": len(dead_letters)
        }

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to get dead letter queue: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "dead_letters": [],
            "total_count": 0
        }

@app.get("/v1/monitoring/task-queues")
async def get_task_queue_status():
    """Get Cloud Tasks queue statistics."""
    try:
        from .task_queue import get_task_queue_manager
        task_manager = get_task_queue_manager()
        stats = await asyncio.to_thread(task_manager.get_queue_stats)
        return stats
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to get task queue stats: {e}")
        return {"error": str(e)}
