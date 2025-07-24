import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
import os
import json
from pathlib import Path

# Since the script is outside the package, we need to import it carefully
from examples.pbs_fast_batch import process_batch_fast
from clipscribe.models import VideoIntelligence, VideoMetadata


@pytest.mark.asyncio
@patch('examples.pbs_fast_batch.VideoIntelligenceRetriever')
@patch('examples.pbs_fast_batch.MultiVideoProcessor')
async def test_batch_processing_end_to_end_success(mock_retriever_class, mock_processor_class, tmp_path):
    """Test that batch processing works end-to-end with successful videos."""
    test_urls = [
        "https://www.youtube.com/watch?v=test1",
        "https://www.youtube.com/watch?v=test2"
    ]
    
    # Mock VideoIntelligenceRetriever
    mock_instance = AsyncMock()
    
    async def mock_process_url(url):
        # Create real VideoIntelligence object instead of MagicMock
        metadata = VideoMetadata(
            title=f"Test Video for {url}",
            description="Test description",
            duration=60.0,
            platform="youtube",
            url=url,
            video_id=url.split("=")[-1],
            published_date=None,
            view_count=None,
            channel=None
        )
        
        vi = VideoIntelligence(
            metadata=metadata,
            transcript="Test transcript",
            summary="Test summary",
            key_points=[],
            entities=[],
            relationships=[],
            topics=["test"],
            sentiment=None,
            processing_cost=0.035,
            duration=60.0,
            extraction_metadata={}
        )
        return vi
        
    mock_instance.process_url = AsyncMock(side_effect=mock_process_url)
    mock_instance.save_all_formats = lambda *args, **kwargs: None  # Synchronous mock
    mock_instance.save_collection_outputs = lambda *args, **kwargs: None  # Synchronous mock
    mock_retriever_class.return_value = mock_instance

    mock_processor_instance = AsyncMock()
    mock_processor_instance.process_videos = AsyncMock(return_value=AsyncMock())
    mock_processor_class.return_value = mock_processor_instance

    with patch('pathlib.Path.mkdir'):
        with patch('clipscribe.utils.filename.create_output_structure', return_value={'directory': tmp_path}):
            successful, failures = await process_batch_fast(test_urls, concurrent_limit=2)

    assert len(successful) == 2
    assert len(failures) == 0
    # Note: save method calls not asserted since using lambda functions


@pytest.mark.asyncio
@patch('examples.pbs_fast_batch.VideoIntelligenceRetriever')
@patch('examples.pbs_fast_batch.MultiVideoProcessor')
async def test_batch_processing_handles_failures_gracefully(mock_retriever_class, mock_processor_class, tmp_path):
    """Test that batch processing handles failures gracefully."""
    test_urls = [
        "https://www.youtube.com/watch?v=success1",
        "https://www.youtube.com/watch?v=fail1",  # This will fail
        "https://www.youtube.com/watch?v=success2"
    ]
    
    # Mock VideoIntelligenceRetriever with mixed success/failure
    mock_instance = AsyncMock()
    
    async def mock_process_url(url):
        if "fail" in url:
            raise Exception("Simulated processing failure")
        
        # Create real VideoIntelligence object instead of MagicMock
        metadata = VideoMetadata(
            title=f"Test Video for {url}",
            description="Test description",
            duration=60.0,
            platform="youtube",
            url=url,
            video_id=url.split("=")[-1],
            published_date=None,
            view_count=None,
            channel=None
        )
        
        vi = VideoIntelligence(
            metadata=metadata,
            transcript="Test transcript",
            summary="Test summary",
            key_points=[],
            entities=[],
            relationships=[],
            topics=["test"],
            sentiment=None,
            processing_cost=0.035,
            duration=60.0,
            extraction_metadata={}
        )
        return vi
        
    mock_instance.process_url = AsyncMock(side_effect=mock_process_url)
    mock_instance.save_all_formats = lambda *args, **kwargs: None  # Synchronous mock
    mock_instance.save_collection_outputs = lambda *args, **kwargs: None  # Synchronous mock
    mock_retriever_class.return_value = mock_instance

    mock_processor_instance = AsyncMock()
    mock_processor_instance.process_videos = AsyncMock(return_value=AsyncMock())
    mock_processor_class.return_value = mock_processor_instance

    with patch('pathlib.Path.mkdir'):
        with patch('clipscribe.utils.filename.create_output_structure', return_value={'directory': tmp_path}):
            successful, failures = await process_batch_fast(test_urls, concurrent_limit=3)

    # Should have 2 successful and 1 failure
    assert len(successful) == 2
    assert len(failures) == 1 