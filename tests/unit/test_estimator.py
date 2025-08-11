from clipscribe.api.estimator import _secs_from_bytes_heuristic, estimate_job


def test_secs_from_bytes_video():
    assert _secs_from_bytes_heuristic(250_000, "video/mp4") >= 1


def test_secs_from_bytes_audio():
    # ~32kB should be ~2 seconds at 128 kbps
    s = _secs_from_bytes_heuristic(32_000, "audio/mpeg")
    assert 1 <= s <= 3


def test_estimate_job_fallback_when_unknown():
    # No url or gcs_uri falls back to 60s
    est = estimate_job({})
    assert est["estimated_duration_seconds"] >= 60
    assert est["estimated_cost_usd"] > 0
