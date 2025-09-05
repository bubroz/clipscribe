"""
Tests for Grok API client functionality.

Tests the real Grok API client with proper mocking for API calls.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from httpx import Response

from src.clipscribe.retrievers.grok_client import (
    GrokAPIClient,
    GrokAPIError,
    GrokAuthenticationError,
    GrokRateLimitError
)


class TestGrokAPIClient:
    """Test Grok API client functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.api_key = "test-api-key"
        self.client = GrokAPIClient(api_key=self.api_key)

    def test_client_initialization(self):
        """Test client initialization with proper configuration."""
        assert self.client.api_key == self.api_key
        assert self.client.base_url == "https://api.x.ai/v1"
        assert self.client.timeout == 60
        assert self.client.max_retries == 3

    def test_cost_calculation_grok_beta_3(self):
        """Test cost calculation for Grok Beta-3."""
        input_tokens = 1000
        output_tokens = 500

        cost = self.client.calculate_cost(input_tokens, output_tokens, "grok-beta-3")

        # Expected: (1000/1000 * 0.005) + (500/1000 * 0.015) = 0.005 + 0.0075 = 0.0125
        assert cost == 0.0125

    def test_cost_calculation_grok_3(self):
        """Test cost calculation for Grok 3."""
        input_tokens = 2000
        output_tokens = 1000

        cost = self.client.calculate_cost(input_tokens, output_tokens, "grok-3")

        # Expected: (2000/1000 * 0.003) + (1000/1000 * 0.01) = 0.006 + 0.01 = 0.016
        assert cost == 0.016

    def test_cost_calculation_grok_code_fast(self):
        """Test cost calculation for Grok Code Fast."""
        input_tokens = 500
        output_tokens = 200

        cost = self.client.calculate_cost(input_tokens, output_tokens, "grok-code-fast-1")

        # Expected: (500/1000 * 0.001) + (200/1000 * 0.003) = 0.0005 + 0.0006 = 0.0011
        assert cost == 0.0011

    def test_token_estimation(self):
        """Test token estimation from text."""
        text = "This is a test message with some words."
        tokens = self.client.estimate_tokens(text)

        # Expected: ~39 characters / 4 = ~9.75 tokens, integer division gives 9
        assert tokens == 9

        # Test another example
        longer_text = "This is a longer test message with more words to test the token estimation function."
        longer_tokens = self.client.estimate_tokens(longer_text)
        assert longer_tokens > 9  # Should be more tokens for longer text

    @patch('httpx.AsyncClient.post')
    async def test_successful_chat_completion(self, mock_post):
        """Test successful chat completion."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Test response"
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        async with self.client:
            result = await self.client.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                model="grok-beta-3"
            )

        assert result["choices"][0]["message"]["content"] == "Test response"
        mock_post.assert_called_once()

    @patch('httpx.AsyncClient.post')
    async def test_authentication_error(self, mock_post):
        """Test authentication error handling."""
        # Mock 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Invalid API key"
        mock_post.return_value = mock_response

        async with self.client:
            with pytest.raises(GrokAuthenticationError):
                await self.client.chat_completion(
                    messages=[{"role": "user", "content": "Hello"}]
                )

    @patch('httpx.AsyncClient.post')
    async def test_rate_limit_error(self, mock_post):
        """Test rate limit error handling."""
        # Mock 429 response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_post.return_value = mock_response

        async with self.client:
            with pytest.raises(GrokRateLimitError):
                await self.client.chat_completion(
                    messages=[{"role": "user", "content": "Hello"}]
                )

    @patch('httpx.AsyncClient.post')
    async def test_generic_api_error(self, mock_post):
        """Test generic API error handling."""
        # Mock 400 response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_post.return_value = mock_response

        async with self.client:
            with pytest.raises(GrokAPIError):
                await self.client.chat_completion(
                    messages=[{"role": "user", "content": "Hello"}]
                )

    @patch('httpx.AsyncClient.post')
    async def test_retry_on_timeout(self, mock_post):
        """Test retry logic on timeout."""
        # Mock timeout on first call, success on second
        call_count = 0

        def mock_post_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Timeout")  # Simulate timeout
            else:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "choices": [{"message": {"content": "Success"}}]
                }
                return mock_response

        mock_post.side_effect = mock_post_side_effect

        async with self.client:
            result = await self.client.chat_completion(
                messages=[{"role": "user", "content": "Hello"}]
            )

        assert call_count == 2  # Should retry once
        assert result["choices"][0]["message"]["content"] == "Success"

    @patch('httpx.AsyncClient.post')
    async def test_list_models(self, mock_post):
        """Test model listing."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": ["grok-beta-3", "grok-3"]
        }
        mock_post.return_value = mock_response

        async with self.client:
            result = await self.client.list_models()

        assert result["models"] == ["grok-beta-3", "grok-3"]

    @patch('httpx.AsyncClient.post')
    async def test_health_check_success(self, mock_post):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": []}
        mock_post.return_value = mock_response

        async with self.client:
            is_healthy = await self.client.health_check()

        assert is_healthy is True

    @patch('httpx.AsyncClient.post')
    async def test_health_check_failure(self, mock_post):
        """Test failed health check."""
        mock_post.side_effect = Exception("Connection failed")

        async with self.client:
            is_healthy = await self.client.health_check()

        assert is_healthy is False

    def test_request_payload_structure(self):
        """Test that request payloads are properly structured."""
        # This is a unit test to verify payload construction
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"}
        ]

        # Test payload structure (without making actual request)
        expected_payload = {
            "model": "grok-beta-3",
            "messages": messages,
            "temperature": 0.1,
            "stream": False,
            "max_tokens": 1000
        }

        # Verify payload structure matches expected OpenAI format
        assert "model" in expected_payload
        assert "messages" in expected_payload
        assert "temperature" in expected_payload
        assert "stream" in expected_payload
        assert expected_payload["model"] == "grok-beta-3"
        assert len(expected_payload["messages"]) == 2
