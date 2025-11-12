"""
Grok API Client for xAI

This module provides a real implementation of the xAI Grok API client.
Uses OpenAI-compatible API structure for chat completions.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

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
        max_retries: int = 3,
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
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
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
        model: str = "grok-4",
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a chat completion using Grok API.

        Args:
            messages: List of message dictionaries
            model: Model to use (grok-4, grok-beta-3, grok-code-fast-1)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            tools: List of tools for server-side execution (web_search, x_search, etc.)
            tool_choice: Tool choice strategy ("auto", "required", "none", or specific tool)
            response_format: Response format spec (json_object or json_schema)
            **kwargs: Additional parameters

        Returns:
            API response dictionary with usage stats and cached token info
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        # Add tools if provided
        if tools:
            payload["tools"] = tools
            if tool_choice:
                payload["tool_choice"] = tool_choice

        # Add response format if provided (json_object or json_schema)
        if response_format:
            payload["response_format"] = response_format

        # Add any additional parameters
        payload.update(kwargs)

        return await self._make_request("chat/completions", payload)

    async def _make_request(
        self, endpoint: str, payload: Dict[str, Any], retry_count: int = 0
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
                url, json=payload, headers={"Content-Type": "application/json"}
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
                await asyncio.sleep(2**retry_count)  # Exponential backoff
                return await self._make_request(endpoint, payload, retry_count + 1)
            else:
                raise GrokAPIError(f"Request timeout after {self.max_retries} retries: {e}")

        except httpx.ConnectError as e:
            if retry_count < self.max_retries:
                logger.warning(f"Connection error, retrying ({retry_count + 1}/{self.max_retries})")
                await asyncio.sleep(2**retry_count)
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
        cached_tokens: int = 0,
        tool_calls: int = 0,
        model: str = "grok-4",
        return_breakdown: bool = True,
    ) -> Union[Dict[str, float], float]:
        """
        Calculate cost for API usage with caching support.

        Based on xAI pricing as of November 2025:
        - grok-4: $0.003 per 1K input tokens, $0.01 per 1K output tokens
        - grok-beta-3: $0.005 per 1K input tokens, $0.015 per 1K output tokens
        - grok-code-fast-1: $0.001 per 1K input tokens, $0.003 per 1K output tokens
        - Cached tokens: 50% discount on input token cost (May 2025)
        - Tool calls: Currently free (subject to change)

        Args:
            input_tokens: Number of input tokens (non-cached)
            output_tokens: Number of output tokens
            cached_tokens: Number of cached input tokens (50% discount)
            tool_calls: Number of tool calls made
            model: Model used

        Returns:
            Dict with cost breakdown:
            {
                "input_cost": float,
                "output_cost": float,
                "cache_savings": float,
                "tool_cost": float,
                "total": float
            }
        """
        pricing = {
            "grok-4": {"input": 0.003, "output": 0.01},
            "grok-beta-3": {"input": 0.005, "output": 0.015},
            "grok-3": {"input": 0.003, "output": 0.01},
            "grok-code-fast-1": {"input": 0.001, "output": 0.003},
        }

        rates = pricing.get(model, pricing["grok-4"])

        # Calculate regular input cost
        input_cost = (input_tokens / 1000) * rates["input"]

        # Calculate cached input cost (50% discount)
        cached_cost = (cached_tokens / 1000) * rates["input"] * 0.5

        # Calculate savings from caching
        full_cached_cost = (cached_tokens / 1000) * rates["input"]
        cache_savings = full_cached_cost - cached_cost

        # Output cost
        output_cost = (output_tokens / 1000) * rates["output"]

        # Tool cost (currently free, but tracked separately)
        tool_cost = 0.0  # May change in future

        total = input_cost + cached_cost + output_cost + tool_cost

        breakdown = {
            "input_cost": round(input_cost, 6),
            "cached_cost": round(cached_cost, 6),
            "output_cost": round(output_cost, 6),
            "cache_savings": round(cache_savings, 6),
            "tool_cost": round(tool_cost, 6),
            "total": round(total, 6),
        }

        # Backward compatibility: return float if requested
        if not return_breakdown:
            return breakdown["total"]

        return breakdown

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

    # ==============================================================================
    # FILES API (November 2025)
    # ==============================================================================

    async def upload_file(
        self, file_path: Union[str, Path], purpose: str = "assistants"
    ) -> Dict[str, Any]:
        """
        Upload a file to xAI for use with Collections or other features.

        Args:
            file_path: Path to file to upload
            purpose: Purpose of file ("assistants" for Collections)

        Returns:
            File metadata including file_id

        Example response:
            {
                "id": "file-abc123",
                "object": "file",
                "purpose": "assistants",
                "filename": "transcript.txt",
                "bytes": 12345,
                "created_at": 1699564800
            }
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        url = f"{self.base_url}/files"

        # Create multipart form data
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "application/octet-stream")}
            data = {"purpose": purpose}

            # Note: httpx automatically sets Content-Type for multipart
            response = await self.client.post(
                url,
                files=files,
                data=data,
                headers={"Authorization": f"Bearer {self.api_key}"},  # Don't set Content-Type
            )

        if response.status_code == 200:
            return response.json()
        else:
            raise GrokAPIError(f"File upload failed: {response.status_code} - {response.text}")

    async def list_files(self) -> Dict[str, Any]:
        """
        List all uploaded files.

        Returns:
            List of file objects
        """
        url = f"{self.base_url}/files"
        response = await self.client.get(url)

        if response.status_code == 200:
            return response.json()
        else:
            raise GrokAPIError(f"List files failed: {response.status_code} - {response.text}")

    async def retrieve_file(self, file_id: str) -> Dict[str, Any]:
        """
        Retrieve information about a specific file.

        Args:
            file_id: ID of the file

        Returns:
            File metadata
        """
        url = f"{self.base_url}/files/{file_id}"
        response = await self.client.get(url)

        if response.status_code == 200:
            return response.json()
        else:
            raise GrokAPIError(f"Retrieve file failed: {response.status_code} - {response.text}")

    async def delete_file(self, file_id: str) -> Dict[str, Any]:
        """
        Delete a file from xAI storage.

        Args:
            file_id: ID of the file to delete

        Returns:
            Deletion confirmation
        """
        url = f"{self.base_url}/files/{file_id}"
        response = await self.client.delete(url)

        if response.status_code == 200:
            return response.json()
        else:
            raise GrokAPIError(f"Delete file failed: {response.status_code} - {response.text}")

    # ==============================================================================
    # COLLECTIONS API (August 2025)
    # ==============================================================================

    async def create_collection(
        self, name: str, description: str = "", model: str = "grok-4"
    ) -> Dict[str, Any]:
        """
        Create a new collection for knowledge base.

        Args:
            name: Collection name
            description: Optional description
            model: Model to use for embeddings

        Returns:
            Collection metadata including collection_id
        """
        url = f"{self.base_url}/collections"
        payload = {"name": name, "description": description, "model": model}

        response = await self.client.post(url, json=payload)

        if response.status_code == 200:
            return response.json()
        else:
            raise GrokAPIError(
                f"Create collection failed: {response.status_code} - {response.text}"
            )

    async def add_files_to_collection(
        self, collection_id: str, file_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Add files to an existing collection.

        Args:
            collection_id: ID of the collection
            file_ids: List of file IDs to add

        Returns:
            Update confirmation
        """
        url = f"{self.base_url}/collections/{collection_id}/files"
        payload = {"file_ids": file_ids}

        response = await self.client.post(url, json=payload)

        if response.status_code == 200:
            return response.json()
        else:
            raise GrokAPIError(
                f"Add files to collection failed: {response.status_code} - {response.text}"
            )

    async def search_collection(
        self, collection_id: str, query: str, top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Search a collection using semantic search.

        Args:
            collection_id: ID of the collection
            query: Search query
            top_k: Number of results to return

        Returns:
            Search results with relevance scores
        """
        url = f"{self.base_url}/collections/{collection_id}/search"
        payload = {"query": query, "top_k": top_k}

        response = await self.client.post(url, json=payload)

        if response.status_code == 200:
            return response.json()
        else:
            raise GrokAPIError(
                f"Search collection failed: {response.status_code} - {response.text}"
            )

    async def list_collections(self) -> Dict[str, Any]:
        """
        List all collections.

        Returns:
            List of collection objects
        """
        url = f"{self.base_url}/collections"
        response = await self.client.get(url)

        if response.status_code == 200:
            return response.json()
        else:
            raise GrokAPIError(f"List collections failed: {response.status_code} - {response.text}")

    async def delete_collection(self, collection_id: str) -> Dict[str, Any]:
        """
        Delete a collection.

        Args:
            collection_id: ID of the collection to delete

        Returns:
            Deletion confirmation
        """
        url = f"{self.base_url}/collections/{collection_id}"
        response = await self.client.delete(url)

        if response.status_code == 200:
            return response.json()
        else:
            raise GrokAPIError(
                f"Delete collection failed: {response.status_code} - {response.text}"
            )

    # ==============================================================================
    # COST TRACKING WITH CACHING SUPPORT
    # ==============================================================================

    def extract_usage_stats(self, response: Dict[str, Any]) -> Dict[str, int]:
        """
        Extract token usage statistics from API response.

        Args:
            response: API response

        Returns:
            Dict with input_tokens, output_tokens, cached_tokens
        """
        usage = response.get("usage", {})
        return {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "cached_tokens": usage.get("cached_tokens", 0),  # May 2025 feature
            "total_tokens": usage.get("total_tokens", 0),
        }
