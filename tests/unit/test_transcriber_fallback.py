import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from clipscribe.retrievers.transcriber import GeminiFlashTranscriber, TemporalIntelligenceLevel

# Mock the VertexAITranscriber to simulate its presence and behavior
class MockVertexAITranscriber:
    async def transcribe_with_vertex(self, *args, **kwargs):
        # This method will be mocked to either succeed or fail
        pass

@pytest.fixture
def mock_settings(mocker):
    """Fixture to mock the Settings class and control use_vertex_ai."""
    mock_settings_instance = MagicMock()
    mocker.patch('clipscribe.retrievers.transcriber.Settings', return_value=mock_settings_instance)
    
    # Configure mocks to behave like real objects
    mock_settings_instance.get_temporal_intelligence_config.return_value = {
        'level': TemporalIntelligenceLevel.ENHANCED
    }
    mock_settings_instance.gemini_request_timeout = 300
    mock_settings_instance.estimate_cost.return_value = 0.05
    
    return mock_settings_instance

@pytest.fixture
def mock_gemini_api(mocker):
    """Fixture to mock the standard Gemini API calls."""
    mocker.patch('google.generativeai.configure')
    mocker.patch('clipscribe.retrievers.gemini_pool.GeminiPool', MagicMock())
    
    # Mock the direct Gemini transcription call to return a predictable success value
    mocker.patch(
        'clipscribe.retrievers.transcriber.GeminiFlashTranscriber._retry_generate_content',
        new_callable=AsyncMock,
        return_value=MagicMock(text='{"summary": "Gemini Success"}')
    )
    # Mock the file upload part of the Gemini path
    mocker.patch('google.generativeai.upload_file', return_value=MagicMock(state=MagicMock(name="ACTIVE")))
    mocker.patch('google.generativeai.get_file', return_value=MagicMock(state=MagicMock(name="ACTIVE")))
    mocker.patch('google.generativeai.delete_file')


@pytest.mark.asyncio
@patch('clipscribe.retrievers.transcriber.VertexAITranscriber', new_callable=AsyncMock)
async def test_transcriber_uses_vertex_ai_when_enabled_and_successful(mock_vertex_class, mock_settings, mock_gemini_api):
    """
    Verify that the transcriber correctly uses Vertex AI when it is enabled and succeeds,
    and does NOT fall back to the standard Gemini API.
    """
    mock_settings.use_vertex_ai = True
    
    # Mock a successful Vertex AI response with the expected object structure
    mock_vertex_result = {'transcript': 'Vertex Success'}
    mock_vertex_class.transcribe_with_vertex.return_value = mock_vertex_result
    
    transcriber = GeminiFlashTranscriber()
    # Manually assign the mocked instance
    transcriber.vertex_transcriber = mock_vertex_class.return_value

    result = await transcriber.transcribe_audio("fake_audio.mp3", duration=60)
    
    # Assert that Vertex AI was called
    mock_vertex_class.transcribe_with_vertex.assert_awaited_once()
    
    # Assert that the result is from Vertex AI
    assert result['transcript'] == 'Vertex Success'
    
    # Assert that the standard Gemini API was NOT called
    GeminiFlashTranscriber._retry_generate_content.assert_not_called()


@pytest.mark.asyncio
@patch('clipscribe.retrievers.transcriber.VertexAITranscriber', new_callable=MagicMock)
async def test_transcriber_falls_back_to_gemini_api_on_vertex_failure(mock_vertex_class, mock_settings, mock_gemini_api, caplog):
    """
    Verify that the transcriber gracefully falls back to the standard Gemini API
    when Vertex AI is enabled but fails.
    """
    mock_settings.use_vertex_ai = True
    
    # Mock a failing Vertex AI response
    mock_vertex_instance = mock_vertex_class
    mock_vertex_instance.transcribe_with_vertex = AsyncMock(side_effect=Exception("Vertex AI processing error"))
    
    transcriber = GeminiFlashTranscriber()
    # Manually assign the mocked instance
    transcriber.vertex_transcriber = mock_vertex_instance

    result = await transcriber.transcribe_audio("fake_audio.mp3", duration=60)
    
    # Assert that Vertex AI was called and failed
    mock_vertex_instance.transcribe_with_vertex.assert_awaited_once()
    
    # Assert that a warning was logged about the fallback
    assert "Vertex AI transcription failed" in caplog.text
    assert "Falling back to standard Gemini API" in caplog.text
    
    # Assert that the standard Gemini API was called as a fallback
    GeminiFlashTranscriber._retry_generate_content.assert_called()
    
    # Assert that the final result is from the successful Gemini API call
    assert result["summary"] == "Gemini Success"


@pytest.mark.asyncio
async def test_transcriber_uses_gemini_api_when_vertex_is_disabled(mock_settings, mock_gemini_api):
    """
    Verify that the transcriber uses the standard Gemini API directly when
    use_vertex_ai is set to False.
    """
    mock_settings.use_vertex_ai = False
    
    transcriber = GeminiFlashTranscriber()
    # Ensure vertex_transcriber is None, as it would be in the real code path
    transcriber.vertex_transcriber = None

    result = await transcriber.transcribe_audio("fake_audio.mp3", duration=60)

    # Assert that the standard Gemini API was called
    GeminiFlashTranscriber._retry_generate_content.assert_called()
    
    # Assert that the result is from the Gemini API call
    assert result["summary"] == "Gemini Success" 