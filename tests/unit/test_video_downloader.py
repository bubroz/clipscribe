"""Unit tests for video_downloader.py module."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
from clipscribe.retrievers.video_downloader import VideoDownloader
from clipscribe.models import VideoMetadata


@pytest.fixture
def video_downloader():
    """Create a VideoDownloader instance for testing."""
    return VideoDownloader(cache_dir="test_cache")


@pytest.fixture
def mock_video_metadata():
    """Create mock video metadata."""
    from datetime import datetime
    return VideoMetadata(
        video_id="test_123",
        url="https://www.youtube.com/watch?v=test123",
        title="Test Video",
        channel="Test Channel",
        channel_id="test_channel",
        published_at=datetime.now(),
        duration=300,
        view_count=1000,
        description="Test description",
        tags=["test"]
    )


class TestVideoDownloader:
    """Test cases for VideoDownloader class."""

    def test_init(self, video_downloader):
        """Test VideoDownloader initialization."""
        assert video_downloader.cache_dir == Path("test_cache")
        assert video_downloader.cookies_from_browser is None
        assert hasattr(video_downloader, 'video_client')

    def test_init_with_cookies(self):
        """Test VideoDownloader initialization with cookies."""
        downloader = VideoDownloader(cache_dir="test_cache", cookies_from_browser="chrome")
        assert downloader.cookies_from_browser == "chrome"

    def test_is_supported_url_youtube(self, video_downloader):
        """Test URL support detection for YouTube."""
        with patch.object(video_downloader.video_client, 'is_supported_url', return_value=True):
            assert video_downloader.is_supported_url("https://www.youtube.com/watch?v=test") is True

    def test_is_supported_url_unsupported(self, video_downloader):
        """Test URL support detection for unsupported platforms."""
        with patch.object(video_downloader.video_client, 'is_supported_url', return_value=False):
            assert video_downloader.is_supported_url("https://unsupported.com/video") is False

    @pytest.mark.asyncio
    async def test_download_video_success(self, video_downloader, mock_video_metadata):
        """Test successful video download."""
        with patch.object(video_downloader.video_client, 'download_video', new_callable=AsyncMock) as mock_download:
            mock_download.return_value = (mock_video_metadata, "test_media.mp4")

            result_metadata, media_file = await video_downloader.download_video(
                "https://www.youtube.com/watch?v=test"
            )

            assert result_metadata == mock_video_metadata
            assert media_file == "test_media.mp4"
            # Check that download_video was called with the correct arguments
            mock_download.assert_called_once_with(
                "https://www.youtube.com/watch?v=test",
                output_dir=video_downloader.cache_dir,
                cookies_from_browser=None
            )

    @pytest.mark.asyncio
    async def test_download_video_with_cookies(self, video_downloader, mock_video_metadata):
        """Test video download with cookies."""
        downloader = VideoDownloader(cache_dir="test_cache", cookies_from_browser="chrome")

        with patch.object(downloader.video_client, 'download_video', new_callable=AsyncMock) as mock_download:
            mock_download.return_value = (mock_video_metadata, "test_media.mp4")

            result_metadata, media_file = await downloader.download_video(
                "https://www.youtube.com/watch?v=test",
                cookies_from_browser="firefox"
            )

            # Check that download_video was called with the correct arguments
            mock_download.assert_called_once_with(
                "https://www.youtube.com/watch?v=test",
                output_dir=downloader.cache_dir,
                cookies_from_browser="firefox"
            )

    @pytest.mark.asyncio
    async def test_cleanup_temp_file(self, video_downloader, temp_directory):
        """Test temporary file cleanup."""
        # Create a temporary file
        temp_file = temp_directory / "test_video.mp4"
        temp_file.write_text("test content")

        from clipscribe.config.settings import VideoRetentionPolicy
        from clipscribe.retrievers.video_retention_manager import VideoRetentionManager

        retention_manager = VideoRetentionManager()

        await video_downloader.cleanup_temp_file(
            temp_file,
            VideoRetentionPolicy.DELETE,
            retention_manager
        )

        # File should be deleted
        assert not temp_file.exists()

    @pytest.mark.asyncio
    async def test_cleanup_temp_file_with_retention(self, video_downloader, temp_directory):
        """Test temporary file cleanup with retention policy."""
        # Create a temporary file
        temp_file = temp_directory / "test_video.mp4"
        temp_file.write_text("test content")

        from clipscribe.config.settings import VideoRetentionPolicy
        from clipscribe.retrievers.video_retention_manager import VideoRetentionManager

        retention_manager = VideoRetentionManager()

        await video_downloader.cleanup_temp_file(
            temp_file,
            VideoRetentionPolicy.KEEP_ALL,
            retention_manager
        )

        # File should still exist due to retention policy
        assert temp_file.exists()

    @pytest.mark.asyncio
    async def test_search_videos(self, video_downloader):
        """Test video search functionality."""
        mock_results = [
            {"url": "https://www.youtube.com/watch?v=1", "title": "Video 1"},
            {"url": "https://www.youtube.com/watch?v=2", "title": "Video 2"}
        ]

        with patch.object(video_downloader.video_client, 'search_videos', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_results

            results = await video_downloader.search_videos("test query", max_results=2, site="youtube")

            assert results == mock_results
            mock_search.assert_called_once_with("test query", 2, "youtube")

    @pytest.mark.asyncio
    async def test_download_video_error_handling(self, video_downloader):
        """Test error handling during video download."""
        with patch.object(video_downloader.video_client, 'download_video', new_callable=AsyncMock) as mock_download:
            mock_download.side_effect = Exception("Download failed")

            with pytest.raises(Exception, match="Download failed"):
                await video_downloader.download_video("https://www.youtube.com/watch?v=test")

    def test_cache_directory_creation(self, temp_directory):
        """Test cache directory creation."""
        cache_dir = temp_directory / "test_cache"
        assert not cache_dir.exists()

        downloader = VideoDownloader(cache_dir=str(cache_dir))

        assert cache_dir.exists()
        assert cache_dir.is_dir()

    def test_cache_directory_already_exists(self, temp_directory):
        """Test behavior when cache directory already exists."""
        cache_dir = temp_directory / "existing_cache"
        cache_dir.mkdir()

        # Create a file in the directory
        (cache_dir / "existing_file.txt").write_text("test")

        downloader = VideoDownloader(cache_dir=str(cache_dir))

        # Directory should still exist and contain the file
        assert cache_dir.exists()
        assert (cache_dir / "existing_file.txt").exists()

    @pytest.mark.asyncio
    async def test_cleanup_temp_file_none_retention_manager(self, video_downloader, temp_directory):
        """Test cleanup with None retention manager."""
        temp_file = temp_directory / "test_video.mp4"
        temp_file.write_text("test content")

        from clipscribe.config.settings import VideoRetentionPolicy

        await video_downloader.cleanup_temp_file(
            temp_file,
            VideoRetentionPolicy.DELETE,
            None  # None retention manager
        )

        # File should be deleted even without retention manager
        assert not temp_file.exists()

    @pytest.mark.asyncio
    async def test_cleanup_temp_file_error_handling(self, video_downloader, temp_directory):
        """Test cleanup error handling when file cannot be removed."""
        temp_file = temp_directory / "test_video.mp4"
        temp_file.write_text("test content")

        from clipscribe.config.settings import VideoRetentionPolicy
        from clipscribe.retrievers.video_retention_manager import VideoRetentionManager
        from unittest.mock import patch

        retention_manager = VideoRetentionManager()

        # Mock os.unlink to raise an exception
        with patch('os.unlink', side_effect=OSError("Permission denied")):
            await video_downloader.cleanup_temp_file(
                temp_file,
                VideoRetentionPolicy.DELETE,
                retention_manager
            )

        # File should still exist due to the error
        assert temp_file.exists()

    def test_video_client_initialization(self, video_downloader):
        """Test that video client is properly initialized."""
        assert hasattr(video_downloader, 'video_client')
        assert video_downloader.video_client is not None

    @pytest.mark.asyncio
    async def test_multiple_concurrent_downloads(self, video_downloader):
        """Test concurrent download operations."""
        import asyncio

        # Mock multiple downloads
        with patch.object(video_downloader.video_client, 'download_video', new_callable=AsyncMock) as mock_download:
            mock_download.return_value = (mock_video_metadata, "test_media.mp4")

            # Start multiple downloads concurrently
            urls = [f"https://www.youtube.com/watch?v=test{i}" for i in range(3)]
            tasks = [video_downloader.download_video(url) for url in urls]

            results = await asyncio.gather(*tasks)

            # All should succeed
            assert len(results) == 3
            assert all(isinstance(result, tuple) for result in results)
            assert mock_download.call_count == 3
