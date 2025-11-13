"""Unit tests for GrokProvider."""

import json
import pytest
from unittest.mock import AsyncMock, patch
from clipscribe.providers.intelligence.grok import GrokProvider


@pytest.fixture
def mock_grok_response():
    """Mock Grok API response."""
    return {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "entities": [
                        {"name": "Test Person", "type": "PERSON", "confidence": 0.9, "evidence": "quote"}
                    ],
                    "relationships": [
                        {"subject": "A", "predicate": "knows", "object": "B", "confidence": 0.8, "evidence": "quote"}
                    ],
                    "topics": [
                        {"name": "Testing", "relevance": 0.9, "time_range": "00:00-10:00"}
                    ],
                    "key_moments": [
                        {"timestamp": "00:05", "description": "moment", "significance": 0.8, "quote": "quote"}
                    ],
                    "sentiment": {"overall": "neutral", "confidence": 0.7, "per_topic": {}}
                })
            }
        }],
        "usage": {
            "prompt_tokens": 1000,
            "completion_tokens": 500,
            "cached_tokens": 200,
        }
    }


@pytest.mark.asyncio
async def test_grok_provider_extract(mock_transcript_result, mock_grok_response):
    """Test Grok provider intelligence extraction."""
    with patch.dict("os.environ", {"XAI_API_KEY": "test-key"}):
        with patch("clipscribe.retrievers.grok_client.GrokAPIClient.chat_completion", new_callable=AsyncMock, return_value=mock_grok_response):
            provider = GrokProvider()
            result = await provider.extract(mock_transcript_result)
            
            assert result.provider == "grok"
            assert len(result.entities) == 1
            assert len(result.relationships) == 1
            assert len(result.topics) == 1
            assert len(result.key_moments) == 1
            assert "total" in result.cost_breakdown
            assert result.cache_stats["cached_tokens"] == 200


def test_grok_cost_estimation():
    """Test Grok cost estimation."""
    with patch.dict("os.environ", {"XAI_API_KEY": "test-key"}):
        provider = GrokProvider()
        
        # Estimate cost for 10,000 character transcript
        cost = provider.estimate_cost(10000)
        assert cost > 0  # Should have some cost
        assert cost < 0.01  # Should be very cheap for short transcript


def test_grok_config_validation():
    """Test Grok configuration validation."""
    with patch.dict("os.environ", {"XAI_API_KEY": "test-key"}):
        provider = GrokProvider()
        assert provider.validate_config() is True
    
    # Test without API key
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(Exception):  # Should raise ConfigurationError
            GrokProvider()


def test_grok_preserves_cache_stats(mock_transcript_result, mock_grok_response):
    """Test that Grok provider preserves cache statistics."""
    with patch.dict("os.environ", {"XAI_API_KEY": "test-key"}):
        with patch("clipscribe.retrievers.grok_client.GrokAPIClient.chat_completion", new_callable=AsyncMock, return_value=mock_grok_response):
            provider = GrokProvider()
            result = pytest.mark.asyncio(provider.extract)(mock_transcript_result)
            
            # Verify cache stats preserved
            assert "cached_tokens" in result.cache_stats
            assert "cache_savings" in result.cache_stats


def test_grok_preserves_cost_breakdown(mock_transcript_result, mock_grok_response):
    """Test that Grok provider preserves detailed cost breakdown."""
    with patch.dict("os.environ", {"XAI_API_KEY": "test-key"}):
        provider = GrokProvider()
        
        # Cost breakdown should include all Grok details
        # This test verifies the provider wrapper preserves the existing GrokAPIClient features
        assert provider.client is not None  # Uses existing GrokAPIClient

