"""
Anthropic Claude provider implementation.

This module implements the AIProvider protocol for Anthropic's Claude API.
It handles:
1. Converting our unified message format to Anthropic's format
2. Calling the Anthropic API
3. Converting Anthropic's response back to our unified format

The provider is completely self-contained and can be swapped with other
providers without affecting the rest of the application.

Example:
    >>> provider = AnthropicProvider(api_key="sk-ant-...")
    >>> messages = [ChatMessage(role="user", content="Hello!")]
    >>> response = await provider.chat(messages)
    >>> print(response.content)
    "Hello! How can I help you today?"
"""

import anthropic
from typing import AsyncIterator

from .base import AIProvider
from .models import ChatMessage, ChatResponse, TokenUsage


class AnthropicProvider:
    """
    Anthropic Claude API provider.

    This class implements the AIProvider protocol for Claude. It automatically
    satisfies the protocol because it has the required async methods with the
    correct signatures - no explicit inheritance needed!

    Attributes:
        client: The async Anthropic API client
        default_model: Default Claude model to use
        default_temperature: Default temperature setting
        default_max_tokens: Default max tokens setting
    """

    def __init__(
        self,
        api_key: str,
        default_model: str = "claude-3-5-sonnet-20241022",
        default_temperature: float = 0.7,
        default_max_tokens: int = 1000,
    ):
        """
        Initialize the Anthropic provider.

        Args:
            api_key: Anthropic API key
            default_model: Default model name (e.g., "claude-3-5-sonnet-20241022")
            default_temperature: Default temperature (0.0-1.0)
            default_max_tokens: Default maximum tokens in response

        Example:
            >>> provider = AnthropicProvider(
            ...     api_key="sk-ant-...",
            ...     default_model="claude-3-5-sonnet-20241022"
            ... )
        """
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.default_model = default_model
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatResponse:
        """
        Generate a complete chat response using Claude.

        This method:
        1. Converts our ChatMessage format to Anthropic's format
        2. Calls the Anthropic API
        3. Converts the response back to our ChatResponse format

        Args:
            messages: List of conversation messages
            temperature: Response randomness (0.0-1.0). Uses default if None.
            max_tokens: Maximum tokens in response. Uses default if None.
            **kwargs: Additional Anthropic-specific parameters (e.g., top_p)

        Returns:
            ChatResponse with Claude's reply

        Raises:
            anthropic.APIError: If the API request fails

        Example:
            >>> messages = [
            ...     ChatMessage(role="user", content="What is Python?")
            ... ]
            >>> response = await provider.chat(messages, temperature=0.5)
            >>> print(response.content)
            "Python is a high-level programming language..."
        """
        # Use defaults if not specified
        temperature = temperature if temperature is not None else self.default_temperature
        max_tokens = max_tokens if max_tokens is not None else self.default_max_tokens

        # Convert our unified format to Anthropic's format
        anthropic_messages, system_message = self._convert_messages_to_anthropic(messages)

        # Call Anthropic API
        # Build API call parameters
        api_params = {
            "model": kwargs.get("model", self.default_model),
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **{k: v for k, v in kwargs.items() if k != "model"},  # Pass other kwargs
        }

        # Only include system parameter if we have a system message
        if system_message:
            api_params["system"] = system_message

        api_response = await self.client.messages.create(**api_params)

        # Convert Anthropic's response to our unified format
        return self._convert_response_from_anthropic(api_response)

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        Generate a streaming chat response using Claude.

        Phase 1: This is a placeholder. Streaming will be implemented in Phase 6.

        For now, this method calls the regular chat() method and yields the
        complete response. In Phase 6, we'll implement true streaming.

        Args:
            messages: List of conversation messages
            temperature: Response randomness (0.0-1.0)
            max_tokens: Maximum tokens in response
            **kwargs: Additional Anthropic-specific parameters

        Yields:
            str: Response chunks (currently just one complete chunk)

        Example:
            >>> messages = [ChatMessage(role="user", content="Hi")]
            >>> async for chunk in provider.stream_chat(messages):
            ...     print(chunk, end="")
            "Hello! How can I help you?"

        Note:
            Phase 6 will implement true streaming using:
            async with self.client.messages.stream(...) as stream:
                async for text in stream.text_stream:
                    yield text
        """
        # Phase 1: Placeholder - just return complete response
        response = await self.chat(
            messages, temperature=temperature, max_tokens=max_tokens, **kwargs
        )
        yield response.content

        # Phase 6: True streaming implementation
        # temperature = temperature if temperature is not None else self.default_temperature
        # max_tokens = max_tokens if max_tokens is not None else self.default_max_tokens
        #
        # anthropic_messages, system_message = self._convert_messages_to_anthropic(messages)
        #
        # async with self.client.messages.stream(
        #     model=kwargs.get("model", self.default_model),
        #     messages=anthropic_messages,
        #     system=system_message,
        #     temperature=temperature,
        #     max_tokens=max_tokens,
        # ) as stream:
        #     async for text in stream.text_stream:
        #         yield text

    def _convert_messages_to_anthropic(
        self, messages: list[ChatMessage]
    ) -> tuple[list[dict], str | None]:
        """
        Convert our unified message format to Anthropic's format.

        Anthropic's API has specific requirements:
        1. System messages must be passed separately (not in messages list)
        2. Only one system message is allowed
        3. Messages must alternate between 'user' and 'assistant'
        4. Messages list must start with 'user' role

        Args:
            messages: Our unified ChatMessage list

        Returns:
            tuple: (anthropic_messages, system_message)
                - anthropic_messages: List of dicts for user/assistant messages
                - system_message: Combined system message or None

        Example:
            >>> messages = [
            ...     ChatMessage(role="system", content="You are helpful"),
            ...     ChatMessage(role="user", content="Hello")
            ... ]
            >>> anthropic_msgs, system = provider._convert_messages_to_anthropic(messages)
            >>> print(system)
            "You are helpful"
            >>> print(anthropic_msgs)
            [{"role": "user", "content": "Hello"}]
        """
        # Separate system messages from user/assistant messages
        system_messages = [msg for msg in messages if msg.role == "system"]
        conversation_messages = [msg for msg in messages if msg.role != "system"]

        # Combine all system messages into one (Anthropic only accepts one)
        system_message = None
        if system_messages:
            system_message = "\n\n".join(msg.content for msg in system_messages)

        # Convert conversation messages to Anthropic format
        anthropic_messages = [
            {"role": msg.role, "content": msg.content} for msg in conversation_messages
        ]

        return anthropic_messages, system_message

    def _convert_response_from_anthropic(
        self, api_response: anthropic.types.Message
    ) -> ChatResponse:
        """
        Convert Anthropic's response to our unified ChatResponse format.

        Anthropic returns a Message object with:
        - content: List of content blocks (we use the first text block)
        - model: The model that generated the response
        - usage: Token usage stats
        - id: Unique message ID

        Args:
            api_response: Raw response from Anthropic API

        Returns:
            ChatResponse: Our unified response format

        Example:
            >>> # api_response from Anthropic
            >>> response = provider._convert_response_from_anthropic(api_response)
            >>> print(response.content)
            "Hello! How can I help?"
            >>> print(response.usage.total_tokens)
            150
        """
        # Extract text content from the first content block
        # Anthropic can return multiple blocks, but for chat we use the first text block
        content = ""
        if api_response.content:
            first_block = api_response.content[0]
            if hasattr(first_block, "text"):
                content = first_block.text

        # Convert token usage
        usage = TokenUsage(
            input_tokens=api_response.usage.input_tokens,
            output_tokens=api_response.usage.output_tokens,
        )

        # Create unified response
        return ChatResponse(
            content=content,
            model=api_response.model,
            usage=usage,
            metadata={
                "id": api_response.id,
                "stop_reason": api_response.stop_reason,
                "role": api_response.role,
            },
        )
