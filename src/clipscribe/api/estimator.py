from __future__ import annotations

from typing import Dict, Any, Optional, Tuple

from clipscribe.config.settings import Settings


def _secs_from_bytes_heuristic(size_bytes: int, mime_type: Optional[str]) -> int:
    """Heuristic: approximate duration from file size.
    Defaults assume ~1.0 Mbps video (125_000 bytes/sec) or ~128 kbps audio (16_000 bytes/sec).
    """
    if not size_bytes or size_bytes <= 0:
        return 0
    mt = (mime_type or "").lower()
    if mt.startswith("audio/"):
        bytes_per_sec = 16_000  # ~128 kbps
    else:
        bytes_per_sec = 125_000  # ~1 Mbps video
    return max(1, int(size_bytes / bytes_per_sec))


def estimate_from_url(url: str) -> Tuple[int, Dict[str, Any]]:
    """Estimate duration seconds from a URL using yt-dlp metadata probe (no download).
    Returns (duration_seconds, extra_metadata)
    """
    try:
        # Lazy import to avoid imposing yt_dlp on all code paths
        from yt_dlp import YoutubeDL  # type: ignore

        opts = {
            "quiet": True,
            "skip_download": True,
            "noplaylist": True,
            "forcejson": True,
        }
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            duration = int(info.get("duration") or 0)
            return max(0, duration), {"source": "yt_dlp", "duration": duration}
    except Exception:
        return 0, {"source": "yt_dlp", "error": "probe_failed"}


def estimate_from_gcs_uri(gcs_uri: str) -> Tuple[int, Dict[str, Any]]:
    """Estimate duration seconds from a GCS object using size and optional metadata.
    Returns (duration_seconds, extra_metadata)
    """
    try:
        from google.cloud import storage  # type: ignore

        path = gcs_uri.replace("gs://", "")
        bucket_name, blob_name = path.split("/", 1)
        client = storage.Client()
        blob = client.bucket(bucket_name).blob(blob_name)
        blob.reload()

        size_bytes = int(getattr(blob, "size", 0) or 0)
        mime_type = getattr(blob, "content_type", None)
        # Optional user metadata for duration
        md = getattr(blob, "metadata", {}) or {}
        dur_meta = md.get("duration") or md.get("x-duration")
        if dur_meta:
            try:
                duration = int(float(dur_meta))
                return max(0, duration), {
                    "source": "gcs_metadata",
                    "size_bytes": size_bytes,
                    "mime_type": mime_type,
                }
            except Exception:
                pass

        duration = _secs_from_bytes_heuristic(size_bytes, mime_type)
        return duration, {
            "source": "gcs_size_heuristic",
            "size_bytes": size_bytes,
            "mime_type": mime_type,
        }
    except Exception:
        return 0, {"source": "gcs", "error": "probe_failed"}


def estimate_job(body: Dict[str, Any], settings: Optional[Settings] = None) -> Dict[str, Any]:
    """High-level estimate for a job request body.

    Returns dict with: estimated_duration_seconds, estimated_cost_usd, proposed_model, metadata
    """
    s = settings or Settings()
    duration = 0
    meta: Dict[str, Any] = {}
    if "url" in body:
        duration, meta = estimate_from_url(body["url"])  # type: ignore
    elif "gcs_uri" in body:
        duration, meta = estimate_from_gcs_uri(body["gcs_uri"])  # type: ignore

    # Fallback if unknown
    if duration <= 0:
        duration = 60  # assume 1 minute to avoid zero
        meta.setdefault("fallback", True)

    est_cost = s.estimate_cost(duration)
    proposed_model = "flash"
    return {
        "estimated_duration_seconds": duration,
        "estimated_cost_usd": round(est_cost, 6),
        "proposed_model": proposed_model,
        "metadata": meta,
    }
