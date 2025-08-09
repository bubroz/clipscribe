from __future__ import annotations

import os
import json
import time
from typing import Dict, Any

from rq import Worker, Queue, Connection
import redis


def process_job(job_id: str, payload: Dict[str, Any]) -> None:
    """Dummy worker: writes a second artifact (report.md) to GCS for validation."""
    bucket = os.getenv("GCS_BUCKET")
    if not bucket:
        return
    try:
        from google.cloud import storage  # type: ignore

        client = storage.Client()
        blob = client.bucket(bucket).blob(f"jobs/{job_id}/report.md")
        content = f"# ClipScribe Report\n\nJob: {job_id}\nCreated: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n"
        blob.upload_from_string(content, content_type="text/markdown")
    except Exception:
        pass


def run() -> None:
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_conn = redis.from_url(url)
    with Connection(redis_conn):
        w = Worker([Queue("clipscribe")])
        w.work(with_scheduler=True)


