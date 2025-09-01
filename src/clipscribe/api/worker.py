from __future__ import annotations

import os
import json
import tempfile
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from rq import Worker, Queue
from redis import Redis
import redis

from .retry_manager import get_retry_manager, should_retry_api_error, should_retry_network_error
from .monitoring import get_metrics_collector

logger = logging.getLogger(__name__)


async def _process_payload(job_id: str, payload: Dict[str, Any]) -> None:
    """Process a job: transcribe/analyze and write artifacts to GCS."""
    start_time = datetime.now()
    metrics = get_metrics_collector()
    retry_manager = get_retry_manager()

    # Record job start
    metrics.record_metric("job_started", 1, {"job_id": job_id})

    try:
        logger.info(f"Starting job processing: {job_id}")

        bucket = os.getenv("GCS_BUCKET", "").strip()  # Remove any whitespace/newlines
        if not bucket:
            raise ValueError("GCS_BUCKET not configured")

        from google.cloud import storage  # type: ignore

        # Initialize GCS client with retry
        async def init_gcs_client():
            return storage.Client()

        client = await retry_manager.execute_with_retry(
            f"gcs_init_{job_id}",
            init_gcs_client,
            should_retry_network_error
        )

        bucket_ref = client.bucket(bucket)

        # Helper to upload with retry
        async def upload_bytes(path: str, data: bytes, content_type: str) -> None:
            async def _upload():
                blob = bucket_ref.blob(path)
                blob.cache_control = "public, max-age=300"
                blob.upload_from_string(data, content_type=content_type)
                return True

            await retry_manager.execute_with_retry(
                f"gcs_upload_{job_id}_{path}",
                _upload,
                should_retry_network_error
            )

        artifacts = []

        # Record processing start
        metrics.record_metric("job_processing_started", 1, {"job_id": job_id})
        # Case 1: Direct URL processing via yt-dlp + Gemini
        if "url" in payload:
            from clipscribe.retrievers.universal_video_client import EnhancedUniversalVideoClient
            from clipscribe.retrievers.transcriber import GeminiFlashTranscriber

            # Download video with retry
            async def download_video():
                uvc = EnhancedUniversalVideoClient()
                tmpdir = tempfile.mkdtemp()
                audio_path, metadata = await uvc.download_audio(payload["url"], output_dir=tmpdir)
                return audio_path, metadata, tmpdir

            audio_path, metadata, tmpdir = await retry_manager.execute_with_retry(
                f"video_download_{job_id}",
                download_video,
                should_retry_network_error
            )

            duration = int(getattr(metadata, "duration", 0) or 0)
            metrics.record_metric("video_duration_seconds", duration, {"job_id": job_id})

            # Transcribe with retry
            async def transcribe_video():
                transcriber = GeminiFlashTranscriber(use_pro=False)
                analysis = await transcriber.transcribe_audio(audio_path, duration)
                return analysis

            analysis = await retry_manager.execute_with_retry(
                f"video_transcription_{job_id}",
                transcribe_video,
                should_retry_api_error
            )

            # Record transcription metrics
            entity_count = len(analysis.get('entities', []))
            relationship_count = len(analysis.get('relationships', []))
            metrics.record_metric("transcription_entities", entity_count, {"job_id": job_id})
            metrics.record_metric("transcription_relationships", relationship_count, {"job_id": job_id})

            # transcript.json
            transcript_json = json.dumps(analysis, separators=(",", ":")).encode("utf-8")
            await upload_bytes(f"jobs/{job_id}/transcript.json", transcript_json, "application/json")
            artifacts.append("transcript.json")

            # simple report.md
            report_md = (
                f"# ClipScribe Report\n\nJob: {job_id}\nURL: {payload['url']}\n\n"
                f"Summary: {analysis.get('summary','')[:500]}\n\n"
                f"Entities: {entity_count}, Relationships: {relationship_count}\n"
            ).encode("utf-8")
            await upload_bytes(f"jobs/{job_id}/report.md", report_md, "text/markdown")
            artifacts.append("report.md")

        # Case 2: gcs_uri processing via Vertex AI
        elif "gcs_uri" in payload:
            from clipscribe.retrievers.vertex_ai_transcriber import VertexAITranscriber

            # Transcribe with Vertex AI and retry
            async def transcribe_vertex():
                vtx = VertexAITranscriber()
                result = await vtx.transcribe_with_vertex(
                    gcs_uri=payload["gcs_uri"], enhance_transcript=False, mode="video"
                )
                return result

            result = await retry_manager.execute_with_retry(
                f"vertex_transcription_{job_id}",
                transcribe_vertex,
                should_retry_api_error
            )

            # Record Vertex AI metrics
            entity_count = len(result.get('entities', []))
            relationship_count = len(result.get('relationships', []))
            metrics.record_metric("vertex_entities", entity_count, {"job_id": job_id})
            metrics.record_metric("vertex_relationships", relationship_count, {"job_id": job_id})

            transcript_json = json.dumps(result, default=str, separators=(",", ":")).encode("utf-8")
            await upload_bytes(f"jobs/{job_id}/transcript.json", transcript_json, "application/json")
            artifacts.append("transcript.json")

            report_md = (
                f"# ClipScribe Report\n\nJob: {job_id}\nGCS: {payload['gcs_uri']}\n\n"
                f"Entities: {entity_count}, Relationships: {relationship_count}\n"
            ).encode("utf-8")
            await upload_bytes(f"jobs/{job_id}/report.md", report_md, "text/markdown")
            artifacts.append("report.md")

        # Update manifest.json to include artifact entries
        manifest_path = f"jobs/{job_id}/manifest.json"

        async def update_manifest():
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
            return True

        await retry_manager.execute_with_retry(
            f"manifest_update_{job_id}",
            update_manifest,
            should_retry_network_error
        )

        # Record successful completion
        processing_time = (datetime.now() - start_time).total_seconds()
        metrics.record_metric("job_processing_time_seconds", processing_time, {"job_id": job_id})
        metrics.record_metric("job_completed", 1, {"job_id": job_id})
        metrics.record_metric("artifacts_created", len(artifacts), {"job_id": job_id})

        logger.info(f"Job {job_id} completed successfully in {processing_time:.1f}s with {len(artifacts)} artifacts")

    except Exception as e:
        # Record failure metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        metrics.record_metric("job_failed", 1, {"job_id": job_id, "error_type": type(e).__name__})
        metrics.record_metric("job_processing_time_seconds", processing_time, {"job_id": job_id, "failed": "true"})

        logger.error(f"Job {job_id} failed after {processing_time:.1f}s: {e}")

        # Re-raise to let RQ handle the failure
        raise


def process_job(job_id: str, payload: Dict[str, Any]) -> None:
    """RQ entrypoint - run async payload processor."""
    asyncio.run(_process_payload(job_id, payload))


def run() -> None:
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_conn = redis.from_url(url)
    # Use Redis connection directly for RQ
    w = Worker([Queue("clipscribe")], connection=redis_conn)
    w.work(with_scheduler=True)
