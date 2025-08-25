"""Unit tests for YouTubeClient module."""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path

from clipscribe.retrievers.youtube_client import YouTubeClient
from clipscribe.models import VideoMetadata


@pytest.fixture
def youtube_client():
    """Create YouTube client for testing."""
    return YouTubeClient()


class TestYouTubeClient:
    """Test YouTubeClient functionality."""

    def test_init(self, youtube_client):
        """Test YouTube client initialization."""
        assert youtube_client is not None
        assert isinstance(youtube_client.ydl_opts, dict)
        assert youtube_client.ydl_opts["format"] == "bestaudio/best"
        assert youtube_client.ydl_opts["quiet"] is True

    @pytest.mark.asyncio
    async def test_search_videos_success(self, youtube_client):
        """Test successful video search."""
        mock_search_result = {
            "result": [
                {
                    "id": "test_video_123",
                    "title": "Test YouTube Video",
                    "channel": "Test Channel",
                    "channel_id": "test_channel_123",
                    "duration": "5:00",
                    "views": "10K views",
                    "publish_time": "1 month ago",
                    "long_desc": "A test video for unit testing"
                }
            ]
        }

        with patch('clipscribe.retrievers.youtube_client.VideosSearch') as mock_videos_search:
            # Create a proper mock instance
            mock_instance = MagicMock()
            mock_instance.result.return_value = mock_search_result
            mock_videos_search.return_value = mock_instance

            # Mock all parsing methods to avoid any external processing
            with patch.object(youtube_client, '_parse_duration', return_value=300), \
                 patch.object(youtube_client, '_parse_view_count', return_value=10000), \
                 patch.object(youtube_client, '_parse_published_date', return_value=datetime(2024, 1, 15, 14, 30, 0)):

                results = await youtube_client.search_videos("test query", max_results=5)

                # Verify the mock was called correctly
                mock_videos_search.assert_called_once_with("test query", limit=5)
                mock_instance.result.assert_called_once()

                assert len(results) == 1
                assert results[0].video_id == "test_video_123"
                assert results[0].title == "Test YouTube Video"
                assert results[0].channel == "Test Channel"

    @pytest.mark.asyncio
    async def test_search_videos_empty_results(self, youtube_client):
        """Test video search with no results."""
        mock_search_result = {"result": []}

        with patch('clipscribe.retrievers.youtube_client.VideosSearch') as mock_videos_search:
            mock_instance = MagicMock()
            mock_instance.result.return_value = mock_search_result
            mock_videos_search.return_value = mock_instance

            results = await youtube_client.search_videos("nonexistent query", max_results=5)

            mock_videos_search.assert_called_once_with("nonexistent query", limit=5)
            mock_instance.result.assert_called_once()

            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_videos_error_handling(self, youtube_client):
        """Test video search error handling."""
        with patch('clipscribe.retrievers.youtube_client.VideosSearch') as mock_videos_search:
            mock_instance = MagicMock()
            mock_instance.result.side_effect = Exception("Search failed")
            mock_videos_search.return_value = mock_instance

            results = await youtube_client.search_videos("test query", max_results=5)

            mock_videos_search.assert_called_once_with("test query", limit=5)
            mock_instance.result.assert_called_once()

            assert results == []

    def test_parse_duration_various_formats(self, youtube_client):
        """Test duration parsing with various formats."""
        test_cases = [
            ("5:30", 330),
            ("1:23:45", 5025),
            ("45", 45),
            ("1:30:00", 5400),
            ("0:30", 30),
            ("", 0),
            (None, 0),
        ]

        for duration_str, expected_seconds in test_cases:
            result = youtube_client._parse_duration(duration_str)
            assert result == expected_seconds, f"Failed for {duration_str}"

    def test_parse_view_count_various_formats(self, youtube_client):
        """Test view count parsing with various formats."""
        test_cases = [
            ("10K views", 10000),
            ("1.5M views", 1500000),
            ("500 views", 500),
            ("2,500 views", 2500),
            ("0 views", 0),
            ("", 0),
            (None, 0),
        ]

        for view_str, expected_count in test_cases:
            result = youtube_client._parse_view_count(view_str)
            assert result == expected_count, f"Failed for {view_str}"

    def test_parse_published_date_various_formats(self, youtube_client):
        """Test published date parsing with various formats."""
        now = datetime.now()

        test_cases = [
            ("1 month ago", now - timedelta(days=30)),
            ("2 weeks ago", now - timedelta(weeks=2)),
            ("3 days ago", now - timedelta(days=3)),
            ("5 hours ago", now - timedelta(hours=5)),
            ("just now", now),
            ("", now),
            (None, now),
        ]

        for time_str, expected_time in test_cases:
            result = youtube_client._parse_published_date(time_str)
            # Check that result is within reasonable bounds (within 1 day)
            time_diff = abs((result - expected_time).total_seconds())
            assert time_diff < 86400, f"Failed for {time_str}: got {result}, expected around {expected_time}"

    @pytest.mark.asyncio
    async def test_download_audio_success(self, youtube_client):
        """Test successful audio download."""
        mock_info = {
            'id': 'test_video_123',
            'title': 'Test Video',
            'uploader': 'Test Channel',
            'channel_id': 'test_channel',
            'duration': 300,
            'view_count': 10000,
            'upload_date': '20240115',  # String format as expected by datetime.strptime
            'description': 'Test description',
            'tags': ['test'],
            'webpage_url': 'https://www.youtube.com/watch?v=test_video_123'
        }

        # Create expected metadata that _create_metadata_from_info should return
        expected_metadata = VideoMetadata(
            video_id="test_video_123",
            url="https://www.youtube.com/watch?v=test_video_123",
            title="Test Video",
            channel="Test Channel",
            channel_id="test_channel",
            duration=300,
            view_count=10000,
            published_at=datetime(2024, 1, 15, 0, 0, 0),
            description="Test description",
            tags=['test']
        )

        with patch('clipscribe.retrievers.youtube_client.yt_dlp.YoutubeDL') as mock_ydl_class, \
             patch.object(youtube_client, '_create_metadata_from_info', return_value=expected_metadata) as mock_create_metadata:

            mock_ydl_instance = MagicMock()
            mock_ydl_instance.extract_info.return_value = mock_info
            mock_ydl_instance.download.return_value = 0
            mock_ydl_class.return_value = mock_ydl_instance

            with patch('tempfile.mkdtemp', return_value='/tmp/test'), \
                 patch('tempfile.NamedTemporaryFile') as mock_temp_file, \
                 patch('os.path.exists', return_value=True), \
                 patch('os.path.getsize', return_value=1024 * 1024):

                mock_temp_file.return_value.__enter__.return_value.name = '/tmp/test_audio.mp3'

                result = await youtube_client.download_audio("https://www.youtube.com/watch?v=test_video_123")

                # Verify the mocks were called correctly
                mock_ydl_class.assert_called()
                mock_ydl_instance.extract_info.assert_called_once_with("https://www.youtube.com/watch?v=test_video_123", download=False)
                mock_ydl_instance.download.assert_called_once()

                assert isinstance(result, tuple)
                assert len(result) == 2
                audio_path, metadata = result
                assert isinstance(audio_path, str)
                assert isinstance(metadata, VideoMetadata)

    @pytest.mark.asyncio
    async def test_download_audio_failure(self, youtube_client):
        """Test audio download failure."""
        with patch('clipscribe.retrievers.youtube_client.yt_dlp.YoutubeDL') as mock_ydl_class:
            mock_ydl_instance = MagicMock()
            mock_ydl_instance.extract_info.side_effect = Exception("Download failed")
            mock_ydl_class.return_value = mock_ydl_instance

            with patch('tempfile.mkdtemp', return_value='/tmp/test'), \
                 patch('tempfile.NamedTemporaryFile'):
                with pytest.raises(Exception, match="Download failed"):
                    await youtube_client.download_audio("https://www.youtube.com/watch?v=invalid")

    @pytest.mark.asyncio
    async def test_get_video_info_success(self, youtube_client):
        """Test successful video info retrieval."""
        mock_video_info = {
            'id': 'test123',
            'title': 'Test Video',
            'uploader': 'Test Channel',
            'channel_id': 'test_channel',
            'duration': 300,
            'view_count': 10000,
            'upload_date': '20240115',  # String format as expected by datetime.strptime
            'description': 'Test description',
            'tags': ['test', 'video'],
            'webpage_url': 'https://www.youtube.com/watch?v=test123'
        }

        # Create expected metadata that _create_metadata_from_info should return
        expected_metadata = VideoMetadata(
            video_id="test123",
            url="https://www.youtube.com/watch?v=test123",
            title="Test Video",
            channel="Test Channel",
            channel_id="test_channel",
            duration=300,
            view_count=10000,
            published_at=datetime(2024, 1, 15, 0, 0, 0),
            description="Test description",
            tags=['test', 'video']
        )

        with patch('clipscribe.retrievers.youtube_client.yt_dlp.YoutubeDL') as mock_ydl_class, \
             patch.object(youtube_client, '_create_metadata_from_info', return_value=expected_metadata) as mock_create_metadata:

            mock_ydl_instance = MagicMock()
            mock_ydl_instance.extract_info.return_value = mock_video_info
            mock_ydl_class.return_value = mock_ydl_instance

            result = await youtube_client.get_video_info("https://www.youtube.com/watch?v=test123")

            mock_ydl_class.assert_called_once_with({"quiet": True})
            mock_ydl_instance.extract_info.assert_called_once_with("https://www.youtube.com/watch?v=test123", download=False)
            mock_create_metadata.assert_called_once()

            assert isinstance(result, VideoMetadata)
            assert result.video_id == "test123"
            assert result.title == "Test Video"

    @pytest.mark.asyncio
    async def test_get_video_info_error(self, youtube_client):
        """Test video info retrieval error."""
        with patch('clipscribe.retrievers.youtube_client.yt_dlp.YoutubeDL') as mock_ydl_class:
            mock_ydl_instance = MagicMock()
            mock_ydl_instance.extract_info.side_effect = Exception("Video not found")
            mock_ydl_class.return_value = mock_ydl_instance

            with pytest.raises(Exception, match="Video not found"):
                await youtube_client.get_video_info("https://www.youtube.com/watch?v=invalid")
