"""Unit tests for VoxtralProvider."""

from unittest.mock import AsyncMock, patch

import pytest

from clipscribe.providers.transcription.voxtral import VoxtralProvider
from clipscribe.transcribers.voxtral_transcriber import VoxtralTranscriptionResult


@pytest.fixture
def mock_voxtral_result():
    """Mock VoxtralTranscriptionResult."""
    return VoxtralTranscriptionResult(
        text="This is a test transcript.",
        language="en",
        duration=60.0,
        cost=0.001,
        model="voxtral-mini-2507",
        confidence=0.95,
        segments=[
            {"start": 0.0, "end": 5.0, "text": "This is a test transcript.", "confidence": 0.95}
        ],
    )


@pytest.mark.asyncio
async def test_voxtral_provider_transcribe(mock_voxtral_result):
    """Test Voxtral provider transcription."""
    with patch.dict("os.environ", {"MISTRAL_API_KEY": "test-key"}):
        with patch(
            "clipscribe.transcribers.voxtral_transcriber.VoxtralTranscriber.transcribe_audio",
            new_callable=AsyncMock,
            return_value=mock_voxtral_result,
        ):
            provider = VoxtralProvider()
            result = await provider.transcribe("test.mp3", diarize=False)

            assert result.provider == "voxtral"
            assert result.language == "en"
            assert result.duration == 60.0
            assert result.speakers == 0  # Voxtral doesn't support speakers
            assert result.cost == 0.001
            assert len(result.segments) == 1


@pytest.mark.asyncio
async def test_voxtral_diarization_raises_error():
    """Test that requesting diarization raises ValueError."""
    with patch.dict("os.environ", {"MISTRAL_API_KEY": "test-key"}):
        provider = VoxtralProvider()

        with pytest.raises(ValueError, match="does not support speaker diarization"):
            await provider.transcribe("test.mp3", diarize=True)


def test_voxtral_cost_estimation():
    """Test Voxtral cost estimation."""
    with patch.dict("os.environ", {"MISTRAL_API_KEY": "test-key"}):
        provider = VoxtralProvider()

        # 30 minutes = 1800 seconds
        cost = provider.estimate_cost(1800)
        assert cost == pytest.approx(0.03, rel=0.01)  # $0.001/min * 30min


def test_voxtral_supports_diarization():
    """Test that Voxtral reports no diarization support."""
    with patch.dict("os.environ", {"MISTRAL_API_KEY": "test-key"}):
        provider = VoxtralProvider()
        assert provider.supports_diarization is False


def test_voxtral_config_validation():
    """Test configuration validation."""
    with patch.dict("os.environ", {"MISTRAL_API_KEY": "test-key"}):
        provider = VoxtralProvider()
        assert provider.validate_config() is True
