# tests/unit/test_video_retriever.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever
from tests.helpers import create_mock_video_intelligence, create_mock_video_metadata


@pytest.mark.asyncio
async def test_process_url_success():
    """Test successful processing of a URL with new modular structure."""
    mock_video_intel = create_mock_video_intelligence()

    with patch.object(VideoIntelligenceRetriever, '__init__', return_value=None) as mock_init:
        retriever = VideoIntelligenceRetriever()
        retriever.processor = MagicMock()

        with patch.object(retriever.processor, 'process_url', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_video_intel

            result = await retriever.process_url("https://www.youtube.com/watch?v=test123")

            mock_process.assert_called_once_with("https://www.youtube.com/watch?v=test123")
            assert result == mock_video_intel


@pytest.mark.asyncio
async def test_process_url_failure():
    """Test handling of processing failure."""
    with patch.object(VideoIntelligenceRetriever, '__init__', return_value=None):
        retriever = VideoIntelligenceRetriever()
        retriever.processor = MagicMock()

        with patch.object(retriever.processor, 'process_url', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = None

            result = await retriever.process_url("https://www.youtube.com/watch?v=test123")

            assert result is None


@pytest.mark.asyncio
async def test_search_success():
    """Test successful video search."""
    mock_results = [create_mock_video_metadata() for _ in range(2)]

    with patch.object(VideoIntelligenceRetriever, '__init__', return_value=None):
        retriever = VideoIntelligenceRetriever()
        retriever.processor = MagicMock()

        with patch.object(retriever.processor.downloader, 'search_videos', return_value=mock_results), \
             patch.object(retriever.processor, 'process_url', new_callable=AsyncMock) as mock_process:

            mock_process.return_value = create_mock_video_intelligence()

            results = await retriever.search("test query", max_results=2)

            assert len(results) == 2
            retriever.processor.downloader.search_videos.assert_called_once_with("test query", 2, "youtube")


@pytest.mark.asyncio
async def test_search_empty_results():
    """Test search with no results."""
    with patch.object(VideoIntelligenceRetriever, '__init__', return_value=None):
        retriever = VideoIntelligenceRetriever()
        retriever.processor = MagicMock()

        with patch.object(retriever.processor.downloader, 'search_videos', return_value=[]):
            results = await retriever.search("empty query")

            assert results == []


def test_save_transcript_delegation():
    """Test that save_transcript delegates to processor."""
    mock_video = create_mock_video_intelligence()
    mock_result = {"txt": "/path/to/transcript.txt"}

    with patch.object(VideoIntelligenceRetriever, '__init__', return_value=None):
        retriever = VideoIntelligenceRetriever()
        retriever.processor = MagicMock()

        with patch.object(retriever.processor, 'save_transcript', return_value=mock_result) as mock_save:
            result = retriever.save_transcript(mock_video, "output_dir", ["txt"])

            assert result == mock_result
            mock_save.assert_called_once_with(mock_video, "output_dir", ["txt"])


def test_save_all_formats_delegation():
    """Test that save_all_formats delegates to processor."""
    mock_video = create_mock_video_intelligence()
    mock_result = {"json": "/path/to/video.json", "txt": "/path/to/transcript.txt"}

    with patch.object(VideoIntelligenceRetriever, '__init__', return_value=None):
        retriever = VideoIntelligenceRetriever()
        retriever.processor = MagicMock()

        with patch.object(retriever.processor, 'save_all_formats', return_value=mock_result) as mock_save:
            result = retriever.save_all_formats(mock_video, "output_dir", True)

            assert result == mock_result
            mock_save.assert_called_once_with(mock_video, "output_dir", True)


def test_get_stats_delegation():
    """Test that get_stats delegates to processor."""
    mock_stats = {
        "videos_processed": 5,
        "total_cost": 1.25,
        "average_cost": 0.25
    }

    with patch.object(VideoIntelligenceRetriever, '__init__', return_value=None):
        retriever = VideoIntelligenceRetriever()
        retriever.processor = MagicMock()

        with patch.object(retriever.processor, 'get_stats', return_value=mock_stats) as mock_get_stats:
            result = retriever.get_stats()

            assert result == mock_stats
            mock_get_stats.assert_called_once()


def test_get_saved_files():
    """Test getting saved files paths."""
    mock_video = create_mock_video_intelligence()

    with patch.object(VideoIntelligenceRetriever, '__init__', return_value=None):
        retriever = VideoIntelligenceRetriever()

        result = retriever.get_saved_files(mock_video)

        # The method currently returns empty dict as placeholder
        assert result == {}


@pytest.mark.asyncio
async def test_retrieve_url():
    """Test retrieve method with URL."""
    mock_video_intel = create_mock_video_intelligence()

    with patch.object(VideoIntelligenceRetriever, '__init__', return_value=None):
        retriever = VideoIntelligenceRetriever()
        retriever.processor = MagicMock()

        # Create mock metadata with the test URL
        mock_metadata = create_mock_video_metadata(video_id="test123", title="Test Video")
        mock_metadata.url = "https://www.youtube.com/watch?v=test123"

        with patch.object(retriever.processor.downloader, 'search_videos', return_value=[mock_metadata]), \
             patch.object(retriever.processor, 'process_url', new_callable=AsyncMock) as mock_process, \
             patch.object(retriever.processor.output_formatter, '_to_chimera_format') as mock_chimera:

            mock_process.return_value = mock_video_intel
            mock_chimera.return_value = {"type": "video", "content": "test"}

            result = await retriever.retrieve("https://www.youtube.com/watch?v=test123")

            assert len(result) == 1
            mock_process.assert_called_once_with("https://www.youtube.com/watch?v=test123")


@pytest.mark.asyncio
async def test_retrieve_search():
    """Test retrieve method with search query."""
    mock_results = [create_mock_video_metadata() for _ in range(2)]

    with patch.object(VideoIntelligenceRetriever, '__init__', return_value=None):
        retriever = VideoIntelligenceRetriever()
        retriever.processor = MagicMock()

        with patch.object(retriever.processor.downloader, 'search_videos', return_value=mock_results), \
             patch.object(retriever.processor, 'process_url', new_callable=AsyncMock) as mock_process, \
             patch.object(retriever.processor.output_formatter, '_to_chimera_format') as mock_chimera:

            mock_process.return_value = create_mock_video_intelligence()
            mock_chimera.return_value = {"type": "video", "content": "test"}

            results = await retriever.retrieve("test search query", max_results=2)

            assert len(results) == 2


@pytest.mark.asyncio
async def test_retrieve_process_failure():
    """Test retrieve method when processing fails."""
    with patch.object(VideoIntelligenceRetriever, '__init__', return_value=None):
        retriever = VideoIntelligenceRetriever()
        retriever.processor = MagicMock()

        with patch.object(retriever.processor, 'process_url', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = None

            result = await retriever.retrieve("https://www.youtube.com/watch?v=test123")

            assert result == []


def test_get_video_metadata_dict():
    """Test metadata extraction helper."""
    mock_video = create_mock_video_intelligence()

    with patch.object(VideoIntelligenceRetriever, '__init__', return_value=None):
        retriever = VideoIntelligenceRetriever()

        result = retriever._get_video_metadata_dict(mock_video)

        assert result["title"] == mock_video.metadata.title
        assert result["url"] == mock_video.metadata.url
        assert result["channel"] == mock_video.metadata.channel
        assert result["duration"] == mock_video.metadata.duration


def test_get_video_metadata_dict_none_video():
    """Test metadata extraction with None video."""
    with patch.object(VideoIntelligenceRetriever, '__init__', return_value=None):
        retriever = VideoIntelligenceRetriever()

        result = retriever._get_video_metadata_dict(None)

        assert result["title"] == "Unknown"
        assert result["url"] == "Unknown"
        assert result["channel"] == "Unknown"
        assert result["duration"] == 0


@pytest.mark.asyncio
async def test_legacy_method_aliases():
    """Test that legacy method aliases work."""
    mock_video_intel = create_mock_video_intelligence()

    with patch.object(VideoIntelligenceRetriever, '__init__', return_value=None):
        retriever = VideoIntelligenceRetriever()
        retriever.processor = MagicMock()

        with patch.object(retriever.processor, 'process_url', new_callable=AsyncMock) as mock_process:
            mock_process.return_value = mock_video_intel

            # Test _process_video_enhanced
            result1 = await retriever._process_video_enhanced("https://test.com/video")
            assert result1 == mock_video_intel

            # Test _process_video
            result2 = await retriever._process_video("https://test.com/video")
            assert result2 == mock_video_intel

            assert mock_process.call_count == 2


def test_save_collection_outputs_delegation():
    """Test save_collection_outputs delegation (now returns empty dict)."""
    mock_collection = MagicMock()

    with patch.object(VideoIntelligenceRetriever, '__init__', return_value=None):
        retriever = VideoIntelligenceRetriever()

        result = retriever.save_collection_outputs(mock_collection, "output_dir")

        assert result == {}
