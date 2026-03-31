"""
Conversation service - orchestrates memory and AI provider.

This module provides the main business logic for chat operations,
coordinating between the memory system (conversation context) and
the AI provider (API calls).

The ConversationService is the primary entry point for all chat
operations in the application. It handles:
- Retrieving conversation history
- Adding user messages to context
- Calling the AI with full conversation
- Storing AI responses in memory

Example:
    >>> service = ConversationService(provider, memory_manager)
    >>> response = await service.send_message(
    ...     session_id="user-123",
    ...     user_message="What is async/await?",
    ...     temperature=0.7
    ... )
    >>> print(response.content)
"""

from typing import Optional

from chatbot.memory import MemoryManager
from chatbot.providers import AIProvider, ChatMessage, ChatResponse

# Conditional import - Phase 3+
# Repository is optional for backward compatibility with Phase 2
try:
    from chatbot.storage import ConversationRepository
except ImportError:
    ConversationRepository = None  # type: ignore


class ConversationService:
    """
    Orchestrates conversation flow between memory and AI provider.

    This is the core business logic layer that:
    1. Maintains conversation context via MemoryManager
    2. Communicates with AI provider (Anthropic, OpenAI, etc.)
    3. Ensures messages are saved to memory

    The service provides a clean interface for the API layer, hiding
    the complexity of memory management and provider communication.

    Architecture Note:
        This follows the "Facade" pattern - it provides a simplified
        interface to the complex subsystems (memory + provider).

    Attributes:
        provider: The AI provider to use for generating responses
        memory_manager: Manages conversation history across sessions
    """

    def __init__(
        self,
        provider: AIProvider,
        memory_manager: MemoryManager,
    ):
        """
        Initialize the conversation service.

        Args:
            provider: AI provider instance (Anthropic, OpenAI, etc.)
            memory_manager: Memory manager for conversation history

        Example:
            >>> from chatbot.providers import AnthropicProvider
            >>> from chatbot.memory import MemoryManager
            >>>
            >>> provider = AnthropicProvider(api_key="...")
            >>> memory = MemoryManager()
            >>> service = ConversationService(provider, memory)
        """
        self.provider = provider
        self.memory_manager = memory_manager

    async def _warm_start_session(
        self,
        session_id: str,
        repository: "ConversationRepository",
    ) -> int:
        """
        Load recent messages from database to RAM after server restart.

        This "warm start" ensures conversation context is available even after
        the server restarts and RAM is cleared. Only loads the most recent N
        messages to respect memory limits.

        Phase 3.5 Feature: Completes the persistence loop by reading from
        database when RAM is empty.

        Args:
            session_id: The session identifier
            repository: Database repository to load messages from

        Returns:
            int: Number of messages loaded from database

        Example:
            >>> # After server restart, RAM is empty
            >>> count = await service._warm_start_session("session-123", repo)
            >>> # RAM now has recent 50 messages from database
            >>> print(f"Loaded {count} messages")
            Loaded 35 messages

        Note:
            - Only loads up to max_messages (default: 50)
            - Loads in chronological order (oldest to newest)
            - Respects existing deque behavior
            - Called automatically by send_message() when needed
        """
        # Get recent messages from database
        # Limit to max_messages to respect RAM constraints
        # Use get_recent_messages to get MOST RECENT N (not oldest N)
        db_messages = await repository.get_recent_messages_as_chat_messages(
            session_id,
            limit=self.memory_manager.max_messages,
        )

        # Load into RAM in chronological order
        # MemoryManager.add_message() maintains order via deque
        for msg in db_messages:
            await self.memory_manager.add_message(session_id, msg)

        # Mark session as warm started for observability
        if len(db_messages) > 0:
            await self.memory_manager.mark_warm_started(session_id)

        return len(db_messages)

    async def send_message(
        self,
        session_id: str,
        user_message: str,
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        repository: Optional["ConversationRepository"] = None,
    ) -> ChatResponse:
        """
        Send a message and get a response with full conversation context.

        This is the main method for chat operations. It:
        1. Retrieves conversation history for the session
        2. Adds system prompt (if provided)
        3. Adds the user's new message
        4. Sends full conversation to AI provider
        5. Stores the AI's response in memory
        6. Persists to database (if repository provided - Phase 3+)
        7. Returns the response

        Args:
            session_id: Unique identifier for this conversation
            user_message: The user's message text
            temperature: Response randomness (0.0-1.0), None uses provider default
            max_tokens: Max response tokens, None uses provider default
            system_prompt: Optional system instructions for the AI
            repository: Optional ConversationRepository for persistence (Phase 3+)

        Returns:
            ChatResponse from the AI provider

        Raises:
            Exception: If AI provider fails (network, auth, rate limit, etc.)

        Example:
            >>> # Phase 2: In-memory only
            >>> response = await service.send_message(
            ...     session_id="user-123-conv-1",
            ...     user_message="Explain async/await in Python",
            ...     temperature=0.7,
            ... )
            >>>
            >>> # Phase 3: With database persistence
            >>> response = await service.send_message(
            ...     session_id="user-123-conv-1",
            ...     user_message="Explain async/await in Python",
            ...     repository=conversation_repo,  # Persists to database
            ... )

        Note on Two-Tier Memory (Phase 3+):
            When a repository is provided, messages are stored in both:
            - RAM (MemoryManager): Fast, recent messages for context
            - Database (Repository): Permanent, all messages for history

            This hybrid approach provides:
            - Speed: In-memory access for active conversations
            - Persistence: Survives server restarts
            - Scalability: Can offload old messages from RAM

        Note on System Prompts:
            System prompts are NOT stored in conversation history. They're
            included with each request but don't count as conversation messages.
            This is intentional - system prompts are instructions, not conversation.
        """
        # 1. Get conversation history for this session
        history = await self.memory_manager.get_messages(session_id)

        # Phase 3.5: Warm start if RAM empty but database has messages
        if not history and repository:
            # RAM is empty - check if database has messages to load
            loaded_count = await self._warm_start_session(session_id, repository)
            if loaded_count > 0:
                # Warm start successful - reload history from RAM
                history = await self.memory_manager.get_messages(session_id)
                # Log warm start for observability
                print(f"🔥 Warm start: loaded {loaded_count} messages for session {session_id}")

        # 2. Build the full message list for the AI
        messages: list[ChatMessage] = []

        # Add system prompt if provided (goes first, not stored in history)
        if system_prompt:
            messages.append(
                ChatMessage(
                    role="system",
                    content=system_prompt,
                )
            )

        # Add conversation history
        messages.extend(history)

        # Add the new user message
        user_msg = ChatMessage(
            role="user",
            content=user_message,
        )
        messages.append(user_msg)

        # 3. Call the AI provider with full conversation
        ai_response = await self.provider.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # 4. Store the user message in memory (RAM - fast)
        await self.memory_manager.add_message(session_id, user_msg)

        # 5. Store the AI response in memory (RAM - fast)
        assistant_msg = ChatMessage(
            role="assistant",
            content=ai_response.content,
        )
        await self.memory_manager.add_message(session_id, assistant_msg)

        # 6. Persist to database (Phase 3+) - permanent storage
        if repository is not None:
            # Save user message to database
            await repository.add_message(
                session_id=session_id,
                role=user_msg.role,
                content=user_msg.content,
            )

            # Save AI response to database
            await repository.add_message(
                session_id=session_id,
                role=assistant_msg.role,
                content=assistant_msg.content,
            )
            # Note: Repository commits happen automatically via FastAPI's
            # database session dependency (async context manager)

        # 7. Return the response
        return ai_response

    async def get_conversation_history(
        self,
        session_id: str,
    ) -> list[ChatMessage]:
        """
        Get the conversation history for a session.

        Useful for displaying conversation to the user or debugging.

        Args:
            session_id: The session identifier

        Returns:
            List of messages in chronological order

        Example:
            >>> history = await service.get_conversation_history("session-123")
            >>> for msg in history:
            ...     print(f"{msg.role}: {msg.content}")
            user: Hello!
            assistant: Hi! How can I help you?
            user: What's the weather?
            assistant: I don't have access to weather data...
        """
        return await self.memory_manager.get_messages(session_id)

    async def clear_conversation(self, session_id: str) -> None:
        """
        Clear conversation history for a session.

        Useful for "start new conversation" feature. The session remains
        active but message history is cleared.

        Args:
            session_id: The session identifier

        Example:
            >>> await service.clear_conversation("session-123")
            >>> history = await service.get_conversation_history("session-123")
            >>> len(history)
            0
        """
        await self.memory_manager.clear_session(session_id)

    async def delete_conversation(self, session_id: str) -> None:
        """
        Completely delete a conversation session.

        Unlike clear_conversation(), this removes the session entirely
        from memory. Use this for user logout or explicit deletion.

        Args:
            session_id: The session identifier

        Example:
            >>> await service.delete_conversation("session-123")
            >>> # Session is completely removed from memory
        """
        await self.memory_manager.delete_session(session_id)

    async def get_conversation_stats(self, session_id: str) -> dict:
        """
        Get statistics about a conversation.

        Returns message count, token usage, and context window status.

        Args:
            session_id: The session identifier

        Returns:
            Dictionary with conversation statistics

        Example:
            >>> stats = await service.get_conversation_stats("session-123")
            >>> print(stats)
            {
                'message_count': 20,
                'estimated_tokens': 5400,
                'near_limit': False
            }

        Note:
            This is useful for:
            - Displaying stats to users
            - Monitoring context window usage
            - Triggering warnings when approaching limits
            - Analytics and usage tracking
        """
        return await self.memory_manager.get_session_stats(session_id)

    async def list_active_sessions(self) -> list[str]:
        """
        List all active conversation sessions.

        Useful for admin interfaces, debugging, or "continue conversation"
        features.

        Returns:
            List of active session IDs

        Example:
            >>> sessions = await service.list_active_sessions()
            >>> print(f"Managing {len(sessions)} conversations")

        Note:
            In Phase 3, when we add database storage, this would query
            the database instead of just in-memory sessions. You'd be
            able to see all historical sessions, not just active ones.
        """
        return await self.memory_manager.list_sessions()

    def __repr__(self) -> str:
        """
        String representation for debugging.

        Example:
            >>> service = ConversationService(provider, memory)
            >>> repr(service)
            'ConversationService(provider=AnthropicProvider, sessions=5)'
        """
        provider_name = type(self.provider).__name__
        session_count = len(self.memory_manager._sessions)
        return f"ConversationService(provider={provider_name}, sessions={session_count})"
