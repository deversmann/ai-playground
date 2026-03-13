"""
Short-term memory using deque for conversation context.

This module implements in-memory conversation history using a deque
(double-ended queue) for efficient FIFO management. The memory is:
- Session-scoped (lost on server restart)
- Size-limited (automatic removal of oldest messages)
- Fast (O(1) operations)

The deque automatically removes the oldest messages when the maximum
length is reached, ensuring we don't exceed context window limits.

Example:
    >>> memory = ShortTermMemory(max_messages=3)
    >>> memory.add_message(ChatMessage(role="user", content="Hello"))
    >>> memory.add_message(ChatMessage(role="assistant", content="Hi!"))
    >>> memory.add_message(ChatMessage(role="user", content="How are you?"))
    >>> memory.add_message(ChatMessage(role="assistant", content="Great!"))
    >>> # Only last 3 messages kept (first user message dropped)
    >>> len(memory.get_messages())
    3
"""

from collections import deque
from typing import Deque

from chatbot.providers.models import ChatMessage


class ShortTermMemory:
    """
    Manages conversation history for a single session using a deque.

    This class provides a fixed-size rolling window of recent messages.
    When the maximum size is reached, adding a new message automatically
    removes the oldest message (FIFO - First In, First Out).

    Thread Safety:
        This class is NOT thread-safe. Use MemoryManager for thread-safe
        multi-session management with asyncio.Lock.

    Attributes:
        max_messages: Maximum number of messages to retain
        max_tokens: Approximate maximum tokens (for context window management)
    """

    def __init__(
        self,
        max_messages: int = 50,
        max_tokens: int = 100_000,
    ):
        """
        Initialize short-term memory.

        Args:
            max_messages: Maximum messages to keep (default: 50)
                When this limit is reached, oldest messages are automatically
                removed. This prevents unbounded growth.
            max_tokens: Approximate token limit (default: 100,000)
                This is a soft limit for context window management. We estimate
                ~4 characters per token. Claude Sonnet supports 200k tokens, so
                100k gives us headroom for the response.

        Example:
            >>> # Keep last 20 messages or ~50k tokens
            >>> memory = ShortTermMemory(max_messages=20, max_tokens=50_000)
        """
        self.max_messages = max_messages
        self.max_tokens = max_tokens

        # Deque with maxlen automatically removes oldest when full
        # This is why we use deque instead of a list!
        self._messages: Deque[ChatMessage] = deque(maxlen=max_messages)

    def add_message(self, message: ChatMessage) -> None:
        """
        Add a message to the conversation history.

        If the deque is at max capacity, the oldest message is automatically
        removed before adding the new one.

        Args:
            message: The message to add

        Example:
            >>> memory = ShortTermMemory(max_messages=2)
            >>> memory.add_message(ChatMessage(role="user", content="First"))
            >>> memory.add_message(ChatMessage(role="user", content="Second"))
            >>> memory.add_message(ChatMessage(role="user", content="Third"))
            >>> # "First" was automatically removed
            >>> messages = memory.get_messages()
            >>> len(messages)
            2
            >>> messages[0].content
            'Second'
        """
        self._messages.append(message)

    def get_messages(self) -> list[ChatMessage]:
        """
        Get all messages in the conversation history.

        Returns a copy of the message list to prevent external modification
        of the internal deque.

        Returns:
            List of messages in chronological order (oldest first)

        Example:
            >>> memory = ShortTermMemory()
            >>> memory.add_message(ChatMessage(role="user", content="Hello"))
            >>> messages = memory.get_messages()
            >>> len(messages)
            1
            >>> messages[0].content
            'Hello'
        """
        return list(self._messages)

    def clear(self) -> None:
        """
        Clear all messages from the conversation history.

        Useful for starting a new conversation in the same session.

        Example:
            >>> memory = ShortTermMemory()
            >>> memory.add_message(ChatMessage(role="user", content="Test"))
            >>> len(memory.get_messages())
            1
            >>> memory.clear()
            >>> len(memory.get_messages())
            0
        """
        self._messages.clear()

    def get_message_count(self) -> int:
        """
        Get the number of messages currently stored.

        Returns:
            Number of messages in history

        Example:
            >>> memory = ShortTermMemory()
            >>> memory.get_message_count()
            0
            >>> memory.add_message(ChatMessage(role="user", content="Hi"))
            >>> memory.get_message_count()
            1
        """
        return len(self._messages)

    def estimate_tokens(self) -> int:
        """
        Estimate the total number of tokens in the conversation.

        This is an approximation using the rule: ~4 characters per token.
        Real token counting would require using the model's tokenizer, but
        this approximation is good enough for context window management.

        Returns:
            Estimated token count

        Example:
            >>> memory = ShortTermMemory()
            >>> memory.add_message(ChatMessage(role="user", content="Hi there!"))
            >>> # "Hi there!" = 9 chars ≈ 2-3 tokens
            >>> memory.estimate_tokens()
            2

        Note:
            This is a rough estimate. Different tokenizers split text differently.
            For production use, you'd want to use the actual tokenizer:
            - Anthropic: anthropic.count_tokens()
            - OpenAI: tiktoken library
        """
        total_chars = sum(len(msg.content) for msg in self._messages)
        # Rough estimate: 4 characters per token
        # This is conservative - actual ratios vary by language and content
        return total_chars // 4

    def is_near_token_limit(self, threshold: float = 0.8) -> bool:
        """
        Check if we're approaching the token limit.

        Useful for triggering warnings or automatic summarization.

        Args:
            threshold: Percentage of max_tokens (default: 0.8 = 80%)

        Returns:
            True if estimated tokens exceed threshold percentage of max

        Example:
            >>> memory = ShortTermMemory(max_tokens=100)
            >>> # Add messages totaling ~85 tokens
            >>> memory.is_near_token_limit(threshold=0.8)  # 80% of 100
            True

        Note:
            In Phase 4, we could implement automatic summarization when
            approaching limits, or retrieve only the most relevant context
            from semantic memory.
        """
        estimated = self.estimate_tokens()
        limit = self.max_tokens * threshold
        return estimated >= limit

    def __len__(self) -> int:
        """
        Support len() built-in.

        Example:
            >>> memory = ShortTermMemory()
            >>> len(memory)
            0
            >>> memory.add_message(ChatMessage(role="user", content="Test"))
            >>> len(memory)
            1
        """
        return len(self._messages)

    def __repr__(self) -> str:
        """
        String representation for debugging.

        Example:
            >>> memory = ShortTermMemory(max_messages=10)
            >>> memory.add_message(ChatMessage(role="user", content="Hi"))
            >>> repr(memory)
            'ShortTermMemory(messages=1/10, tokens=~0)'
        """
        return (
            f"ShortTermMemory("
            f"messages={len(self)}/{self.max_messages}, "
            f"tokens=~{self.estimate_tokens()})"
        )
