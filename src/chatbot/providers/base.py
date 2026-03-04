"""
Base protocol for AI providers.

This module defines the interface that all AI providers must implement.
Using Python's Protocol (structural typing), any class that implements
these methods automatically satisfies the interface - no explicit
inheritance required.

This design allows us to:
1. Easily swap between different AI providers (Anthropic, OpenAI, Ollama)
2. Add new providers without modifying existing code
3. Type-check provider usage at development time
4. Keep provider implementations independent and decoupled

Example:
    Any class with these async methods is a valid AIProvider:

    class MyProvider:
        async def chat(...) -> ChatResponse: ...
        async def stream_chat(...) -> AsyncIterator[str]: ...

    No need to inherit from AIProvider or explicitly implement it!
"""

from typing import AsyncIterator, Protocol

from .models import ChatMessage, ChatResponse


class AIProvider(Protocol):
    """
    Protocol defining the interface for AI providers.

    Any class implementing these methods can be used as an AI provider,
    regardless of its implementation details. This is structural typing
    (duck typing with type checking).

    All methods must be async to support non-blocking I/O.
    """

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatResponse:
        """
        Generate a complete chat response.

        This method sends messages to the AI and waits for a complete response.
        Use this for simple request/response interactions.

        Args:
            messages: List of conversation messages in order
            temperature: Response randomness (0.0-1.0). None uses provider default.
            max_tokens: Maximum tokens in response. None uses provider default.
            **kwargs: Provider-specific additional parameters

        Returns:
            ChatResponse containing the AI's reply and metadata

        Raises:
            Exception: Provider-specific errors (network, auth, rate limit, etc.)

        Example:
            >>> messages = [
            ...     ChatMessage(role="user", content="What is 2+2?")
            ... ]
            >>> response = await provider.chat(messages, temperature=0.0)
            >>> print(response.content)
            "2 + 2 equals 4"

        Note:
            This is a blocking operation (from the perspective of this coroutine).
            It waits for the complete response before returning.
        """
        ...

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        Generate a streaming chat response.

        This method returns an async iterator that yields response chunks
        as they're generated. Use this for real-time streaming in UIs.

        Args:
            messages: List of conversation messages in order
            temperature: Response randomness (0.0-1.0). None uses provider default.
            max_tokens: Maximum tokens in response. None uses provider default.
            **kwargs: Provider-specific additional parameters

        Yields:
            str: Individual chunks of the response as they're generated

        Raises:
            Exception: Provider-specific errors (network, auth, rate limit, etc.)

        Example:
            >>> messages = [
            ...     ChatMessage(role="user", content="Tell me a story")
            ... ]
            >>> async for chunk in provider.stream_chat(messages):
            ...     print(chunk, end="", flush=True)
            "Once upon a time... there was... a chatbot..."

        Note:
            The chunks are raw text pieces, not complete words or sentences.
            The caller is responsible for concatenating them if needed.

        Note (Phase 6):
            In Phase 1, we won't implement streaming. This method will be
            added in Phase 6 when we add advanced features.
        """
        ...


def is_provider(obj: object) -> bool:
    """
    Check if an object implements the AIProvider protocol.

    This is a runtime check useful for validation and debugging.
    Type checkers (mypy, pyright) will check this at compile time.

    Args:
        obj: The object to check

    Returns:
        bool: True if object implements AIProvider protocol

    Example:
        >>> provider = AnthropicProvider(api_key="...")
        >>> is_provider(provider)
        True
        >>> is_provider("not a provider")
        False

    Note:
        This checks for the presence of required methods, not their signatures.
        For full type safety, rely on static type checkers.
    """
    return (
        hasattr(obj, "chat")
        and callable(obj.chat)
        and hasattr(obj, "stream_chat")
        and callable(obj.stream_chat)
    )
