"""
HTTP client for communicating with the AI Chatbot API.

This module handles all HTTP communication with the FastAPI backend.
It provides a clean async interface for the CLI to use.

Example:
    >>> client = APIClient("http://localhost:8000")
    >>> response = await client.send_message("Hello!", "session-123")
    >>> print(response["response"])
"""

import httpx
from typing import Any


class APIClientError(Exception):
    """Raised when API communication fails."""

    pass


class APIClient:
    """
    Async HTTP client for the chatbot API.

    This client handles:
    - Making requests to the API
    - Error handling and retries
    - Response parsing
    - Connection management

    Attributes:
        base_url: The base URL of the API server
        timeout: Request timeout in seconds
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
    ):
        """
        Initialize the API client.

        Args:
            base_url: Base URL of the API server
            timeout: Request timeout in seconds

        Example:
            >>> client = APIClient("http://localhost:8000")
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def health_check(self) -> dict[str, Any]:
        """
        Check if the API server is healthy.

        Returns:
            dict: Health check response

        Raises:
            APIClientError: If health check fails

        Example:
            >>> health = await client.health_check()
            >>> print(health["status"])
            "healthy"
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            raise APIClientError(f"Health check failed: {e}") from e

    async def send_message(
        self,
        message: str,
        session_id: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """
        Send a message to the chatbot and get a response.

        Args:
            message: The user's message
            session_id: Unique session identifier
            temperature: Response randomness (0.0-1.0), optional
            max_tokens: Maximum tokens in response, optional

        Returns:
            dict: API response with AI's reply and metadata

        Raises:
            APIClientError: If the request fails

        Example:
            >>> response = await client.send_message(
            ...     message="What is Python?",
            ...     session_id="user-123",
            ...     temperature=0.7
            ... )
            >>> print(response["response"])
            "Python is a high-level programming language..."
        """
        try:
            # Build request payload
            payload = {
                "message": message,
                "session_id": session_id,
            }

            if temperature is not None:
                payload["temperature"] = temperature

            if max_tokens is not None:
                payload["max_tokens"] = max_tokens

            # Send request
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/send",
                    json=payload,
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            # HTTP error (4xx, 5xx)
            error_detail = "Unknown error"
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", str(e))
            except Exception:
                error_detail = str(e)

            raise APIClientError(
                f"API request failed ({e.response.status_code}): {error_detail}"
            ) from e

        except httpx.HTTPError as e:
            # Network error, timeout, etc.
            raise APIClientError(f"Network error: {e}") from e

    async def get_api_info(self) -> dict[str, Any]:
        """
        Get API information from the root endpoint.

        Returns:
            dict: API information

        Raises:
            APIClientError: If request fails

        Example:
            >>> info = await client.get_api_info()
            >>> print(info["version"])
            "0.4.0"
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/")
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            raise APIClientError(f"Failed to get API info: {e}") from e
