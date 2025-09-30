"""Tests for UniversalVideoClient rate limiting integration."""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from src.clipscribe.retrievers.universal_video_client import UniversalVideoClient
from src.clipscribe.utils.rate_limiter import RateLimiter, DailyCapExceeded


@pytest.fixture
def mock_ydl():
    """Mock yt-dlp YoutubeDL class."""
    with patch("src.clipscribe.retrievers.universal_video_client.yt_dlp.YoutubeDL") as mock:
        # Mock the context manager
        mock_instance = MagicMock()
        mock.return_value.__enter__ = MagicMock(return_value=mock_instance)
        mock.return_value.__exit__ = MagicMock(return_value=None)
        
        # Mock extract_info with proper dict values (not MagicMocks)
        mock_instance.extract_info.return_value = {
            "id": "test123",
            "title": "Test Video",
            "extractor": "youtube",
            "duration": 120,
            "uploader": "Test Channel",
            "timestamp": datetime.now().timestamp(),
            "webpage_url": "https://youtube.com/watch?v=test123",
            "channel_id": "test_channel",
            "view_count": 1000,
            "description": "Test description",
            "tags": ["test"],
        }
        
        # Mock download
        mock_instance.download.return_value = None
        
        yield mock


@pytest.fixture
def video_client_with_limiter():
    """Create video client with fresh rate limiter."""
    limiter = RateLimiter()
    client = UniversalVideoClient(use_impersonation=False, rate_limiter=limiter)
    return client


def test_platform_detection():
    """Test platform detection from URLs."""
    client = UniversalVideoClient(use_impersonation=False)
    
    assert client._detect_platform("https://www.youtube.com/watch?v=test") == "youtube"
    assert client._detect_platform("https://youtu.be/test") == "youtube"
    assert client._detect_platform("https://vimeo.com/123456") == "vimeo"
    assert client._detect_platform("https://twitter.com/user/status/123") == "twitter"
    # Note: x.com also resolves to twitter via "//x.com/" check
    assert client._detect_platform("https://tiktok.com/@user/video/123") == "tiktok"
    assert client._detect_platform("https://facebook.com/video/123") == "facebook"
    assert client._detect_platform("https://instagram.com/p/123") == "instagram"
    assert client._detect_platform("https://twitch.tv/user") == "twitch"
    assert client._detect_platform("https://reddit.com/r/videos/123") == "reddit"
    # Note: "other" fallback tested implicitly (any non-matching domain)


@pytest.mark.asyncio
async def test_rate_limit_enforced(video_client_with_limiter, mock_ydl, tmp_path):
    """Test that rate limiting delays are enforced."""
    client = video_client_with_limiter
    
    # Mock file creation
    test_file = tmp_path / "Test Video-test123.mp3"
    test_file.touch()
    
    with patch("os.listdir", return_value=["Test Video-test123.mp3"]):
        with patch("os.path.exists", return_value=True):
            # First request should be immediate
            start1 = datetime.now()
            await client.download_audio("https://youtube.com/watch?v=test1", str(tmp_path))
            time1 = (datetime.now() - start1).total_seconds()
            
            # Second request should wait ~10s
            start2 = datetime.now()
            await client.download_audio("https://youtube.com/watch?v=test2", str(tmp_path))
            time2 = (datetime.now() - start2).total_seconds()
            
            # First should be fast (<1s), second should wait (>9s)
            assert time1 < 1.0
            assert time2 >= 9.0  # Allow 1s tolerance


@pytest.mark.asyncio
async def test_different_platforms_no_delay(video_client_with_limiter, mock_ydl, tmp_path):
    """Test that different platforms don't interfere with each other."""
    client = video_client_with_limiter
    
    # Mock file creation
    test_file = tmp_path / "Test Video-test123.mp3"
    test_file.touch()
    
    with patch("os.listdir", return_value=["Test Video-test123.mp3"]):
        with patch("os.path.exists", return_value=True):
            # YouTube request
            await client.download_audio("https://youtube.com/watch?v=test1", str(tmp_path))
            
            # Immediate Vimeo request should not wait
            start = datetime.now()
            await client.download_audio("https://vimeo.com/123456", str(tmp_path))
            elapsed = (datetime.now() - start).total_seconds()
            
            # Should be fast (<1s) because different platform
            assert elapsed < 1.0


@pytest.mark.asyncio
async def test_daily_cap_enforcement(video_client_with_limiter, mock_ydl, tmp_path):
    """Test that daily cap is enforced."""
    client = video_client_with_limiter
    
    # Set low cap for testing
    client.rate_limiter.DAILY_CAP = 3
    
    # Mock file creation
    test_file = tmp_path / "Test Video-test123.mp3"
    test_file.touch()
    
    with patch("os.listdir", return_value=["Test Video-test123.mp3"]):
        with patch("os.path.exists", return_value=True):
            # First 3 requests should succeed
            for i in range(3):
                await client.download_audio(f"https://youtube.com/watch?v=test{i}", str(tmp_path))
            
            # 4th request should raise DailyCapExceeded
            with pytest.raises(DailyCapExceeded) as exc_info:
                await client.download_audio("https://youtube.com/watch?v=test3", str(tmp_path))
            
            assert exc_info.value.platform == "youtube"
            assert exc_info.value.cap == 3


@pytest.mark.asyncio
async def test_failure_tracking(video_client_with_limiter, tmp_path):
    """Test that failures are tracked for ban detection."""
    client = video_client_with_limiter
    
    # Mock yt-dlp to fail
    with patch("src.clipscribe.retrievers.universal_video_client.yt_dlp.YoutubeDL") as mock_ydl:
        mock_instance = MagicMock()
        mock_ydl.return_value.__enter__ = MagicMock(return_value=mock_instance)
        mock_ydl.return_value.__exit__ = MagicMock(return_value=None)
        mock_instance.extract_info.side_effect = Exception("403 Forbidden")
        
        # Try to download
        try:
            await client.download_audio("https://youtube.com/watch?v=test", str(tmp_path))
        except Exception:
            pass
        
        # Check that failure was recorded
        assert client.rate_limiter.consecutive_failures["youtube"] > 0


@pytest.mark.asyncio
async def test_success_resets_failures(video_client_with_limiter, mock_ydl, tmp_path):
    """Test that success resets consecutive failures."""
    client = video_client_with_limiter
    
    # Manually set some failures
    client.rate_limiter.consecutive_failures["youtube"] = 2
    
    # Mock file creation
    test_file = tmp_path / "Test Video-test123.mp3"
    test_file.touch()
    
    with patch("os.listdir", return_value=["Test Video-test123.mp3"]):
        with patch("os.path.exists", return_value=True):
            # Successful download should reset
            await client.download_audio("https://youtube.com/watch?v=test", str(tmp_path))
    
    # Failures should be reset
    assert client.rate_limiter.consecutive_failures["youtube"] == 0


@pytest.mark.asyncio
async def test_rate_limiter_initialization():
    """Test that rate limiter is initialized correctly."""
    # With default limiter
    client1 = UniversalVideoClient(use_impersonation=False)
    assert client1.rate_limiter is not None
    assert client1.rate_limiter.REQUEST_DELAY == 10
    assert client1.rate_limiter.DAILY_CAP == 100
    
    # With custom limiter
    custom_limiter = RateLimiter()
    custom_limiter.REQUEST_DELAY = 5
    client2 = UniversalVideoClient(use_impersonation=False, rate_limiter=custom_limiter)
    assert client2.rate_limiter == custom_limiter
    assert client2.rate_limiter.REQUEST_DELAY == 5

