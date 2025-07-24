import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
import os
import json
from pathlib import Path

# Since the script is outside the package, we need to import it carefully
from examples.pbs_fast_batch import process_batch_fast
from clipscribe.models import VideoIntelligence


@pytest.mark.asyncio
@patch('examples.pbs_fast_batch.VideoIntelligenceRetriever')
@patch('examples.pbs_fast_batch.MultiVideoProcessor')
async def test_batch_processing_end_to_end_success(mock_retriever_class, mock_processor_class, tmp_path):
    """
    Verify that the pbs_fast_batch script runs end-to-end successfully.
    """
    test_urls = [
        "https://www.youtube.com/watch?v=test1",
        "https://www.youtube.com/watch?v=test2"
    ]

    # Create a mock that returns a coroutine which resolves to a VI object
    mock_instance = MagicMock()
    
    async def mock_process_url(*args, **kwargs):
        vi = MagicMock(spec=VideoIntelligence)
        vi.entities = [] # Ensure the .entities attribute exists
        vi.processing_cost = 0.035
        return vi
        
    mock_instance.process_url = AsyncMock(side_effect=mock_process_url)
    mock_retriever_class.return_value = mock_instance

    mock_processor_instance = MagicMock()
    mock_processor_instance.process_videos = AsyncMock(return_value=MagicMock())
    mock_processor_class.return_value = mock_processor_instance

    with patch('pathlib.Path.mkdir'):
        with patch('clipscribe.utils.filename.create_output_structure', return_value={'directory': tmp_path}):
            successful, failures = await process_batch_fast(test_urls, concurrent_limit=2)

    assert len(successful) == 2
    assert len(failures) == 0
    mock_instance.save_all_formats.assert_called()
    mock_instance.save_collection_outputs.assert_called()


@pytest.mark.asyncio
@patch('examples.pbs_fast_batch.VideoIntelligenceRetriever')
@patch('examples.pbs_fast_batch.MultiVideoProcessor')
async def test_batch_processing_handles_failures_gracefully(mock_retriever_class, mock_processor_class, tmp_path):
    """
    Verify that the script handles failed videos gracefully.
    """
    test_urls = [
        "https://www.youtube.com/watch?v=success1",
        "https://www.youtube.com/watch?v=fail1",
        "https://www.youtube.com/watch?v=success2"
    ]

    async def mock_process_url_with_failure(url):
        if "fail1" in url:
            raise Exception("Simulated processing failure")
        
        vi = MagicMock(spec=VideoIntelligence)
        vi.entities = []
        vi.processing_cost = 0.035
        return vi

    mock_instance = MagicMock()
    mock_instance.process_url = AsyncMock(side_effect=mock_process_url_with_failure)
    mock_retriever_class.return_value = mock_instance

    mock_processor_instance = MagicMock()
    mock_processor_instance.process_videos = AsyncMock(return_value=MagicMock())
    mock_processor_class.return_value = mock_processor_instance

    with patch('pathlib.Path.mkdir'):
        with patch('clipscribe.utils.filename.create_output_structure', return_value={'directory': tmp_path}):
            successful, failures = await process_batch_fast(test_urls, concurrent_limit=3)

    assert len(successful) == 2
    assert len(failures) == 1
    assert mock_instance.save_all_formats.call_count == 2
    mock_instance.save_collection_outputs.assert_called_once() 