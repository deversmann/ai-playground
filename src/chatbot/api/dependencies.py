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
from chatbot.core import ConversationService
from chatbot.memory import MemoryManager
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


@lru_cache()
def get_memory_manager() -> MemoryManager:
    """
    Get the memory manager instance.

    This dependency creates and returns the memory manager for handling
    conversation history across multiple sessions. The @lru_cache decorator
    ensures we only create one instance (singleton pattern).

    Returns:
        MemoryManager: The singleton memory manager instance

    Usage in routes:
        @app.post("/chat")
        async def chat(memory: MemoryManager = Depends(get_memory_manager)):
            messages = await memory.get_messages(session_id)

    Note (Phase 2):
        Currently uses default values (50 messages, 100k tokens). In
        Phase 3+, we might want to configure these via settings:

        settings = get_settings()
        return MemoryManager(
            max_messages=settings.max_messages,
            max_tokens=settings.max_tokens
        )

    Note on Singleton Pattern:
        We use a singleton because:
        1. Memory manager maintains state (all active sessions)
        2. Creating multiple instances would lose session data
        3. Locks wouldn't work across instances
        4. More memory efficient
    """
    # For now, use default configuration
    # TODO Phase 3: Read from settings
    return MemoryManager(
        max_messages=50,
        max_tokens=100_000,
    )


@lru_cache()
def get_conversation_service() -> ConversationService:
    """
    Get the conversation service instance.

    This is the main dependency for chat operations. It combines the
    AI provider and memory manager into a single service that handles
    the full conversation flow.

    Returns:
        ConversationService: The conversation orchestration service

    Usage in routes:
        @app.post("/chat")
        async def chat(
            service: ConversationService = Depends(get_conversation_service)
        ):
            response = await service.send_message(
                session_id="...",
                user_message="..."
            )

    Note on Dependency Injection:
        This function internally calls get_ai_provider() and
        get_memory_manager(), which are both cached. So we're reusing
        the same provider and memory manager instances across all routes.

    Architecture Note:
        This is the "Facade" pattern - the service provides a simple
        interface to complex subsystems (provider + memory). Routes don't
        need to know about memory management or provider details.
    """
    provider = get_ai_provider()
    memory_manager = get_memory_manager()

    return ConversationService(
        provider=provider,
        memory_manager=memory_manager,
    )
