"""Integration tests for provider pipeline (mocked APIs)."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path
from clipscribe.providers.factory import get_transcription_provider, get_intelligence_provider


@pytest.mark.asyncio
@pytest.mark.integration
async def test_voxtral_grok_pipeline():
    """Test complete Voxtral → Grok pipeline with mocked APIs."""
    from clipscribe.transcribers.voxtral_transcriber import VoxtralTranscriptionResult
    
    # Mock Voxtral response
    mock_voxtral_result = VoxtralTranscriptionResult(
        text="Test transcript text",
        language="en",
        duration=60.0,
        cost=0.001,
        model="voxtral-mini-2507",
        segments=[{"start": 0.0, "end": 60.0, "text": "Test transcript text"}],
    )
    
    # Mock Grok response
    mock_grok_response = {
        "choices": [{
            "message": {
                "content": '{"entities": [], "relationships": [], "topics": [], "key_moments": [], "sentiment": {}}'
            }
        }],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50, "cached_tokens": 0}
    }
    
    with patch.dict("os.environ", {"MISTRAL_API_KEY": "test-key", "XAI_API_KEY": "test-key"}):
        with patch("clipscribe.transcribers.voxtral_transcriber.VoxtralTranscriber.transcribe_audio", new_callable=AsyncMock, return_value=mock_voxtral_result):
            with patch("clipscribe.retrievers.grok_client.GrokAPIClient.chat_completion", new_callable=AsyncMock, return_value=mock_grok_response):
                # Get providers
                transcriber = get_transcription_provider("voxtral")
                extractor = get_intelligence_provider("grok")
                
                # Transcribe
                transcript = await transcriber.transcribe("test.mp3", diarize=False)
                assert transcript.provider == "voxtral"
                assert transcript.cost == 0.001
                
                # Extract intelligence
                intelligence = await extractor.extract(transcript)
                assert intelligence.provider == "grok"
                assert intelligence.cost > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_provider_cost_tracking():
    """Test that providers accurately track costs."""
    from clipscribe.transcribers.voxtral_transcriber import VoxtralTranscriptionResult
    
    mock_result = VoxtralTranscriptionResult(
        text="Test", language="en", duration=1800.0, cost=0.03, model="voxtral-mini-2507"
    )
    
    with patch.dict("os.environ", {"MISTRAL_API_KEY": "test-key"}):
        with patch("clipscribe.transcribers.voxtral_transcriber.VoxtralTranscriber.transcribe_audio", new_callable=AsyncMock, return_value=mock_result):
            provider = get_transcription_provider("voxtral")
            
            # Estimate should match actual
            estimated = provider.estimate_cost(1800.0)  # 30 minutes
            result = await provider.transcribe("test.mp3", diarize=False)
            
            assert abs(estimated - result.cost) < 0.001  # Within $0.001

