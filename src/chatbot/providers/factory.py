"""
Factory for creating AI provider instances.

The Factory Pattern centralizes provider creation logic. Instead of
creating providers directly throughout the code, we use this factory
to create the appropriate provider based on configuration.

Benefits:
1. Single source of truth for provider creation
2. Easy to swap providers via configuration
3. Consistent initialization across the application
4. Easier testing (mock the factory)

Example:
    >>> from chatbot.config import get_settings
    >>> settings = get_settings()
    >>> provider = create_provider(settings)
    >>> # Returns AnthropicProvider, OpenAIProvider, or OllamaProvider
    >>> # based on settings.provider_type
"""

from typing import TYPE_CHECKING

from chatbot.config import Settings

if TYPE_CHECKING:
    # Import for type checking only (avoids circular imports)
    from .base import AIProvider


class ProviderError(Exception):
    """Raised when provider creation or operation fails."""

    pass


class UnsupportedProviderError(ProviderError):
    """Raised when requesting an unsupported provider type."""

    pass


class ProviderConfigurationError(ProviderError):
    """Raised when provider configuration is invalid or incomplete."""

    pass


def create_provider(settings: Settings) -> "AIProvider":
    """
    Create an AI provider based on configuration.

    This is the main entry point for getting a provider instance.
    It reads the provider type from settings and creates the appropriate
    provider with the necessary credentials.

    Args:
        settings: Application settings containing provider configuration

    Returns:
        AIProvider: The configured provider instance

    Raises:
        UnsupportedProviderError: If provider_type is not recognized
        ProviderConfigurationError: If required configuration is missing

    Example:
        >>> from chatbot.config import get_settings
        >>> settings = get_settings()
        >>> provider = create_provider(settings)
        >>> messages = [ChatMessage(role="user", content="Hello")]
        >>> response = await provider.chat(messages)

    Note:
        The provider is created fresh each time. For long-lived providers,
        consider caching the instance (we'll do this in FastAPI dependencies).
    """
    provider_type = settings.provider_type.lower()

    if provider_type == "anthropic":
        return _create_anthropic_provider(settings)

    elif provider_type == "openai":
        # Phase 5: OpenAI implementation
        raise UnsupportedProviderError(
            "OpenAI provider not yet implemented (coming in Phase 5)"
        )

    elif provider_type == "ollama":
        # Phase 5: Ollama implementation
        raise UnsupportedProviderError(
            "Ollama provider not yet implemented (coming in Phase 5)"
        )

    else:
        raise UnsupportedProviderError(
            f"Unknown provider type: '{provider_type}'. "
            f"Supported types: anthropic (Phase 1), openai (Phase 5), ollama (Phase 5)"
        )


def _create_anthropic_provider(settings: Settings) -> "AIProvider":
    """
    Create and configure an Anthropic Claude provider.

    Args:
        settings: Application settings with Anthropic configuration

    Returns:
        AnthropicProvider: Configured Anthropic provider

    Raises:
        ProviderConfigurationError: If Anthropic API key is missing

    Note:
        This is an internal helper. Use create_provider() instead.
    """
    # Import here to avoid circular imports and unnecessary dependencies
    from .anthropic import AnthropicProvider

    if not settings.anthropic_api_key:
        raise ProviderConfigurationError(
            "Anthropic API key is required. Set ANTHROPIC_API_KEY in your .env file."
        )

    return AnthropicProvider(
        api_key=settings.anthropic_api_key,
        default_model=settings.default_model,
        default_temperature=settings.default_temperature,
        default_max_tokens=settings.default_max_tokens,
    )


def _create_openai_provider(settings: Settings) -> "AIProvider":
    """
    Create and configure an OpenAI provider.

    Args:
        settings: Application settings with OpenAI configuration

    Returns:
        OpenAIProvider: Configured OpenAI provider

    Raises:
        ProviderConfigurationError: If OpenAI API key is missing

    Note:
        Phase 5: This will be implemented when we add OpenAI support.
        For now, it raises UnsupportedProviderError.
    """
    raise UnsupportedProviderError("OpenAI provider not yet implemented")


def _create_ollama_provider(settings: Settings) -> "AIProvider":
    """
    Create and configure an Ollama provider.

    Args:
        settings: Application settings with Ollama configuration

    Returns:
        OllamaProvider: Configured Ollama provider

    Note:
        Phase 5: This will be implemented when we add local model support.
        For now, it raises UnsupportedProviderError.
    """
    raise UnsupportedProviderError("Ollama provider not yet implemented")
