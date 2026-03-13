"""
Unit tests for memory system.

Tests for ShortTermMemory and MemoryManager components.
"""

import pytest

from chatbot.memory import MemoryManager, ShortTermMemory
from chatbot.providers.models import ChatMessage


class TestShortTermMemory:
    """Tests for ShortTermMemory class."""

    def test_initialization(self):
        """Test creating a ShortTermMemory instance."""
        memory = ShortTermMemory(max_messages=10, max_tokens=1000)
        assert memory.max_messages == 10
        assert memory.max_tokens == 1000
        assert len(memory) == 0

    def test_add_message(self):
        """Test adding messages to memory."""
        memory = ShortTermMemory()
        msg = ChatMessage(role="user", content="Hello")

        memory.add_message(msg)

        assert len(memory) == 1
        messages = memory.get_messages()
        assert len(messages) == 1
        assert messages[0].content == "Hello"

    def test_max_messages_limit(self):
        """Test that deque automatically removes oldest messages."""
        memory = ShortTermMemory(max_messages=3)

        # Add 4 messages
        memory.add_message(ChatMessage(role="user", content="First"))
        memory.add_message(ChatMessage(role="assistant", content="Response 1"))
        memory.add_message(ChatMessage(role="user", content="Second"))
        memory.add_message(ChatMessage(role="assistant", content="Response 2"))

        # Should only have last 3 messages
        messages = memory.get_messages()
        assert len(messages) == 3
        assert messages[0].content == "Response 1"  # First message dropped
        assert messages[1].content == "Second"
        assert messages[2].content == "Response 2"

    def test_clear(self):
        """Test clearing all messages."""
        memory = ShortTermMemory()
        memory.add_message(ChatMessage(role="user", content="Test"))

        assert len(memory) == 1

        memory.clear()

        assert len(memory) == 0
        assert memory.get_messages() == []

    def test_get_message_count(self):
        """Test getting message count."""
        memory = ShortTermMemory()

        assert memory.get_message_count() == 0

        memory.add_message(ChatMessage(role="user", content="Hello"))
        assert memory.get_message_count() == 1

        memory.add_message(ChatMessage(role="assistant", content="Hi"))
        assert memory.get_message_count() == 2

    def test_estimate_tokens(self):
        """Test token estimation."""
        memory = ShortTermMemory()

        # Empty should be 0
        assert memory.estimate_tokens() == 0

        # Add a message (~20 chars = ~5 tokens)
        memory.add_message(ChatMessage(role="user", content="Hello, how are you?"))
        tokens = memory.estimate_tokens()
        assert tokens > 0
        assert tokens < 100  # Sanity check

    def test_is_near_token_limit(self):
        """Test token limit checking."""
        memory = ShortTermMemory(max_tokens=100)

        # Add small message - not near limit
        memory.add_message(ChatMessage(role="user", content="Hi"))
        assert not memory.is_near_token_limit(threshold=0.8)

        # Add large message to approach limit
        # Need ~80 tokens = ~320 characters
        large_message = "x" * 320
        memory.add_message(ChatMessage(role="user", content=large_message))

        # Should now be near limit
        assert memory.is_near_token_limit(threshold=0.8)

    def test_len_magic_method(self):
        """Test __len__ magic method."""
        memory = ShortTermMemory()

        assert len(memory) == 0

        memory.add_message(ChatMessage(role="user", content="Test"))
        assert len(memory) == 1

    def test_repr(self):
        """Test __repr__ method."""
        memory = ShortTermMemory(max_messages=10)
        memory.add_message(ChatMessage(role="user", content="Test"))

        repr_str = repr(memory)
        assert "ShortTermMemory" in repr_str
        assert "messages=1/10" in repr_str


class TestMemoryManager:
    """Tests for MemoryManager class."""

    def test_initialization(self):
        """Test creating a MemoryManager instance."""
        manager = MemoryManager(max_messages=20, max_tokens=5000)
        assert manager.max_messages == 20
        assert manager.max_tokens == 5000

    @pytest.mark.asyncio
    async def test_add_and_get_messages(self):
        """Test adding and retrieving messages."""
        manager = MemoryManager()
        session_id = "test-session-1"

        # Initially empty
        messages = await manager.get_messages(session_id)
        assert messages == []

        # Add a message
        msg = ChatMessage(role="user", content="Hello")
        await manager.add_message(session_id, msg)

        # Retrieve messages
        messages = await manager.get_messages(session_id)
        assert len(messages) == 1
        assert messages[0].content == "Hello"

    @pytest.mark.asyncio
    async def test_multiple_sessions(self):
        """Test managing multiple independent sessions."""
        manager = MemoryManager()

        # Add messages to different sessions
        await manager.add_message(
            "session-1", ChatMessage(role="user", content="Session 1 message")
        )
        await manager.add_message(
            "session-2", ChatMessage(role="user", content="Session 2 message")
        )

        # Each session should have its own messages
        messages_1 = await manager.get_messages("session-1")
        messages_2 = await manager.get_messages("session-2")

        assert len(messages_1) == 1
        assert len(messages_2) == 1
        assert messages_1[0].content == "Session 1 message"
        assert messages_2[0].content == "Session 2 message"

    @pytest.mark.asyncio
    async def test_clear_session(self):
        """Test clearing a session's messages."""
        manager = MemoryManager()
        session_id = "test-session"

        # Add messages
        await manager.add_message(session_id, ChatMessage(role="user", content="Test"))
        assert len(await manager.get_messages(session_id)) == 1

        # Clear session
        await manager.clear_session(session_id)

        # Should be empty now
        messages = await manager.get_messages(session_id)
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_delete_session(self):
        """Test completely deleting a session."""
        manager = MemoryManager()
        session_id = "test-session"

        # Add messages
        await manager.add_message(session_id, ChatMessage(role="user", content="Test"))

        # Verify session exists
        sessions = await manager.list_sessions()
        assert session_id in sessions

        # Delete session
        await manager.delete_session(session_id)

        # Session should be gone
        sessions = await manager.list_sessions()
        assert session_id not in sessions

        # Getting messages should return empty list
        messages = await manager.get_messages(session_id)
        assert messages == []

    @pytest.mark.asyncio
    async def test_get_session_stats(self):
        """Test getting session statistics."""
        manager = MemoryManager()
        session_id = "test-session"

        # Stats for non-existent session
        stats = await manager.get_session_stats(session_id)
        assert stats["message_count"] == 0
        assert stats["estimated_tokens"] == 0
        assert stats["near_limit"] is False

        # Add messages
        await manager.add_message(
            session_id, ChatMessage(role="user", content="Hello")
        )
        await manager.add_message(
            session_id, ChatMessage(role="assistant", content="Hi there!")
        )

        # Check stats
        stats = await manager.get_session_stats(session_id)
        assert stats["message_count"] == 2
        assert stats["estimated_tokens"] > 0

    @pytest.mark.asyncio
    async def test_list_sessions(self):
        """Test listing all active sessions."""
        manager = MemoryManager()

        # Initially no sessions
        sessions = await manager.list_sessions()
        assert len(sessions) == 0

        # Add sessions
        await manager.add_message(
            "session-1", ChatMessage(role="user", content="Test")
        )
        await manager.add_message(
            "session-2", ChatMessage(role="user", content="Test")
        )

        # Should have 2 sessions
        sessions = await manager.list_sessions()
        assert len(sessions) == 2
        assert "session-1" in sessions
        assert "session-2" in sessions

    @pytest.mark.asyncio
    async def test_get_total_sessions(self):
        """Test getting total session count."""
        manager = MemoryManager()

        assert await manager.get_total_sessions() == 0

        await manager.add_message(
            "session-1", ChatMessage(role="user", content="Test")
        )
        assert await manager.get_total_sessions() == 1

        await manager.add_message(
            "session-2", ChatMessage(role="user", content="Test")
        )
        assert await manager.get_total_sessions() == 2

    @pytest.mark.asyncio
    async def test_concurrent_access_same_session(self):
        """Test that concurrent access to same session is thread-safe."""
        import asyncio

        manager = MemoryManager()
        session_id = "test-session"

        # Add messages concurrently
        async def add_messages(prefix: str, count: int):
            for i in range(count):
                await manager.add_message(
                    session_id, ChatMessage(role="user", content=f"{prefix}-{i}")
                )

        # Run two tasks concurrently adding messages
        await asyncio.gather(add_messages("A", 5), add_messages("B", 5))

        # Should have all 10 messages (order may vary but all should be there)
        messages = await manager.get_messages(session_id)
        assert len(messages) == 10

    def test_repr(self):
        """Test __repr__ method."""
        manager = MemoryManager()
        repr_str = repr(manager)
        assert "MemoryManager" in repr_str
        assert "sessions=0" in repr_str
