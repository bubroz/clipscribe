"""Unit tests for UniversalVideoClient module."""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock, mock_open
from pathlib import Path
import yt_dlp

from clipscribe.retrievers.universal_video_client import UniversalVideoClient, YTDLLogger, Chapter, VideoSegment
from clipscribe.models import VideoMetadata


@pytest.fixture
def universal_client():
    """Create Universal Video client for testing."""
    return UniversalVideoClient()


@pytest.fixture
def mock_video_metadata():
    """Create mock video metadata for testing."""
    return VideoMetadata(
        video_id="test_video_123",
        url="https://www.youtube.com/watch?v=test_video_123",
        title="Test Universal Video",
        channel="Test Channel",
        channel_id="test_channel_123",
        published_at=datetime(2024, 1, 15, 14, 30, 0),
        duration=300,
        view_count=10000,
        description="A test video for universal client testing",
        tags=["test", "universal", "video"]
    )


class TestYTDLLogger:
    """Test YTDLLogger functionality."""

    def test_logger_creation(self):
        """Test YTDLLogger creation."""
        logger = YTDLLogger()
        assert logger is not None

    @patch('clipscribe.retrievers.universal_video_client.logger')
    def test_debug_filtering(self, mock_logger):
        """Test debug message filtering."""
        logger = YTDLLogger()

        # Should filter git/github messages
        logger.debug("This is a git message")
        logger.debug("This is a github message")

        # Should not filter other messages
        logger.debug("This is a normal debug message")

        # Verify only the normal message was logged
        mock_logger.debug.assert_called_once_with("This is a normal debug message")

    @patch('clipscribe.retrievers.universal_video_client.logger')
    def test_info_logging(self, mock_logger):
        """Test info message logging."""
        logger = YTDLLogger()
        logger.info("Test info message")
        mock_logger.info.assert_called_once_with("Test info message")


class TestChapter:
    """Test Chapter dataclass."""

    def test_chapter_creation(self):
        """Test Chapter creation."""
        chapter = Chapter(
            title="Test Chapter",
            start_time=0.0,
            end_time=60.0,
            url="https://example.com/chapter"
        )

        assert chapter.title == "Test Chapter"
        assert chapter.start_time == 0.0
        assert chapter.end_time == 60.0
        assert chapter.url == "https://example.com/chapter"


class TestUniversalVideoClient:
    """Test UniversalVideoClient functionality."""

    def test_init(self, universal_client):
        """Test Universal Video client initialization."""
        assert universal_client is not None
        assert isinstance(universal_client.ydl_opts, dict)
        assert universal_client.ydl_opts["format"] == "bestaudio/best"
        assert universal_client.ydl_opts["quiet"] is True

    @pytest.mark.asyncio
    async def test_search_videos_youtube(self, universal_client):
        """Test YouTube video search."""
        mock_search_result = {
            "result": [
                {
                    "id": "test_video_123",
                    "title": "Test YouTube Video",
                    "channel": {
                        "name": "Test Channel",
                        "id": "test_channel_123"
                    },
                    "duration": "5:00",
                    "views": "10K views",
                    "publish_time": "1 month ago",
                    "long_desc": "A test video",
                    "thumbnails": [{"url": "https://example.com/thumb.jpg"}]
                }
            ]
        }

        with patch('clipscribe.retrievers.universal_video_client.CustomSearch') as mock_search:
            mock_search_instance = AsyncMock()
            mock_search_instance.next.return_value = mock_search_result
            mock_search.return_value = mock_search_instance

            with patch.object(universal_client, '_parse_duration', return_value=300), \
                 patch.object(universal_client, '_parse_view_count', return_value=10000), \
                 patch.object(universal_client, '_parse_published_date', return_value=datetime(2024, 1, 15, 14, 30, 0)):

                results = await universal_client.search_videos("test query", max_results=5, site="youtube")

                assert len(results) == 1
                assert results[0].video_id == "test_video_123"
                assert results[0].title == "Test YouTube Video"

    def test_parse_duration_various_formats(self, universal_client):
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
            result = universal_client._parse_duration(duration_str)
            assert result == expected_seconds, f"Failed for {duration_str}"

    def test_parse_view_count_various_formats(self, universal_client):
        """Test view count parsing with various formats."""
        test_cases = [
            ("10K views", 10000),
            ("1.5M views", 1500000),
            ("500 views", 500),
            ("2,500 views", 2500),
            ("0 views", 0),
            ("", 0),
            ("1M", 1000000),
            ("2.5B", 2500000000),
        ]

        for view_data, expected_count in test_cases:
            result = universal_client._parse_view_count(view_data)
            assert result == expected_count, f"Failed for {view_data}"

    def test_get_supported_sites(self, universal_client):
        """Test get_supported_sites method."""
        with patch('yt_dlp.extractor.list_extractors') as mock_list:
            # Mock extractor with IE_NAME
            mock_extractor = MagicMock()
            mock_extractor.IE_NAME = "youtube"
            mock_list.return_value = [mock_extractor]

            result = universal_client.get_supported_sites()

            assert "youtube" in result
            assert isinstance(result, list)

    def test_get_supported_sites_fallback(self, universal_client):
        """Test get_supported_sites fallback when list_extractors fails."""
        with patch('yt_dlp.extractor.list_extractors') as mock_list:
            mock_list.side_effect = Exception("Test exception")

            result = universal_client.get_supported_sites()

            # Should return fallback list
            assert "youtube" in result
            assert "twitter" in result
            assert isinstance(result, list)

    def test_is_supported_url_supported(self, universal_client):
        """Test is_supported_url with supported URL."""
        with patch('clipscribe.retrievers.universal_video_client.yt_dlp.YoutubeDL') as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value = mock_instance
            mock_instance.extract_info.side_effect = [None, None]  # Both calls succeed

            result = universal_client.is_supported_url("https://youtube.com/watch?v=test")

            assert result is True

    def test_is_supported_url_not_supported(self, universal_client):
        """Test is_supported_url with unsupported URL."""
        with patch('clipscribe.retrievers.universal_video_client.yt_dlp.YoutubeDL') as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value = mock_instance
            # Both calls fail with DownloadError
            mock_instance.extract_info.side_effect = yt_dlp.utils.DownloadError("Not supported")

            result = universal_client.is_supported_url("https://unsupported.com/video")

            assert result is False

    @pytest.mark.asyncio
    async def test_download_audio_success(self, universal_client, mock_video_metadata):
        """Test successful audio download."""
        with patch('clipscribe.retrievers.universal_video_client.yt_dlp.YoutubeDL') as mock_ydl_class, \
             patch('clipscribe.retrievers.universal_video_client.tempfile.mkdtemp') as mock_mkdtemp, \
             patch('clipscribe.retrievers.universal_video_client.os.path.exists') as mock_exists, \
             patch('clipscribe.retrievers.universal_video_client.os.listdir') as mock_listdir, \
             patch.object(universal_client, '_create_metadata_from_info') as mock_create_metadata:

            # Setup mocks
            mock_ydl_instance = MagicMock()
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance

            mock_mkdtemp.return_value = "/tmp/test"
            mock_exists.return_value = True
            mock_listdir.return_value = ["test_video_123.mp3"]
            mock_create_metadata.return_value = mock_video_metadata

            # Mock the extract_info call with proper return values
            mock_info = {
                "title": "Test Video",
                "id": "test_video_123",
                "duration": 300,
                "extractor": "youtube"
            }
            mock_ydl_instance.extract_info.return_value = mock_info

            result = await universal_client.download_audio("https://youtube.com/watch?v=test")

            assert len(result) == 2
            assert result[1].video_id == "test_video_123"

    def test_parse_published_date_various_formats(self, universal_client):
        """Test published date parsing with various formats."""
        test_cases = [
            ("1 hour ago", datetime.now() - timedelta(hours=1)),
            ("2 days ago", datetime.now() - timedelta(days=2)),
            ("1 week ago", datetime.now() - timedelta(weeks=1)),
            ("3 months ago", datetime.now() - timedelta(days=90)),
            ("2 years ago", datetime.now() - timedelta(days=730)),
            ("2023-01-15", datetime(2023, 1, 15)),
        ]

        for date_str, expected_range in test_cases:
            if "ago" in date_str:
                result = universal_client._parse_published_date(date_str)
                # For relative dates, just check it's a datetime object
                assert isinstance(result, datetime)
            else:
                result = universal_client._parse_published_date(date_str)
                assert result == expected_range

    def test_detect_platform(self, universal_client):
        """Test platform detection from URLs."""
        test_cases = [
            ("https://youtube.com/watch?v=test", "youtube"),
            ("https://youtu.be/test", "youtube"),
            ("https://twitter.com/user/status/123", "twitter"),
            ("https://x.com/user/status/123", "x"),
            ("https://tiktok.com/@user/video/123", "tiktok"),
            ("https://vimeo.com/123456", "vimeo"),
            ("https://facebook.com/video/123", "facebook"),
            ("https://instagram.com/p/test/", "instagram"),
            ("https://twitch.tv/user", "twitch"),
            ("https://unknownsite.com/video", "generic"),
        ]

        with patch('clipscribe.retrievers.universal_video_client.yt_dlp.YoutubeDL') as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value = mock_instance

            # Mock successful extraction for unknown URLs
            def mock_extract_info(url, download=False, process=False):
                if "unknownsite" in url:
                    return {"extractor": "generic"}
                return {"extractor": "unknown"}

            mock_instance.extract_info.side_effect = mock_extract_info

            for url, expected_platform in test_cases:
                result = universal_client._detect_platform(url)
                assert result == expected_platform, f"Failed for {url}"

    def test_get_video_sort_order(self, universal_client):
        """Test video sort order mapping."""
        from youtubesearchpython import VideoSortOrder

        test_cases = [
            ("relevance", VideoSortOrder.relevance),
            ("upload_date", VideoSortOrder.uploadDate),
            ("view_count", VideoSortOrder.viewCount),
            ("rating", VideoSortOrder.rating),
            ("newest", VideoSortOrder.uploadDate),
            ("popular", VideoSortOrder.viewCount),
            ("invalid_sort", VideoSortOrder.relevance),  # Default fallback
        ]

        for sort_by, expected_order in test_cases:
            result = universal_client._get_video_sort_order(sort_by)
            assert result == expected_order, f"Failed for {sort_by}"

    @pytest.mark.asyncio
    async def test_download_video_success(self, universal_client, mock_video_metadata):
        """Test successful video download."""
        with patch('clipscribe.retrievers.universal_video_client.tempfile.mkdtemp') as mock_mkdtemp, \
             patch('clipscribe.retrievers.universal_video_client.os.path.join') as mock_join, \
             patch('clipscribe.retrievers.universal_video_client.os.path.exists') as mock_exists, \
             patch('clipscribe.retrievers.universal_video_client.os.path.splitext') as mock_splitext, \
             patch.object(universal_client, 'get_video_info') as mock_get_info, \
             patch('asyncio.create_subprocess_exec') as mock_subprocess, \
             patch('asyncio.subprocess.PIPE') as mock_pipe:

            # Setup mocks
            mock_mkdtemp.return_value = "/tmp/test"
            mock_join.return_value = "/tmp/test/test-video.mp4"
            mock_exists.return_value = True
            mock_splitext.return_value = ("/tmp/test/test-video", ".mp4")
            mock_get_info.return_value = mock_video_metadata

            # Mock subprocess
            mock_process = AsyncMock()
            mock_process.stdout = AsyncMock()
            mock_process.stdout.read = AsyncMock(return_value=b"")
            mock_process.stderr = AsyncMock()
            mock_process.stderr.read = AsyncMock(return_value=b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process

            result = await universal_client.download_video("https://youtube.com/watch?v=test")

            assert len(result) == 2
            assert isinstance(result[0], str)
            assert isinstance(result[1], VideoMetadata)

    @pytest.mark.asyncio
    async def test_download_video_failure(self, universal_client, mock_video_metadata):
        """Test video download failure handling."""
        with patch.object(universal_client, 'get_video_info') as mock_get_info, \
             patch('asyncio.create_subprocess_exec') as mock_subprocess:

            mock_get_info.return_value = mock_video_metadata

            # Mock subprocess failure
            mock_process = AsyncMock()
            mock_process.stdout = AsyncMock()
            mock_process.stdout.read = AsyncMock(return_value=b"")
            mock_process.stderr = AsyncMock()
            mock_process.stderr.read = AsyncMock(return_value=b"Download failed")
            mock_process.returncode = 1
            mock_subprocess.return_value = mock_process

            with pytest.raises(Exception, match="yt-dlp failed"):
                await universal_client.download_video("https://youtube.com/watch?v=test")

    def test_is_playlist_url(self, universal_client):
        """Test playlist URL detection."""
        test_cases = [
            ("https://youtube.com/playlist?list=PLtest", True),
            ("https://youtube.com/watch?v=test&list=PLtest", False),  # Not a playlist URL
            ("https://youtube.com/playlist/test", False),  # Wrong format
            ("https://other.com/playlist?list=PLtest", False),  # Wrong domain
        ]

        for url, expected in test_cases:
            result = universal_client.is_playlist_url(url)
            assert result == expected, f"Failed for {url}"

    @pytest.mark.asyncio
    async def test_get_playlist_urls(self, universal_client):
        """Test playlist URL extraction."""
        with patch('clipscribe.retrievers.universal_video_client.Playlist') as mock_playlist_class:
            mock_playlist = MagicMock()
            mock_playlist.videos = [
                {"link": "https://youtube.com/watch?v=video1"},
                {"link": "https://youtube.com/watch?v=video2"},
            ]
            mock_playlist.hasMoreVideos = False
            mock_playlist_class.return_value = mock_playlist

            result = await universal_client.get_playlist_urls("https://youtube.com/playlist?list=test")

            assert len(result) == 2
            assert "video1" in result[0]
            assert "video2" in result[1]

    @pytest.mark.asyncio
    async def test_extract_playlist_preview(self, universal_client):
        """Test playlist preview extraction."""
        mock_playlist_info = {
            "entries": [
                {
                    "id": "video1",
                    "title": "Video 1",
                    "uploader": "Channel 1",
                    "uploader_id": "channel1",
                    "duration": 300,
                    "description": "Test video 1",
                }
            ],
            "playlist_count": 1,
        }

        with patch('clipscribe.retrievers.universal_video_client.yt_dlp.YoutubeDL') as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance

            def mock_extract_info(url, download=False, process=False):
                return mock_playlist_info

            mock_instance.extract_info.side_effect = mock_extract_info

            preview_videos, total_count = await universal_client.extract_playlist_preview(
                "https://youtube.com/playlist?list=test"
            )

            assert len(preview_videos) == 1
            assert total_count == 1
            assert preview_videos[0].video_id == "video1"

    @pytest.mark.asyncio
    async def test_extract_all_playlist_urls(self, universal_client):
        """Test full playlist URL extraction."""
        mock_playlist_info = {
            "entries": [
                {"id": "video1"},
                {"id": "video2"},
            ]
        }

        with patch('clipscribe.retrievers.universal_video_client.yt_dlp.YoutubeDL') as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance

            def mock_extract_info(url, download=False, process=False):
                return mock_playlist_info

            mock_instance.extract_info.side_effect = mock_extract_info

            result = await universal_client.extract_all_playlist_urls("https://youtube.com/playlist?list=test")

            assert len(result) == 2
            assert "video1" in result[0]
            assert "video2" in result[1]


class TestTemporalIntelligence:
    """Test temporal intelligence extraction methods."""

    def test_extract_chapters_success(self, universal_client):
        """Test successful chapter extraction."""
        mock_info = {
            "chapters": [
                {
                    "title": "Introduction",
                    "start_time": 0.0,
                    "end_time": 60.0,
                    "url": "https://example.com/chapter1"
                },
                {
                    "title": "Main Content",
                    "start_time": 60.0,
                    "end_time": 300.0,
                    "url": "https://example.com/chapter2"
                }
            ]
        }

        chapters = universal_client._extract_chapters(mock_info)

        assert len(chapters) == 2
        assert chapters[0].title == "Introduction"
        assert chapters[0].start_time == 0.0
        assert chapters[0].end_time == 60.0
        assert chapters[1].title == "Main Content"

    def test_extract_chapters_empty(self, universal_client):
        """Test chapter extraction with no chapters."""
        mock_info = {"chapters": []}

        chapters = universal_client._extract_chapters(mock_info)

        assert len(chapters) == 0

    def test_extract_chapters_none(self, universal_client):
        """Test chapter extraction with None chapters."""
        mock_info = {}

        chapters = universal_client._extract_chapters(mock_info)

        assert len(chapters) == 0

    def test_extract_chapters_invalid_data(self, universal_client):
        """Test chapter extraction with invalid data."""
        mock_info = {
            "chapters": [
                {
                    "title": "Valid Chapter",
                    "start_time": 0.0,
                    "end_time": 60.0,
                },
                {
                    "title": None,  # Invalid
                    "start_time": "invalid",  # Invalid
                    "end_time": 120.0,
                }
            ]
        }

        chapters = universal_client._extract_chapters(mock_info)

        # Should only get the valid chapter
        assert len(chapters) == 1
        assert chapters[0].title == "Valid Chapter"

    def test_extract_subtitles_success(self, universal_client):
        """Test successful subtitle extraction."""
        mock_info = {
            "subtitles": {
                "en": [
                    {"url": "https://example.com/en.vtt", "ext": "vtt"}
                ]
            },
            "automatic_captions": {},
            "description": "Test video description"
        }

        subtitles = universal_client._extract_subtitles(mock_info)

        assert subtitles is not None
        assert subtitles.language == "en"
        assert subtitles.full_text == "Test video description"
        assert subtitles.word_level_timing == {}

    def test_extract_subtitles_auto_captions(self, universal_client):
        """Test subtitle extraction with auto captions."""
        mock_info = {
            "subtitles": {},
            "automatic_captions": {
                "en": [
                    {"url": "https://example.com/en-auto.vtt", "ext": "vtt"}
                ]
            },
            "description": "Test video description"
        }

        subtitles = universal_client._extract_subtitles(mock_info)

        assert subtitles is not None
        assert subtitles.language == "en-auto"

    def test_extract_subtitles_fallback_language(self, universal_client):
        """Test subtitle extraction with non-English language."""
        mock_info = {
            "subtitles": {
                "es": [
                    {"url": "https://example.com/es.vtt", "ext": "vtt"}
                ]
            },
            "automatic_captions": {},
            "description": "Test video description"
        }

        subtitles = universal_client._extract_subtitles(mock_info)

        assert subtitles is not None
        assert subtitles.language == "es"

    def test_extract_subtitles_none(self, universal_client):
        """Test subtitle extraction with no subtitles."""
        mock_info = {
            "subtitles": {},
            "automatic_captions": {},
            "description": "Test video description"
        }

        subtitles = universal_client._extract_subtitles(mock_info)

        assert subtitles is None

    def test_extract_sponsorblock_success(self, universal_client):
        """Test successful SponsorBlock extraction."""
        mock_info = {
            "sponsorblock_chapters": [
                {
                    "category": "sponsor",
                    "start_time": 30.0,
                    "end_time": 90.0,
                    "uuid": "test-uuid-1"
                },
                {
                    "category": "intro",
                    "start_time": 0.0,
                    "end_time": 15.0,
                    "uuid": "test-uuid-2"
                }
            ]
        }

        segments = universal_client._extract_sponsorblock(mock_info)

        assert len(segments) == 2
        assert segments[0].category == "sponsor"
        assert segments[0].start_time == 30.0
        assert segments[0].end_time == 90.0
        assert segments[0].uuid == "test-uuid-1"

    def test_extract_sponsorblock_empty(self, universal_client):
        """Test SponsorBlock extraction with no data."""
        mock_info = {}

        segments = universal_client._extract_sponsorblock(mock_info)

        assert len(segments) == 0

    def test_extract_video_metadata(self, universal_client):
        """Test video metadata extraction."""
        mock_info = {
            "title": "Test Video",
            "description": "Test description",
            "duration": 300,
            "upload_date": "20240115",
            "uploader": "Test Channel",
            "view_count": 10000,
            "like_count": 500,
            "comment_count": 100,
            "tags": ["test", "video"],
            "categories": ["Education"],
            "extractor": "youtube",
            "webpage_url": "https://youtube.com/watch?v=test",
            "id": "test123"
        }

        metadata = universal_client._extract_video_metadata(mock_info)

        assert metadata["title"] == "Test Video"
        assert metadata["view_count"] == 10000
        assert metadata["extractor"] == "youtube"
        assert metadata["id"] == "test123"

    def test_extract_word_timing(self, universal_client):
        """Test word-level timing extraction placeholder."""
        mock_info = {"subtitles": {"en": []}}

        timing = universal_client._extract_word_timing(mock_info)

        assert isinstance(timing, dict)
        assert len(timing) == 0

    def test_identify_content_sections(self, universal_client):
        """Test content section identification."""
        mock_info = {"duration": 300}

        # Mock sponsorblock extraction
        with patch.object(universal_client, '_extract_sponsorblock') as mock_extract:
            mock_extract.return_value = [
                VideoSegment("sponsor", 30.0, 90.0),
                VideoSegment("intro", 0.0, 15.0),
                VideoSegment("outro", 270.0, 300.0),
            ]

            sections = universal_client._identify_content_sections(mock_info)

            assert len(sections) == 2  # Content sections split around sponsor
            assert sections[0].category == "content"
            assert sections[0].start_time == 15.0  # After intro
            assert sections[0].end_time == 30.0  # Before sponsor

    def test_identify_content_sections_no_duration(self, universal_client):
        """Test content section identification with no duration."""
        mock_info = {}

        sections = universal_client._identify_content_sections(mock_info)

        assert len(sections) == 0

    @pytest.mark.asyncio
    async def test_extract_temporal_metadata_success(self, universal_client):
        """Test successful temporal metadata extraction."""
        mock_info = {
            "title": "Test Video",
            "extractor": "youtube",
            "chapters": [
                {"title": "Chapter 1", "start_time": 0.0, "end_time": 60.0}
            ],
            "subtitles": {"en": []},
            "sponsorblock_chapters": [
                {"category": "sponsor", "start_time": 30.0, "end_time": 60.0, "uuid": "test"}
            ],
            "duration": 300,
        }

        with patch('clipscribe.retrievers.universal_video_client.yt_dlp.YoutubeDL') as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance
            mock_instance.extract_info.return_value = mock_info

            result = await universal_client.extract_temporal_metadata("https://youtube.com/watch?v=test")

            assert isinstance(result, object)  # TemporalMetadata object
            assert hasattr(result, 'chapters')
            assert hasattr(result, 'subtitles')
            assert hasattr(result, 'sponsorblock_segments')

    @pytest.mark.asyncio
    async def test_extract_temporal_metadata_failure(self, universal_client):
        """Test temporal metadata extraction failure handling."""
        with patch('clipscribe.retrievers.universal_video_client.yt_dlp.YoutubeDL') as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_instance
            mock_instance.extract_info.side_effect = Exception("Extraction failed")

            result = await universal_client.extract_temporal_metadata("https://youtube.com/watch?v=test")

            # Should return empty TemporalMetadata on failure
            assert isinstance(result, object)
            assert hasattr(result, 'chapters')
            assert len(result.chapters) == 0


class TestErrorHandling:
    """Test comprehensive error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_download_audio_retry_success(self, universal_client, mock_video_metadata):
        """Test download audio with successful retry after failure."""
        with patch('clipscribe.retrievers.universal_video_client.yt_dlp.YoutubeDL') as mock_ydl_class, \
             patch('clipscribe.retrievers.universal_video_client.tempfile.mkdtemp') as mock_mkdtemp, \
             patch('clipscribe.retrievers.universal_video_client.os.path.exists') as mock_exists, \
             patch('clipscribe.retrievers.universal_video_client.os.listdir') as mock_listdir, \
             patch.object(universal_client, '_create_metadata_from_info') as mock_create_metadata:

            # Setup mocks
            mock_ydl_instance = MagicMock()
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance

            mock_mkdtemp.return_value = "/tmp/test"
            mock_exists.return_value = True
            mock_listdir.return_value = ["test_video_123.mp3"]
            mock_create_metadata.return_value = mock_video_metadata

            # First call fails, second succeeds
            mock_info = {
                "title": "Test Video",
                "id": "test_video_123",
                "duration": 300,
                "extractor": "youtube"
            }

            mock_ydl_instance.extract_info.side_effect = [
                Exception("ffmpeg error"),  # First attempt fails
                mock_info  # Second attempt succeeds
            ]

            # Mock sleep to avoid actual delay
            with patch('asyncio.sleep'):
                result = await universal_client.download_audio("https://youtube.com/watch?v=test")

                assert len(result) == 2
                assert result[1].video_id == "test_video_123"

    @pytest.mark.asyncio
    async def test_download_audio_all_retries_failed(self, universal_client):
        """Test download audio when all retries fail."""
        with patch('clipscribe.retrievers.universal_video_client.yt_dlp.YoutubeDL') as mock_ydl_class, \
             patch('clipscribe.retrievers.universal_video_client.tempfile.mkdtemp') as mock_mkdtemp, \
             patch.object(universal_client, '_create_metadata_from_info') as mock_create_metadata:

            # Setup mocks
            mock_ydl_instance = MagicMock()
            mock_ydl_class.return_value = mock_ydl_instance

            mock_mkdtemp.return_value = "/tmp/test"
            mock_create_metadata.return_value = mock_video_metadata

            # All attempts fail with non-ffmpeg error
            mock_ydl_instance.extract_info.side_effect = Exception("Network error")

            with pytest.raises(Exception):
                await universal_client.download_audio("https://youtube.com/watch?v=test")

    @pytest.mark.asyncio
    async def test_search_videos_empty_results(self, universal_client):
        """Test YouTube search with empty results."""
        mock_search_result = {
            "result": []
        }

        with patch('clipscribe.retrievers.universal_video_client.CustomSearch') as mock_search:
            mock_search_instance = AsyncMock()
            mock_search_instance.next.return_value = mock_search_result
            mock_search.return_value = mock_search_instance

            results = await universal_client.search_videos("nonexistent query", max_results=5, site="youtube")

            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_videos_malformed_data(self, universal_client):
        """Test YouTube search with malformed data."""
        mock_search_result = {
            "result": [
                {
                    "id": None,  # Malformed ID
                    "title": "Test Video",
                    "channel": None,  # Malformed channel
                    "duration": "invalid",  # Invalid duration
                    "views": "invalid",  # Invalid views
                    "publish_time": "invalid",  # Invalid date
                }
            ]
        }

        with patch('clipscribe.retrievers.universal_video_client.CustomSearch') as mock_search:
            mock_search_instance = AsyncMock()
            mock_search_instance.next.return_value = mock_search_result
            mock_search.return_value = mock_search_instance

            with patch.object(universal_client, '_parse_duration', return_value=0), \
                 patch.object(universal_client, '_parse_view_count', return_value=0), \
                 patch.object(universal_client, '_parse_published_date', return_value=datetime.now()):

                results = await universal_client.search_videos("test query", max_results=5, site="youtube")

                # The malformed data should be skipped due to the exception handling
                assert len(results) == 0

    def test_is_supported_url_partial_failure(self, universal_client):
        """Test URL support check with partial failure."""
        with patch('clipscribe.retrievers.universal_video_client.yt_dlp.YoutubeDL') as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value = mock_instance

            # First call fails, second succeeds
            mock_instance.extract_info.side_effect = [
                yt_dlp.utils.DownloadError("First attempt failed"),
                MagicMock()  # Second attempt succeeds
            ]

            result = universal_client.is_supported_url("https://example.com/video")

            assert result is True

    def test_is_supported_url_complete_failure(self, universal_client):
        """Test URL support check with complete failure."""
        with patch('clipscribe.retrievers.universal_video_client.yt_dlp.YoutubeDL') as mock_ydl:
            mock_instance = MagicMock()
            mock_ydl.return_value = mock_instance

            # Both calls fail
            mock_instance.extract_info.side_effect = yt_dlp.utils.DownloadError("Not supported")

            result = universal_client.is_supported_url("https://unsupported.com/video")

            assert result is False

    def test_create_metadata_from_info_timestamp_parsing(self, universal_client):
        """Test metadata creation with different timestamp formats."""
        # Test with timestamp
        info_with_timestamp = {
            "id": "test123",
            "title": "Test Video",
            "uploader": "Test Channel",
            "duration": 300,
            "url": "https://example.com/video",
            "view_count": 1000,
            "description": "Test",
            "tags": ["test"],
            "timestamp": 1704067200,  # 2024-01-01 00:00:00 UTC
        }

        metadata = universal_client._create_metadata_from_info(info_with_timestamp)
        assert metadata.video_id == "test123"
        assert metadata.title == "Test Video"
        assert isinstance(metadata.published_at, datetime)

    def test_create_metadata_from_info_upload_date_parsing(self, universal_client):
        """Test metadata creation with upload_date format."""
        info_with_upload_date = {
            "id": "test123",
            "title": "Test Video",
            "uploader": "Test Channel",
            "duration": 300,
            "url": "https://example.com/video",
            "view_count": 1000,
            "description": "Test",
            "tags": ["test"],
            "upload_date": "20240101",  # YYYYMMDD format
        }

        metadata = universal_client._create_metadata_from_info(info_with_upload_date)
        assert metadata.video_id == "test123"
        assert isinstance(metadata.published_at, datetime)

    def test_create_metadata_from_info_missing_dates(self, universal_client):
        """Test metadata creation with missing date information."""
        info_no_dates = {
            "id": "test123",
            "title": "Test Video",
            "uploader": "Test Channel",
            "duration": 300,
            "url": "https://example.com/video",
            "view_count": 1000,
            "description": "Test",
            "tags": ["test"],
        }

        metadata = universal_client._create_metadata_from_info(info_no_dates)
        assert metadata.video_id == "test123"
        assert isinstance(metadata.published_at, datetime)  # Should default to now

    @pytest.mark.asyncio
    async def test_search_channel_with_pagination(self, universal_client):
        """Test channel search with pagination."""
        with patch('clipscribe.retrievers.universal_video_client.Channel') as mock_channel_class, \
             patch('clipscribe.retrievers.universal_video_client.Playlist') as mock_playlist_class:

            # Mock channel
            mock_channel = AsyncMock()
            mock_channel.get = AsyncMock(return_value={"id": "test_channel", "title": "Test Channel"})
            mock_channel_class.get = AsyncMock(return_value=mock_channel)

            # Mock playlist with multiple pages
            mock_playlist = MagicMock()
            mock_playlist.videos = [
                {"id": "video1", "title": "Video 1", "duration": "5:00", "publishedTime": "2024-01-01", "viewCount": {"text": "1000 views"}, "description": "Test"},
                {"id": "video2", "title": "Video 2", "duration": "10:00", "publishedTime": "2024-01-02", "viewCount": {"text": "2000 views"}, "description": "Test 2"},
            ]
            mock_playlist.hasMoreVideos = True
            mock_playlist.next = AsyncMock()
            mock_playlist.url = "https://youtube.com/playlist?list=test"
            mock_playlist_class.return_value = mock_playlist

            results = await universal_client.search_channel("test_channel", max_results=5, sort_by="newest")

            assert len(results) == 2
            assert results[0].video_id == "video1"
            assert results[1].video_id == "video2"

    @pytest.mark.asyncio
    async def test_search_channel_empty(self, universal_client):
        """Test channel search with no videos."""
        with patch('clipscribe.retrievers.universal_video_client.Channel') as mock_channel_class:
            mock_channel = AsyncMock()
            mock_channel.get.return_value = None  # Channel not found
            mock_channel_class.get.return_value = mock_channel

            results = await universal_client.search_channel("nonexistent_channel")

            assert len(results) == 0

    def test_progress_hook_empty(self, universal_client):
        """Test that progress hook method exists and is empty."""
        # This method is called by download_video but is empty in the implementation
        universal_client._progress_hook({"status": "downloading"})
        # Should not raise any exception