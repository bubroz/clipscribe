"""Tests for rate limiter."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch
from src.clipscribe.utils.rate_limiter import RateLimiter, DailyCapExceeded


@pytest.fixture
def rate_limiter():
    """Create a fresh rate limiter for each test."""
    return RateLimiter()


def test_rate_limiter_initialization():
    """Test rate limiter initializes with correct defaults."""
    limiter = RateLimiter()
    
    assert limiter.REQUEST_DELAY == 10
    assert limiter.DAILY_CAP == 100
    assert len(limiter.request_history) == 0
    assert len(limiter.last_request_time) == 0


def test_check_daily_cap_under_limit(rate_limiter):
    """Test daily cap check when under limit."""
    assert rate_limiter.check_daily_cap("youtube") is True
    
    # Add some requests
    for _ in range(50):
        rate_limiter.record_request("youtube")
    
    assert rate_limiter.check_daily_cap("youtube") is True


def test_check_daily_cap_at_limit(rate_limiter):
    """Test daily cap check when at limit."""
    # Add exactly DAILY_CAP requests
    for _ in range(rate_limiter.DAILY_CAP):
        rate_limiter.record_request("youtube")
    
    assert rate_limiter.check_daily_cap("youtube") is False


def test_check_daily_cap_over_limit(rate_limiter):
    """Test daily cap check when over limit."""
    # Add more than DAILY_CAP requests
    for _ in range(rate_limiter.DAILY_CAP + 10):
        rate_limiter.record_request("youtube")
    
    assert rate_limiter.check_daily_cap("youtube") is False


def test_check_daily_cap_old_requests_ignored(rate_limiter):
    """Test that old requests (>24h) don't count toward cap."""
    # Mock old timestamps (25 hours ago)
    old_time = datetime.now() - timedelta(hours=25)
    
    for _ in range(rate_limiter.DAILY_CAP):
        rate_limiter.request_history["youtube"].append(old_time)
    
    # Old requests should not count
    assert rate_limiter.check_daily_cap("youtube") is True


@pytest.mark.asyncio
async def test_wait_if_needed_first_request(rate_limiter):
    """Test no wait on first request."""
    start = datetime.now()
    await rate_limiter.wait_if_needed("youtube")
    elapsed = (datetime.now() - start).total_seconds()
    
    # Should be nearly instant (<0.1s)
    assert elapsed < 0.1


@pytest.mark.asyncio
async def test_wait_if_needed_enforces_delay(rate_limiter):
    """Test delay is enforced between requests."""
    # First request
    await rate_limiter.wait_if_needed("youtube")
    
    # Second request should wait
    start = datetime.now()
    await rate_limiter.wait_if_needed("youtube")
    elapsed = (datetime.now() - start).total_seconds()
    
    # Should wait ~REQUEST_DELAY seconds
    assert elapsed >= rate_limiter.REQUEST_DELAY - 0.5  # Allow 0.5s tolerance


@pytest.mark.asyncio
async def test_wait_if_needed_per_platform(rate_limiter):
    """Test delays are per-platform (not global)."""
    # Request youtube
    await rate_limiter.wait_if_needed("youtube")
    
    # Immediate vimeo request should not wait
    start = datetime.now()
    await rate_limiter.wait_if_needed("vimeo")
    elapsed = (datetime.now() - start).total_seconds()
    
    # Should be nearly instant
    assert elapsed < 0.1


def test_record_request_success(rate_limiter):
    """Test recording successful request."""
    rate_limiter.record_request("youtube", success=True)
    
    assert len(rate_limiter.request_history["youtube"]) == 1
    assert rate_limiter.consecutive_failures["youtube"] == 0


def test_record_request_failure(rate_limiter):
    """Test recording failed request."""
    rate_limiter.record_request("youtube", success=False)
    
    assert len(rate_limiter.request_history["youtube"]) == 1
    assert rate_limiter.consecutive_failures["youtube"] == 1


def test_consecutive_failures_reset_on_success(rate_limiter):
    """Test consecutive failures reset after success."""
    # Record failures
    rate_limiter.record_request("youtube", success=False)
    rate_limiter.record_request("youtube", success=False)
    assert rate_limiter.consecutive_failures["youtube"] == 2
    
    # Success should reset
    rate_limiter.record_request("youtube", success=True)
    assert rate_limiter.consecutive_failures["youtube"] == 0


def test_get_stats_empty(rate_limiter):
    """Test stats for platform with no requests."""
    stats = rate_limiter.get_stats("youtube")
    
    assert stats["platform"] == "youtube"
    assert stats["requests_today"] == 0
    assert stats["requests_this_week"] == 0
    assert stats["remaining_today"] == rate_limiter.DAILY_CAP


def test_get_stats_with_requests(rate_limiter):
    """Test stats for platform with requests."""
    # Add 10 requests
    for _ in range(10):
        rate_limiter.record_request("youtube")
    
    stats = rate_limiter.get_stats("youtube")
    
    assert stats["requests_today"] == 10
    assert stats["requests_this_week"] == 10
    assert stats["remaining_today"] == rate_limiter.DAILY_CAP - 10


def test_get_all_stats(rate_limiter):
    """Test getting stats for all platforms."""
    rate_limiter.record_request("youtube")
    rate_limiter.record_request("vimeo")
    rate_limiter.record_request("vimeo")
    
    all_stats = rate_limiter.get_all_stats()
    
    assert "youtube" in all_stats
    assert "vimeo" in all_stats
    assert all_stats["youtube"]["requests_today"] == 1
    assert all_stats["vimeo"]["requests_today"] == 2


def test_environment_overrides():
    """Test environment variables override defaults."""
    with patch.dict("os.environ", {"CLIPSCRIBE_REQUEST_DELAY": "5", "CLIPSCRIBE_DAILY_CAP": "200"}):
        limiter = RateLimiter()
        
        assert limiter.REQUEST_DELAY == 5
        assert limiter.DAILY_CAP == 200


def test_daily_cap_exceeded_exception():
    """Test DailyCapExceeded exception."""
    exc = DailyCapExceeded("youtube", 100)
    
    assert exc.platform == "youtube"
    assert exc.cap == 100
    assert "youtube" in str(exc)
    assert "100" in str(exc)

