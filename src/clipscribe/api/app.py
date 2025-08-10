from __future__ import annotations

from typing import Optional, Dict, Any, List
import os
import json
import time
import uuid
import asyncio
import hashlib
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI, Header, HTTPException, Response, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from rq import Queue
import redis


class SubmitByUrl(BaseModel):
    url: str
    options: Optional[Dict[str, Any]] = None


class SubmitByGcsUri(BaseModel):
    gcs_uri: str
    options: Optional[Dict[str, Any]] = None


class Job(BaseModel):
    job_id: str
    state: str
    progress: Dict[str, int] = Field(default_factory=lambda: {"current_chunk": 0, "total_chunks": 0})
    cost_to_date_usd: float = 0.0
    schema_version: str = "1.0.0"
    manifest_url: Optional[str] = None
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    updated_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    error: Optional[str] = None


class PresignRequest(BaseModel):
    filename: str
    content_type: str


class PresignResponse(BaseModel):
    upload_url: str
    gcs_uri: str


def _request_id() -> str:
    return uuid.uuid4().hex


def _error(code: str, message: str, status: int = 400, retry_after_seconds: Optional[int] = None) -> JSONResponse:
    payload = {"code": code, "message": message}
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
redis_conn = None
job_queue: Optional[Queue] = None
try:
    redis_conn = redis.from_url(redis_url)
    job_queue = Queue("clipscribe", connection=redis_conn)
except Exception:
    pass


@app.middleware("http")
async def add_request_id_header(request: Request, call_next):
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


# ---- Redis helpers ----
def _redis_available() -> bool:
    return redis_conn is not None


def _r_set(key: str, value: str, ex: Optional[int] = None) -> None:
    if _redis_available():
        redis_conn.set(key, value, ex=ex)


def _r_get(key: str) -> Optional[str]:
    if _redis_available():
        v = redis_conn.get(key)
        return v.decode("utf-8") if v is not None else None
    return None


def _r_sadd(key: str, member: str) -> None:
    if _redis_available():
        redis_conn.sadd(key, member)


def _r_srem(key: str, member: str) -> None:
    if _redis_available():
        redis_conn.srem(key, member)


def _r_scard(key: str) -> int:
    if _redis_available():
        try:
            return int(redis_conn.scard(key))
        except Exception:
            return 0
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


def _token_id_from_auth(authorization: Optional[str]) -> Optional[str]:
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


def _fingerprint_from_body(body: Dict[str, Any]) -> str:
    if "gcs_uri" in body:
        return f"gcs:{body['gcs_uri']}|opts:{json.dumps(body.get('options') or {}, sort_keys=True)}"
    if "url" in body:
        return f"url:{body['url']}|opts:{json.dumps(body.get('options') or {}, sort_keys=True)}"
    return uuid.uuid4().hex


async def _enqueue_job_processing(job: Job, source: Dict[str, Any]) -> None:
    """Simulate background processing and write manifest to GCS."""
    q = job_events.setdefault(job.job_id, asyncio.Queue())
    # Update states with small delays
    async def push(event: str, data: Dict[str, Any]) -> None:
        await q.put(f"event: {event}\n" + f"data: {json.dumps(data)}\n\n")

    async def set_state(state: str, progress: Optional[Dict[str, int]] = None) -> None:
        job.state = state
        job.updated_at = _now_iso()
        if progress:
            job.progress = progress
        _save_job(job)
        await push("status", {"state": state})
        await push("progress", job.progress)

    await set_state("DOWNLOADING", {"current_chunk": 0, "total_chunks": 6})
    await asyncio.sleep(0.2)
    await set_state("ANALYZING", {"current_chunk": 3, "total_chunks": 6})
    await asyncio.sleep(0.2)

    # Write manifest to GCS
    bucket = os.getenv("GCS_BUCKET")
    manifest_obj_path = f"jobs/{job.job_id}/manifest.json"
    manifest_content = {
        "job_id": job.job_id,
        "schema_version": job.schema_version,
        "source": source,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }
    if bucket:
        try:
            from google.cloud import storage  # type: ignore

            client = storage.Client()
            blob = client.bucket(bucket).blob(manifest_obj_path)
            blob.cache_control = "public, max-age=300"
            # Explicitly pass content_type to the upload call to ensure header matches
            blob.upload_from_string(
                json.dumps(manifest_content, separators=(",", ":")),
                content_type="application/json",
            )
        except Exception as e:
            # Surface write failures during dev
            print(f"[warn] failed to write manifest to gs://{bucket}/{manifest_obj_path}: {e}")

    job.manifest_url = f"https://storage.googleapis.com/{bucket or 'mock-bucket'}/{manifest_obj_path}"
    await asyncio.sleep(0.1)
    await set_state("WRITING_ARTIFACTS", {"current_chunk": 6, "total_chunks": 6})
    await push("cost", {"usd": 0.003})
    job.state = "COMPLETED"
    job.updated_at = _now_iso()
    _save_job(job)
    _r_srem("cs:active_jobs", job.job_id)
    await push("done", {"job_id": job.job_id})


@app.post("/v1/jobs", response_model=Job, status_code=202)
async def create_job(
    req: Request,
    body: Dict[str, Any],
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
):
    if not authorization:
        return _error("invalid_input", "Missing or invalid bearer token", status=401)

    if not ("url" in body or "gcs_uri" in body):
        return _error("invalid_input", "Provide either url or gcs_uri", status=400)

    # Per-token RPM & daily budget counters (Redis)
    token_id = _token_id_from_auth(authorization)
    if token_id and _redis_available():
        # RPM
        rpm_key = f"cs:lim:{token_id}:rpm:{int(time.time() // 60)}"
        rpm = int(redis_conn.incr(rpm_key))
        if rpm == 1:
            redis_conn.expire(rpm_key, 60)
        max_rpm = int(os.getenv("TOKEN_MAX_RPM", "60"))
        if rpm > max_rpm:
            return _error("rate_limited", "Per-token RPM exceeded", status=429, retry_after_seconds=10)
        # Daily budget (simple request-count based proxy)
        day_key = f"cs:lim:{token_id}:day:{datetime.utcnow().strftime('%Y%m%d')}"
        day_count = int(redis_conn.incr(day_key))
        if day_count == 1:
            redis_conn.expire(day_key, _seconds_until_end_of_day_utc())
        max_daily = int(os.getenv("TOKEN_MAX_DAILY_REQUESTS", "2000"))
        if day_count > max_daily:
            return _error("budget_exceeded", "Daily quota exceeded", status=429, retry_after_seconds=3600)

    # Simple admission control: throttle if too many active jobs (Redis-backed)
    active_jobs = _r_scard("cs:active_jobs")
    throttle_limit = int(os.getenv("ADMISSION_ACTIVE_LIMIT", "100"))
    if active_jobs >= throttle_limit:
        return _error("rate_limited", "Too many active jobs", status=429, retry_after_seconds=10)

    fp = _fingerprint_from_body(body)
    async with jobs_lock:
        if idempotency_key:
            existing_id = _r_get(f"cs:idmp:{idempotency_key}") or idempotency_to_job.get(idempotency_key)
            if existing_id:
                j = _load_job(existing_id)
                if j:
                    return j
        existing_fp_id = _r_get(f"cs:fp:{fp}") or fingerprint_to_job.get(fp)
        if existing_fp_id:
            j = _load_job(existing_fp_id)
            if j:
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

    # Start background processing and enqueue worker side-effect
    asyncio.create_task(_enqueue_job_processing(job, body))
    try:
        if job_queue is not None:
            job_queue.enqueue("clipscribe.api.worker.process_job", job_id, body, job_timeout=600)
    except Exception:
        # ignore enqueue failures in dev
        pass
    return job


@app.get("/v1/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str, authorization: Optional[str] = Header(default=None, alias="Authorization")):
    if not authorization:
        return _error("invalid_input", "Missing or invalid bearer token", status=401)
    # Mock status
    job = _load_job(job_id)
    if not job:
        return _error("invalid_input", "Job not found", status=404)
    return job


@app.get("/v1/jobs/{job_id}/events")
async def get_job_events(job_id: str, authorization: Optional[str] = Header(default=None, alias="Authorization")):
    if not authorization:
        return _error("invalid_input", "Missing or invalid bearer token", status=401)
    q = job_events.setdefault(job_id, asyncio.Queue())

    async def stream():
        # If job exists, push current state snapshot first
        job = jobs_by_id.get(job_id)
        if job:
            yield "event: status\n" + f"data: {{\"state\":\"{job.state}\"}}\n\n"
            yield "event: progress\n" + f"data: {json.dumps(job.progress)}\n\n"
        while True:
            msg = await q.get()
            yield msg

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/v1/jobs/{job_id}/artifacts")
async def list_artifacts(job_id: str, authorization: Optional[str] = Header(default=None, alias="Authorization")):
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
                url = blob.generate_signed_url(version="v4", expiration=900, method="GET")
                kind = "manifest_json" if name.endswith("manifest.json") else "file"
                size_bytes = int(getattr(blob, "size", 0) or 0)
                artifacts.append({
                    "id": os.path.basename(name),
                    "kind": kind,
                    "size_bytes": size_bytes,
                    "url": url,
                })
        except Exception as e:
            print(f"[warn] listing artifacts failed for gs://{bucket}/jobs/{job_id}/: {e}")
    return {"job_id": job_id, "artifacts": artifacts}


@app.get("/v1/estimate")
async def estimate(url: Optional[str] = None, gcs_uri: Optional[str] = None, authorization: Optional[str] = Header(default=None, alias="Authorization")):
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


@app.post("/v1/uploads/presign", response_model=PresignResponse)
async def presign_upload(req: PresignRequest, authorization: Optional[str] = Header(default=None, alias="Authorization")):
    if not authorization:
        return _error("invalid_input", "Missing or invalid bearer token", status=401)

    bucket = os.getenv("GCS_BUCKET")
    if bucket:
        try:
            from google.cloud import storage  # type: ignore

            client = storage.Client()
            # Path: tmp/<uuid>/<filename>
            object_path = f"tmp/{uuid.uuid4().hex}/{req.filename}"
            blob = client.bucket(bucket).blob(object_path)
            upload_url = blob.generate_signed_url(
                version="v4",
                expiration=900,  # 15 minutes
                method="PUT",
                content_type=req.content_type,
            )
            gcs_uri = f"gs://{bucket}/{object_path}"
            return PresignResponse(upload_url=upload_url, gcs_uri=gcs_uri)
        except Exception as e:
            # Fall through to mock if signing fails
            pass

    # Mock fallback
    bucket = bucket or "mock-bucket"
    upload_url = f"https://storage.googleapis.com/{bucket}/tmp/{uuid.uuid4().hex}?signature=mock"
    gcs_uri = f"gs://{bucket}/tmp/{uuid.uuid4().hex}/{req.filename}"
    return PresignResponse(upload_url=upload_url, gcs_uri=gcs_uri)


def run():
    import uvicorn

    uvicorn.run(
        "clipscribe.api.app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        reload=bool(os.getenv("UVICORN_RELOAD", "false").lower() == "true"),
    )


