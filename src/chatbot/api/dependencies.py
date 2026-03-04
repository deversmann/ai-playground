"""
FastAPI dependency injection.

Dependencies are functions that FastAPI calls automatically to provide
resources to route handlers. This pattern:
1. Keeps routes clean and focused
2. Makes testing easy (mock dependencies)
3. Centralizes resource management
4. Enables reuse across routes

Example:
    @app.post("/chat")
    async def chat(
        request: ChatRequest,
        provider: AIProvider = Depends(get_ai_provider)  # Injected!
    ):
        # provider is automatically created and passed in
        response = await provider.chat(...)
"""

from functools import lru_cache

from chatbot.config import Settings, get_settings
from chatbot.providers import AIProvider, create_provider


@lru_cache()
def get_ai_provider() -> AIProvider:
    """
    Get the configured AI provider instance.

    This dependency creates and returns the appropriate AI provider based
    on the application settings. The @lru_cache decorator ensures we only
    create one provider instance and reuse it.

    Returns:
        AIProvider: The configured provider (e.g., AnthropicProvider)

    Raises:
        ProviderConfigurationError: If provider configuration is invalid

    Usage in routes:
        @app.post("/chat")
        async def chat(provider: AIProvider = Depends(get_ai_provider)):
            response = await provider.chat(...)

    Note:
        For production, you might want to use a more sophisticated caching
        strategy, especially if you need to refresh credentials or handle
        multiple users with different providers.

    Note (Phase 2+):
        When we add dependency injection for other services (memory manager,
        database session, etc.), they'll follow this same pattern.
    """
    settings = get_settings()
    return create_provider(settings)


def get_current_settings() -> Settings:
    """
    Get the current application settings.

    This dependency provides access to settings in route handlers.
    Useful for reading configuration values or passing settings to
    other components.

    Returns:
        Settings: Application settings

    Usage in routes:
        @app.get("/info")
        async def info(settings: Settings = Depends(get_current_settings)):
            return {"model": settings.default_model}

    Note:
        This uses get_settings() which is already cached, so it's
        efficient to call multiple times.
    """
    return get_settings()
