# tests/unit/test_video_retriever.py
import pytest
from unittest.mock import patch, AsyncMock
from clipscribe.retrievers.video_retriever import VideoIntelligenceRetriever
from tests.helpers import create_mock_video_intelligence


@pytest.mark.asyncio
async def test_process_url_success():
    """Test successful processing of a URL."""
    with patch(
        "clipscribe.retrievers.video_retriever.VideoIntelligenceRetriever._process_video_enhanced",
        new_callable=AsyncMock,
    ) as mock_process:
        mock_process.return_value = create_mock_video_intelligence()
        retriever = VideoIntelligenceRetriever()

        with patch.object(retriever.video_client, "is_supported_url", return_value=True):
            result = await retriever.process_url("https://test.com/video")
            mock_process.assert_called_once_with("https://test.com/video", None)
            assert result is not None


@pytest.mark.asyncio
async def test_process_url_unsupported(mocker):
    """Test handling of an unsupported URL."""
    retriever = VideoIntelligenceRetriever()
    mocker.patch.object(retriever.video_client, "is_supported_url", return_value=False)
    result = await retriever.process_url("http://unsupported.url/video")
    assert result is None
