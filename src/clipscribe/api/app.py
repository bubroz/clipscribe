from __future__ import annotations

from typing import Optional, Dict, Any
import os
import json
import time
import uuid

from fastapi import FastAPI, Header, HTTPException, Response, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware


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


@app.middleware("http")
async def add_request_id_header(request: Request, call_next):
    response = await call_next(request)
    if "X-Request-ID" not in response.headers:
        response.headers["X-Request-ID"] = _request_id()
    return response


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

    # Mock acceptance, generate job id
    job_id = uuid.uuid4().hex
    bucket = os.getenv("GCS_BUCKET", "mock-bucket")
    manifest_url = f"https://storage.googleapis.com/{bucket}/jobs/{job_id}/manifest.json"
    return Job(job_id=job_id, state="QUEUED", manifest_url=manifest_url)


@app.get("/v1/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str, authorization: Optional[str] = Header(default=None, alias="Authorization")):
    if not authorization:
        return _error("invalid_input", "Missing or invalid bearer token", status=401)
    # Mock status
    return Job(job_id=job_id, state="ANALYZING", progress={"current_chunk": 1, "total_chunks": 6})


@app.get("/v1/jobs/{job_id}/events")
async def get_job_events(job_id: str, authorization: Optional[str] = Header(default=None, alias="Authorization")):
    if not authorization:
        return _error("invalid_input", "Missing or invalid bearer token", status=401)

    async def event_stream():
        yield "event: status\n" + "data: {\"state\":\"DOWNLOADING\"}\n\n"
        yield "event: progress\n" + "data: {\"current_chunk\":1,\"total_chunks\":6}\n\n"
        yield "event: cost\n" + "data: {\"usd\":0.003}\n\n"
        yield "event: done\n" + f"data: {{\"job_id\":\"{job_id}\"}}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


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


