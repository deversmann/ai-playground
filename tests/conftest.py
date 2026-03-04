"""
Pytest configuration and fixtures.

This file contains shared test fixtures that can be used across all tests.
Pytest automatically discovers and uses fixtures defined here.

Common fixtures:
- mock_provider: A fake AI provider for testing without API calls
- test_settings: Test configuration
- api_client: FastAPI test client
"""

import pytest
from typing import AsyncIterator

from chatbot.config import Settings
from chatbot.providers import ChatMessage, ChatResponse, TokenUsage


@pytest.fixture
def test_settings() -> Settings:
    """
    Create test settings with safe defaults.

    Returns:
        Settings: Configuration for testing

    Example:
        def test_something(test_settings):
            assert test_settings.provider_type == "anthropic"
    """
    return Settings(
        api_host="127.0.0.1",
        api_port=8888,  # Different port for testing
        api_reload=False,
        provider_type="anthropic",
        anthropic_api_key="test-api-key",
        default_model="claude-3-5-sonnet-20241022",
        default_temperature=0.7,
        default_max_tokens=100,
    )


class MockAIProvider:
    """
    Mock AI provider for testing.

    This fake provider doesn't call any real AI API. Instead, it returns
    predefined responses. Perfect for fast, deterministic tests.

    Example:
        >>> provider = MockAIProvider()
        >>> messages = [ChatMessage(role="user", content="Hello")]
        >>> response = await provider.chat(messages)
        >>> print(response.content)
        "Mock response to: Hello"
    """

    def __init__(self, response_prefix: str = "Mock response"):
        """
        Initialize mock provider.

        Args:
            response_prefix: Prefix for mock responses
        """
        self.response_prefix = response_prefix
        self.call_count = 0

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatResponse:
        """Return a mock chat response."""
        self.call_count += 1

        # Echo the last user message
        user_messages = [m for m in messages if m.role == "user"]
        last_message = user_messages[-1].content if user_messages else "no message"

        return ChatResponse(
            content=f"{self.response_prefix} to: {last_message}",
            model="mock-model",
            usage=TokenUsage(input_tokens=10, output_tokens=20),
            metadata={"mock": True, "call_count": self.call_count},
        )

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Return a mock streaming response."""
        # Just yield the complete response
        response = await self.chat(messages, temperature=temperature, max_tokens=max_tokens)
        yield response.content


@pytest.fixture
def mock_provider() -> MockAIProvider:
    """
    Create a mock AI provider for testing.

    Returns:
        MockAIProvider: Fake provider that returns predictable responses

    Example:
        async def test_chat(mock_provider):
            messages = [ChatMessage(role="user", content="test")]
            response = await mock_provider.chat(messages)
            assert "Mock response" in response.content
    """
    return MockAIProvider()


@pytest.fixture
def sample_messages() -> list[ChatMessage]:
    """
    Create sample chat messages for testing.

    Returns:
        list[ChatMessage]: Sample conversation messages

    Example:
        def test_something(sample_messages):
            assert len(sample_messages) == 2
            assert sample_messages[0].role == "user"
    """
    return [
        ChatMessage(role="user", content="Hello!"),
        ChatMessage(role="assistant", content="Hi! How can I help?"),
        ChatMessage(role="user", content="What is Python?"),
    ]
