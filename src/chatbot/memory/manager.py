"""
Memory manager for multi-session conversation tracking.

This module provides thread-safe management of multiple conversation
sessions. Each session has its own ShortTermMemory instance and an
asyncio.Lock for synchronization.

The manager ensures that concurrent requests for the same session don't
interfere with each other, while allowing different sessions to run
in parallel.

Example:
    >>> manager = MemoryManager()
    >>>
    >>> # Two users can chat simultaneously
    >>> await manager.add_message(
    ...     "user-1",
    ...     ChatMessage(role="user", content="Hello")
    ... )
    >>> await manager.add_message(
    ...     "user-2",
    ...     ChatMessage(role="user", content="Hi")
    ... )
    >>>
    >>> # Each session maintains its own conversation
    >>> messages_1 = await manager.get_messages("user-1")
    >>> messages_2 = await manager.get_messages("user-2")
"""

import asyncio
from typing import Dict

from chatbot.providers.models import ChatMessage
from .short_term import ShortTermMemory


class MemoryManager:
    """
    Thread-safe manager for multiple conversation sessions.

    Manages a dictionary of session_id -> ShortTermMemory instances,
    with per-session locking to prevent race conditions when multiple
    async tasks access the same session.

    Thread Safety:
        Each session has its own asyncio.Lock. Only one async task can
        modify a given session at a time, but different sessions can be
        modified in parallel.

    Architecture Note:
        This is a singleton-like service that should be created once and
        injected via FastAPI's dependency injection system.

    Attributes:
        max_messages: Default max messages per session
        max_tokens: Default max tokens per session
    """

    def __init__(
        self,
        max_messages: int = 50,
        max_tokens: int = 100_000,
    ):
        """
        Initialize the memory manager.

        Args:
            max_messages: Default max messages per session (default: 50)
            max_tokens: Default max tokens per session (default: 100,000)

        Example:
            >>> manager = MemoryManager(max_messages=30, max_tokens=50_000)
        """
        self.max_messages = max_messages
        self.max_tokens = max_tokens

        # Dictionary of session_id -> ShortTermMemory
        self._sessions: Dict[str, ShortTermMemory] = {}

        # Dictionary of session_id -> asyncio.Lock
        # One lock per session allows parallel access to different sessions
        self._locks: Dict[str, asyncio.Lock] = {}

        # Dictionary of session_id -> bool (Phase 3.5: track warm starts)
        # True if session was loaded from database after restart
        self._warm_started: Dict[str, bool] = {}

    def _get_or_create_session(self, session_id: str) -> ShortTermMemory:
        """
        Get or create a session's memory.

        This is an internal method. NOT thread-safe - callers must hold
        the session's lock before calling this.

        Args:
            session_id: The session identifier

        Returns:
            ShortTermMemory instance for the session

        Note:
            This method doesn't use async/await because it's purely
            in-memory operations. The locking happens at the higher level
            in the public methods.
        """
        if session_id not in self._sessions:
            # Create new session memory
            self._sessions[session_id] = ShortTermMemory(
                max_messages=self.max_messages,
                max_tokens=self.max_tokens,
            )

        if session_id not in self._locks:
            # Create lock for this session
            self._locks[session_id] = asyncio.Lock()

        return self._sessions[session_id]

    async def add_message(self, session_id: str, message: ChatMessage) -> None:
        """
        Add a message to a session's conversation history.

        Thread-safe: Uses asyncio.Lock to ensure only one task can modify
        a session at a time.

        Args:
            session_id: The session identifier
            message: The message to add

        Example:
            >>> manager = MemoryManager()
            >>> msg = ChatMessage(role="user", content="Hello!")
            >>> await manager.add_message("session-123", msg)

        Note on Locking:
            The pattern we use here is:
            1. Get or create lock for this session
            2. Acquire the lock (blocks if another task holds it)
            3. Safely modify the session
            4. Lock automatically released by 'async with'

            This is the async equivalent of threading.Lock, but for
            asyncio tasks instead of threads.
        """
        # Ensure session and lock exist
        if session_id not in self._locks:
            self._locks[session_id] = asyncio.Lock()

        # Acquire the lock for this session
        # Only one task can be inside this block for a given session_id
        async with self._locks[session_id]:
            session = self._get_or_create_session(session_id)
            session.add_message(message)

    async def get_messages(self, session_id: str) -> list[ChatMessage]:
        """
        Get all messages for a session.

        Thread-safe: Acquires the session lock before reading.

        Args:
            session_id: The session identifier

        Returns:
            List of messages (empty if session doesn't exist)

        Example:
            >>> manager = MemoryManager()
            >>> messages = await manager.get_messages("session-123")
            >>> if not messages:
            ...     print("New session!")

        Note on Read Locking:
            Even though we're just reading, we still acquire the lock.
            This prevents reading while another task is writing, which
            could return inconsistent data (e.g., half-updated conversation).

            In very high-throughput systems, you might use asyncio.RWLock
            (read-write lock) to allow concurrent reads. But for our use
            case, the simple Lock is sufficient and easier to reason about.
        """
        if session_id not in self._locks:
            self._locks[session_id] = asyncio.Lock()

        async with self._locks[session_id]:
            # If session doesn't exist, return empty list
            if session_id not in self._sessions:
                return []

            session = self._sessions[session_id]
            return session.get_messages()

    async def clear_session(self, session_id: str) -> None:
        """
        Clear all messages for a session.

        Keeps the session alive (doesn't delete it), just clears the
        message history. Useful for "start new conversation" feature.

        Args:
            session_id: The session identifier

        Example:
            >>> manager = MemoryManager()
            >>> await manager.add_message("s1", ChatMessage(...))
            >>> await manager.clear_session("s1")
            >>> messages = await manager.get_messages("s1")
            >>> len(messages)
            0
        """
        if session_id not in self._locks:
            self._locks[session_id] = asyncio.Lock()

        async with self._locks[session_id]:
            if session_id in self._sessions:
                self._sessions[session_id].clear()

    async def delete_session(self, session_id: str) -> None:
        """
        Completely delete a session.

        Removes the session from memory, including its lock. Use this
        for cleanup when a user logs out or explicitly deletes their
        conversation history.

        Args:
            session_id: The session identifier

        Example:
            >>> manager = MemoryManager()
            >>> await manager.add_message("s1", ChatMessage(...))
            >>> await manager.delete_session("s1")
            >>> # Session is completely gone, not just cleared

        Note:
            This is different from clear_session():
            - clear_session(): Empties messages, keeps session alive
            - delete_session(): Removes session entirely from memory
        """
        # Need to acquire lock before deleting to ensure no other
        # task is currently using this session
        if session_id in self._locks:
            async with self._locks[session_id]:
                # Remove session and its lock
                self._sessions.pop(session_id, None)
                # We remove the lock AFTER exiting the context manager
                # to avoid issues with the lock being deleted while held
            # Now safe to remove the lock
            self._locks.pop(session_id, None)
            # Also remove warm_started flag
            self._warm_started.pop(session_id, None)

    async def mark_warm_started(self, session_id: str) -> None:
        """
        Mark a session as having been warm started from database.

        Phase 3.5 feature: Track which sessions were loaded from database
        after server restart for observability.

        Args:
            session_id: The session identifier

        Example:
            >>> manager = MemoryManager()
            >>> await manager.mark_warm_started("session-123")
            >>> stats = await manager.get_session_stats("session-123")
            >>> print(stats["warm_started"])
            True
        """
        self._warm_started[session_id] = True

    async def get_session_stats(self, session_id: str) -> dict:
        """
        Get statistics for a session.

        Returns message count and estimated token usage. Useful for
        displaying to users or monitoring context window usage.

        Args:
            session_id: The session identifier

        Returns:
            Dictionary with 'message_count', 'estimated_tokens', and
            'near_limit' keys

        Example:
            >>> manager = MemoryManager()
            >>> stats = await manager.get_session_stats("session-123")
            >>> print(stats)
            {
                'message_count': 15,
                'estimated_tokens': 3200,
                'near_limit': False
            }

        Note:
            In a real production system, you might want to track:
            - Total tokens used (for billing)
            - Session creation time
            - Last activity timestamp
            - Number of turns (user/assistant pairs)
        """
        if session_id not in self._locks:
            self._locks[session_id] = asyncio.Lock()

        async with self._locks[session_id]:
            if session_id not in self._sessions:
                return {
                    "message_count": 0,
                    "estimated_tokens": 0,
                    "near_limit": False,
                    "warm_started": False,  # Phase 3.5
                }

            session = self._sessions[session_id]
            return {
                "message_count": session.get_message_count(),
                "estimated_tokens": session.estimate_tokens(),
                "near_limit": session.is_near_token_limit(),
                "warm_started": self._warm_started.get(session_id, False),  # Phase 3.5
            }

    async def list_sessions(self) -> list[str]:
        """
        List all active session IDs.

        Useful for admin interfaces or debugging.

        Returns:
            List of session IDs

        Example:
            >>> manager = MemoryManager()
            >>> await manager.add_message("s1", ChatMessage(...))
            >>> await manager.add_message("s2", ChatMessage(...))
            >>> sessions = await manager.list_sessions()
            >>> sessions
            ['s1', 's2']
        """
        # No locking needed - we're just reading the keys
        # Even if sessions are being added/removed, getting a snapshot
        # of current keys is atomic in Python
        return list(self._sessions.keys())

    async def get_total_sessions(self) -> int:
        """
        Get the total number of active sessions.

        Returns:
            Number of active sessions

        Example:
            >>> manager = MemoryManager()
            >>> count = await manager.get_total_sessions()
            >>> print(f"Managing {count} conversations")
        """
        return len(self._sessions)

    def __repr__(self) -> str:
        """
        String representation for debugging.

        Example:
            >>> manager = MemoryManager()
            >>> repr(manager)
            'MemoryManager(sessions=0)'
        """
        return f"MemoryManager(sessions={len(self._sessions)})"
