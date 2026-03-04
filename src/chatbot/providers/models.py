"""
Shared data models for AI providers.

These models provide a unified interface across different AI providers
(Anthropic, OpenAI, Ollama, etc.). Each provider converts its specific
API format to/from these standard models.

This abstraction allows the rest of the application to work with any
provider without knowing the implementation details.
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ChatMessage:
    """
    A single message in a conversation.

    This is the unified format used across all providers. Each provider
    is responsible for converting between this format and their specific
    API format.

    Attributes:
        role: Who sent the message ('system', 'user', or 'assistant')
        content: The actual message text

    Example:
        >>> msg = ChatMessage(role="user", content="Hello, AI!")
        >>> print(msg.role, msg.content)
        user Hello, AI!
    """

    role: Literal["system", "user", "assistant"]
    content: str

    def __post_init__(self):
        """Validate the message after initialization."""
        if self.role not in ("system", "user", "assistant"):
            raise ValueError(
                f"Invalid role: {self.role}. Must be 'system', 'user', or 'assistant'"
            )

        if not self.content or not self.content.strip():
            raise ValueError("Message content cannot be empty")


@dataclass
class TokenUsage:
    """
    Token usage statistics for a chat completion.

    Different providers report tokens differently. This provides a
    standardized way to track token usage across all providers.

    Attributes:
        input_tokens: Tokens in the prompt/input
        output_tokens: Tokens in the response/output
        total_tokens: Total tokens used (input + output)

    Example:
        >>> usage = TokenUsage(input_tokens=100, output_tokens=50)
        >>> print(usage.total_tokens)
        150
    """

    input_tokens: int
    output_tokens: int
    total_tokens: int = field(init=False)

    def __post_init__(self):
        """Calculate total tokens after initialization."""
        self.total_tokens = self.input_tokens + self.output_tokens

    @classmethod
    def from_dict(cls, data: dict) -> "TokenUsage":
        """
        Create TokenUsage from a dictionary.

        Handles different provider formats flexibly.

        Args:
            data: Dictionary with 'input_tokens' and 'output_tokens' keys,
                  or alternative key names like 'prompt_tokens', 'completion_tokens'

        Returns:
            TokenUsage instance

        Example:
            >>> usage = TokenUsage.from_dict({
            ...     "input_tokens": 100,
            ...     "output_tokens": 50
            ... })
            >>> print(usage.total_tokens)
            150
        """
        # Handle different provider naming conventions
        input_tokens = data.get("input_tokens") or data.get("prompt_tokens", 0)
        output_tokens = data.get("output_tokens") or data.get("completion_tokens", 0)

        return cls(input_tokens=input_tokens, output_tokens=output_tokens)


@dataclass
class ChatResponse:
    """
    Response from an AI provider.

    This is the unified response format returned by all providers.
    Providers convert their specific response format into this structure.

    Attributes:
        content: The AI's response text
        model: The model that generated the response
        usage: Token usage statistics
        metadata: Provider-specific additional data (response ID, etc.)

    Example:
        >>> response = ChatResponse(
        ...     content="Hello! How can I help?",
        ...     model="claude-3-5-sonnet-20241022",
        ...     usage=TokenUsage(input_tokens=10, output_tokens=6),
        ...     metadata={"id": "msg_123"}
        ... )
        >>> print(response.content)
        Hello! How can I help?
    """

    content: str
    model: str
    usage: TokenUsage
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate the response after initialization."""
        if not self.content:
            raise ValueError("Response content cannot be empty")

        if not self.model:
            raise ValueError("Model name must be provided")

    def to_dict(self) -> dict:
        """
        Convert the response to a dictionary.

        Useful for serialization to JSON for API responses.

        Returns:
            Dictionary representation of the response

        Example:
            >>> response = ChatResponse(
            ...     content="Hi!",
            ...     model="claude",
            ...     usage=TokenUsage(input_tokens=5, output_tokens=2)
            ... )
            >>> response.to_dict()
            {
                'content': 'Hi!',
                'model': 'claude',
                'usage': {'input_tokens': 5, 'output_tokens': 2, 'total_tokens': 7},
                'metadata': {}
            }
        """
        return {
            "content": self.content,
            "model": self.model,
            "usage": {
                "input_tokens": self.usage.input_tokens,
                "output_tokens": self.usage.output_tokens,
                "total_tokens": self.usage.total_tokens,
            },
            "metadata": self.metadata,
        }
