# tests/unit/test_transcriber.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from clipscribe.retrievers.transcriber import GeminiFlashTranscriber
from tests.helpers import create_mock_video_intelligence


@pytest.fixture
def transcriber():
    """Fixture to create a GeminiFlashTranscriber instance with mocked dependencies."""
    with patch("googleapiclient.discovery.build"), patch("clipscribe.retrievers.transcriber.genai"):
        return GeminiFlashTranscriber()


@pytest.mark.asyncio
async def test_transcribe_video_success(transcriber):
    """Test successful video transcription."""
    with patch.object(transcriber, "_retry_generate_content", new_callable=AsyncMock) as mock_retry:
        mock_response = Mock()
        mock_response.text = '{"transcript": "Test transcript", "summary": "A summary"}'
        mock_retry.return_value = mock_response

        with (
            patch("clipscribe.retrievers.transcriber.genai.upload_file", new_callable=AsyncMock),
            patch("clipscribe.retrievers.transcriber.genai.get_file", new_callable=AsyncMock),
            patch("clipscribe.retrievers.transcriber.genai.delete_file", new_callable=AsyncMock),
            patch.object(
                transcriber,
                "_parse_json_response",
                return_value={
                    "transcript": "Test transcript",
                    "summary": "A summary",
                    "key_points": [],
                    "entities": [],
                    "topics": [],
                    "relationships": [],
                    "dates": [],
                },
            ),
        ):

            result = await transcriber.transcribe_video("test.mp4", 300)
            assert result["transcript"] == "Test transcript"
