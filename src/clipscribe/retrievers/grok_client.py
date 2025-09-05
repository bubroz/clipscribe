"""
Grok API Client for xAI

This module provides a real implementation of the xAI Grok API client.
Uses OpenAI-compatible API structure for chat completions.
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


class GrokAPIError(Exception):
    """Base exception for Grok API errors."""
    pass


class GrokAuthenticationError(GrokAPIError):
    """Authentication error."""
    pass


class GrokRateLimitError(GrokAPIError):
    """Rate limit exceeded."""
    pass


class GrokAPIClient:
    """
    Real Grok API client using xAI's REST API.

    Compatible with OpenAI SDK structure for easy integration.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.x.ai/v1",
        timeout: int = 60,
        max_retries: int = 3
    ):
        """
        Initialize Grok API client.

        Args:
            api_key: xAI API key
            base_url: Base URL for API calls
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        # HTTP client for connection reuse
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )

        logger.info("Grok API client initialized")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "grok-beta-3",
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a chat completion using Grok API.

        Args:
            messages: List of message dictionaries
            model: Model to use (grok-beta-3, grok-3, grok-code-fast-1)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional parameters

        Returns:
            API response dictionary
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        # Add any additional parameters
        payload.update(kwargs)

        return await self._make_request("chat/completions", payload)

    async def _make_request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Grok API with retry logic.

        Args:
            endpoint: API endpoint
            payload: Request payload
            retry_count: Current retry count

        Returns:
            API response dictionary

        Raises:
            GrokAPIError: For API-related errors
        """
        url = f"{self.base_url}/{endpoint}"

        try:
            logger.debug(f"Making request to {url} with payload: {json.dumps(payload, indent=2)}")

            response = await self.client.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            # Handle different response codes
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise GrokAuthenticationError(f"Authentication failed: {response.text}")
            elif response.status_code == 429:
                raise GrokRateLimitError(f"Rate limit exceeded: {response.text}")
            elif response.status_code == 400:
                raise GrokAPIError(f"Bad request: {response.text}")
            elif response.status_code == 500:
                raise GrokAPIError(f"Server error: {response.text}")
            else:
                raise GrokAPIError(f"Unexpected status {response.status_code}: {response.text}")

        except httpx.TimeoutException as e:
            if retry_count < self.max_retries:
                logger.warning(f"Request timeout, retrying ({retry_count + 1}/{self.max_retries})")
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                return await self._make_request(endpoint, payload, retry_count + 1)
            else:
                raise GrokAPIError(f"Request timeout after {self.max_retries} retries: {e}")

        except httpx.ConnectError as e:
            if retry_count < self.max_retries:
                logger.warning(f"Connection error, retrying ({retry_count + 1}/{self.max_retries})")
                await asyncio.sleep(2 ** retry_count)
                return await self._make_request(endpoint, payload, retry_count + 1)
            else:
                raise GrokAPIError(f"Connection error after {self.max_retries} retries: {e}")

        except Exception as e:
            logger.error(f"Unexpected error in Grok API request: {e}")
            raise GrokAPIError(f"Unexpected error: {e}")

    async def list_models(self) -> Dict[str, Any]:
        """
        List available models.

        Returns:
            Models response
        """
        return await self._make_request("models", {})

    async def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        Get information about a specific model.

        Args:
            model: Model name

        Returns:
            Model information
        """
        return await self._make_request(f"models/{model}", {})

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "grok-beta-3"
    ) -> float:
        """
        Calculate cost for API usage.

        Based on xAI pricing as of September 2025:
        - grok-beta-3: $0.005 per 1K input tokens, $0.015 per 1K output tokens
        - grok-3: $0.003 per 1K input tokens, $0.01 per 1K output tokens
        - grok-code-fast-1: $0.001 per 1K input tokens, $0.003 per 1K output tokens

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model used

        Returns:
            Cost in USD
        """
        pricing = {
            "grok-beta-3": {"input": 0.005, "output": 0.015},
            "grok-3": {"input": 0.003, "output": 0.01},
            "grok-4": {"input": 0.003, "output": 0.01},  # Updated for Grok 4 pricing (July 2025)
            "grok-code-fast-1": {"input": 0.001, "output": 0.003}
        }

        rates = pricing.get(model, pricing["grok-beta-3"])

        input_cost = (input_tokens / 1000) * rates["input"]
        output_cost = (output_tokens / 1000) * rates["output"]

        return round(input_cost + output_cost, 6)

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.

        Rough approximation: ~4 characters per token for English text.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        return len(text) // 4

    async def health_check(self) -> bool:
        """
        Check if the API is accessible and responding.

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            # Try to list models as a health check
            await self.list_models()
            return True
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
