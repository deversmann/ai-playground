"""
AI provider abstraction layer.

This package provides a unified interface for working with different AI providers
(Anthropic Claude, OpenAI, Ollama, etc.) through a common Protocol.

Main exports:
- AIProvider: The protocol that all providers implement
- ChatMessage, ChatResponse, TokenUsage: Unified data models
- create_provider: Factory function for creating providers
- AnthropicProvider: Anthropic Claude implementation

Example:
    >>> from chatbot.providers import create_provider, ChatMessage
    >>> from chatbot.config import get_settings
    >>>
    >>> settings = get_settings()
    >>> provider = create_provider(settings)
    >>>
    >>> messages = [ChatMessage(role="user", content="Hello!")]
    >>> response = await provider.chat(messages)
    >>> print(response.content)
"""

from .anthropic import AnthropicProvider
from .base import AIProvider, is_provider
from .factory import (
    ProviderConfigurationError,
    ProviderError,
    UnsupportedProviderError,
    create_provider,
)
from .models import ChatMessage, ChatResponse, TokenUsage

__all__ = [
    # Protocol and utilities
    "AIProvider",
    "is_provider",
    # Data models
    "ChatMessage",
    "ChatResponse",
    "TokenUsage",
    # Factory
    "create_provider",
    "ProviderError",
    "ProviderConfigurationError",
    "UnsupportedProviderError",
    # Implementations
    "AnthropicProvider",
]
