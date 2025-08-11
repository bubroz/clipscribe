from __future__ import annotations

import os
import json
import tempfile
import asyncio
from typing import Dict, Any

from rq import Worker, Queue, Connection
import redis


async def _process_payload(job_id: str, payload: Dict[str, Any]) -> None:
    """Process a job: transcribe/analyze and write artifacts to GCS."""
    bucket = os.getenv("GCS_BUCKET")
    if not bucket:
        return

    from google.cloud import storage  # type: ignore

    client = storage.Client()
    bucket_ref = client.bucket(bucket)

    # Helper to upload
    def upload_bytes(path: str, data: bytes, content_type: str) -> None:
        blob = bucket_ref.blob(path)
        blob.cache_control = "public, max-age=300"
        blob.upload_from_string(data, content_type=content_type)

    artifacts = []

    try:
        # Case 1: Direct URL processing via yt-dlp + Gemini
        if "url" in payload:
            from clipscribe.retrievers.universal_video_client import EnhancedUniversalVideoClient
            from clipscribe.retrievers.transcriber import GeminiFlashTranscriber

            uvc = EnhancedUniversalVideoClient()
            tmpdir = tempfile.mkdtemp()
            audio_path, metadata = await uvc.download_audio(payload["url"], output_dir=tmpdir)

            duration = int(getattr(metadata, "duration", 0) or 0)
            transcriber = GeminiFlashTranscriber(use_pro=False)
            analysis = await transcriber.transcribe_audio(audio_path, duration)

            # transcript.json
            transcript_json = json.dumps(analysis, separators=(",", ":")).encode("utf-8")
            upload_bytes(f"jobs/{job_id}/transcript.json", transcript_json, "application/json")
            artifacts.append("transcript.json")

            # simple report.md
            report_md = (
                f"# ClipScribe Report\n\nJob: {job_id}\nURL: {payload['url']}\n\n"
                f"Summary: {analysis.get('summary','')[:500]}\n\n"
                f"Entities: {len(analysis.get('entities', []))}, Relationships: {len(analysis.get('relationships', []))}\n"
            ).encode("utf-8")
            upload_bytes(f"jobs/{job_id}/report.md", report_md, "text/markdown")
            artifacts.append("report.md")

        # Case 2: gcs_uri processing via Vertex AI
        elif "gcs_uri" in payload:
            from clipscribe.retrievers.vertex_ai_transcriber import VertexAITranscriber

            vtx = VertexAITranscriber()
            result = await vtx.transcribe_with_vertex(
                gcs_uri=payload["gcs_uri"], enhance_transcript=False, mode="video"
            )
            transcript_json = json.dumps(result, default=str, separators=(",", ":")).encode("utf-8")
            upload_bytes(f"jobs/{job_id}/transcript.json", transcript_json, "application/json")
            artifacts.append("transcript.json")

            report_md = (
                f"# ClipScribe Report\n\nJob: {job_id}\nGCS: {payload['gcs_uri']}\n\n"
                f"Entities: {len(result.get('entities', []))}, Relationships: {len(result.get('relationships', []))}\n"
            ).encode("utf-8")
            upload_bytes(f"jobs/{job_id}/report.md", report_md, "text/markdown")
            artifacts.append("report.md")

        # Update manifest.json to include artifact entries
        manifest_path = f"jobs/{job_id}/manifest.json"
        blob = bucket_ref.blob(manifest_path)
        manifest = {}
        if blob.exists(client):
            try:
                manifest = json.loads(blob.download_as_text())
            except Exception:
                manifest = {}
        manifest.setdefault("artifacts", {})
        for name in artifacts:
            manifest["artifacts"][name] = {"path": name}
        blob.cache_control = "public, max-age=300"
        blob.upload_from_string(
            json.dumps(manifest, separators=(",", ":")), content_type="application/json"
        )

    except Exception as e:
        # Best-effort logging to stdout (rq captures logs)
        print(f"[worker] job {job_id} failed: {e}")


def process_job(job_id: str, payload: Dict[str, Any]) -> None:
    """RQ entrypoint - run async payload processor."""
    asyncio.run(_process_payload(job_id, payload))


def run() -> None:
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_conn = redis.from_url(url)
    with Connection(redis_conn):
        w = Worker([Queue("clipscribe")])
        w.work(with_scheduler=True)
