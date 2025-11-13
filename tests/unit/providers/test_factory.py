"""Unit tests for provider factory."""

import pytest
from clipscribe.providers.factory import get_transcription_provider, get_intelligence_provider
from clipscribe.providers.base import ConfigurationError


def test_get_valid_transcription_provider():
    """Test getting valid transcription providers."""
    from unittest.mock import patch
    
    with patch.dict("os.environ", {"MISTRAL_API_KEY": "test-key"}):
        provider = get_transcription_provider("voxtral")
        assert provider.name == "voxtral"


def test_get_invalid_transcription_provider():
    """Test that invalid provider name raises ValueError."""
    with pytest.raises(ValueError, match="Unknown transcription provider"):
        get_transcription_provider("invalid-provider")


def test_get_valid_intelligence_provider():
    """Test getting valid intelligence provider."""
    from unittest.mock import patch
    
    with patch.dict("os.environ", {"XAI_API_KEY": "test-key"}):
        provider = get_intelligence_provider("grok")
        assert provider.name == "grok"


def test_get_invalid_intelligence_provider():
    """Test that invalid provider name raises ValueError."""
    with pytest.raises(ValueError, match="Unknown intelligence provider"):
        get_intelligence_provider("invalid-provider")


def test_provider_validation_failure():
    """Test that provider with invalid config raises ConfigurationError."""
    from unittest.mock import patch
    
    # Missing API key should raise ConfigurationError
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ConfigurationError):
            get_transcription_provider("voxtral")

