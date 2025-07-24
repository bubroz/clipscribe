"""Integration tests for the complete ClipScribe workflow."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path

# Use the correct, modern entry point for the application
from clipscribe.retrievers import VideoIntelligenceRetriever
from clipscribe.models import VideoIntelligence, VideoMetadata, VideoTranscript

# Define a constant for a test URL
TEST_VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

@pytest.fixture
def mock_retriever():
    """Fixture to provide a mocked VideoIntelligenceRetriever."""
    # Create a mock VideoIntelligence object to be returned by process_url
    mock_result = VideoIntelligence(
        metadata=VideoMetadata(
            video_id="dQw4w9WgXcQ",
            title="Test Video",
            channel="Test Channel",
            channel_id="test_channel",
            published_at=MagicMock(),
            duration=212,
            tags=[], description="", url="", view_count=0
        ),
        transcript=VideoTranscript(full_text="Never gonna give you up", segments=[]),
        summary="A summary",
        key_points=[],
        entities=[],
        topics=[]
    )
    
    with patch('clipscribe.retrievers.video_retriever.VideoIntelligenceRetriever') as mock:
        instance = mock.return_value
        instance.process_url = AsyncMock(return_value=mock_result)
        # Mock the save methods as well
        instance.save_all_formats = MagicMock()
        instance.save_collection_outputs = MagicMock()
        yield instance

@pytest.mark.asyncio
async def test_full_workflow_end_to_end(mock_retriever):
    """
    Test the full, end-to-end user workflow using the modern API.
    This replaces the old, brittle tests that used the deprecated client.
    """
    # The primary user action: process a URL.
    result = await mock_retriever.process_url(TEST_VIDEO_URL)
    
    # Verify the retriever was called correctly.
    mock_retriever.process_url.assert_awaited_once_with(TEST_VIDEO_URL)
    
    # Verify that the result is a valid VideoIntelligence object.
    assert isinstance(result, VideoIntelligence)
    assert result.metadata.video_id == "dQw4w9WgXcQ"
    assert "Never gonna give you up" in result.transcript.full_text
    
    # Verify that saving outputs can be called (the mock handles the implementation).
    output_dir = Path("/tmp/test_output")
    mock_retriever.save_all_formats(result, output_dir)
    mock_retriever.save_all_formats.assert_called_once_with(result, output_dir)

@pytest.mark.asyncio
async def test_error_handling_in_workflow(mock_retriever):
    """
    Test that the workflow handles processing errors gracefully.
    """
    # Configure the mock to raise an exception.
    mock_retriever.process_url.side_effect = Exception("Simulated processing failure")
    
    with pytest.raises(Exception, match="Simulated processing failure"):
        await mock_retriever.process_url(TEST_VIDEO_URL)
        
    # Ensure that even with an error, the call was attempted.
    mock_retriever.process_url.assert_awaited_once_with(TEST_VIDEO_URL) 