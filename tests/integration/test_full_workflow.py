# tests/integration/test_full_workflow.py
import pytest
from unittest.mock import patch, AsyncMock
from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever
from clipscribe.models import VideoIntelligence
from tests.helpers import create_mock_video_intelligence

TEST_VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


@pytest.mark.asyncio
async def test_full_workflow_end_to_end():
    """Test the full end-to-end workflow for a single video."""
    with (
        patch("clipscribe.retrievers.video_retriever.UniversalVideoClient") as mock_client,
        patch("clipscribe.retrievers.video_retriever.GeminiFlashTranscriber") as mock_transcriber,
        patch(
            "clipscribe.retrievers.video_retriever.AdvancedHybridExtractor", create=True
        ) as mock_extractor,
    ):

        mock_video = create_mock_video_intelligence()

        # Correctly mock the async download_video to be awaitable
        mock_client.return_value.download_video = AsyncMock(
            return_value=("test.mp4", mock_video.metadata)
        )

        mock_transcriber.return_value.transcribe_video = AsyncMock(
            return_value={
                "transcript": "Test transcript",
                "summary": "A summary",
                "key_points": [],
                "topics": [],
                "entities": [],
                "relationships": [],
                "dates": [],
                "processing_cost": 0.01,
            }
        )
        mock_extractor.return_value.extract_all = AsyncMock(return_value=mock_video)

        retriever = VideoIntelligenceRetriever()
        result = await retriever.process_url("https://test.com/video")

        assert result is not None
        assert isinstance(result, VideoIntelligence)
        assert result.transcript.full_text == "Test transcript"
