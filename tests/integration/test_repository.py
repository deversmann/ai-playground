"""
Integration tests for ConversationRepository.

These tests use a real SQLite database to verify repository operations.
The database is created in memory for each test and discarded afterward.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from chatbot.providers.models import ChatMessage
from chatbot.storage.models import Base
from chatbot.storage.repositories import ConversationRepository


@pytest.fixture
async def async_engine():
    """Create an in-memory SQLite database engine for testing."""
    # Use in-memory SQLite database (doesn't persist)
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",  # In-memory database
        echo=False,  # Set to True for SQL debugging
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest.fixture
async def db_session(async_engine):
    """Create a database session for testing."""
    async_session_factory = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_factory() as session:
        yield session
        await session.rollback()  # Rollback any uncommitted changes


@pytest.fixture
async def repository(db_session):
    """Create a ConversationRepository for testing."""
    return ConversationRepository(session=db_session)


class TestConversationRepository:
    """Test ConversationRepository CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_conversation(self, repository, db_session):
        """Test creating a new conversation."""
        conv = await repository.create_conversation("session-123")
        await db_session.commit()

        assert conv is not None
        assert conv.session_id == "session-123"
        assert conv.message_count == 0
        assert conv.id is not None  # Auto-generated

    @pytest.mark.asyncio
    async def test_get_conversation(self, repository, db_session):
        """Test retrieving a conversation by session_id."""
        # Create
        await repository.create_conversation("session-abc")
        await db_session.commit()

        # Retrieve
        conv = await repository.get_conversation("session-abc")

        assert conv is not None
        assert conv.session_id == "session-abc"

    @pytest.mark.asyncio
    async def test_get_nonexistent_conversation(self, repository):
        """Test retrieving a conversation that doesn't exist."""
        conv = await repository.get_conversation("nonexistent")
        assert conv is None

    @pytest.mark.asyncio
    async def test_get_or_create_conversation_new(self, repository, db_session):
        """Test get_or_create with a new conversation."""
        conv = await repository.get_or_create_conversation("session-new")
        await db_session.commit()

        assert conv is not None
        assert conv.session_id == "session-new"

    @pytest.mark.asyncio
    async def test_get_or_create_conversation_existing(self, repository, db_session):
        """Test get_or_create with an existing conversation."""
        # Create first
        conv1 = await repository.get_or_create_conversation("session-existing")
        await db_session.commit()
        original_id = conv1.id

        # Get existing
        conv2 = await repository.get_or_create_conversation("session-existing")

        assert conv2.id == original_id  # Same conversation
        assert conv2.session_id == "session-existing"

    @pytest.mark.asyncio
    async def test_add_message(self, repository, db_session):
        """Test adding a message to a conversation."""
        msg = await repository.add_message(
            session_id="session-msg",
            role="user",
            content="Hello, world!",
        )
        await db_session.commit()

        assert msg is not None
        assert msg.role == "user"
        assert msg.content == "Hello, world!"
        assert msg.conversation_id is not None

    @pytest.mark.asyncio
    async def test_add_message_creates_conversation(self, repository, db_session):
        """Test that adding a message creates conversation if it doesn't exist."""
        msg = await repository.add_message(
            session_id="auto-created-session",
            role="user",
            content="Test message",
        )
        await db_session.commit()

        # Verify conversation was created
        conv = await repository.get_conversation("auto-created-session")
        assert conv is not None
        assert conv.message_count == 1

    @pytest.mark.asyncio
    async def test_add_message_with_token_count(self, repository, db_session):
        """Test adding a message with token count."""
        msg = await repository.add_message(
            session_id="session-tokens",
            role="assistant",
            content="This is a response",
            token_count=42,
        )
        await db_session.commit()

        assert msg.token_count == 42

    @pytest.mark.asyncio
    async def test_add_messages_batch(self, repository, db_session):
        """Test adding multiple messages at once."""
        messages = [
            ChatMessage(role="user", content="Message 1"),
            ChatMessage(role="assistant", content="Response 1"),
            ChatMessage(role="user", content="Message 2"),
        ]

        db_messages = await repository.add_messages_batch(
            session_id="batch-session",
            messages=messages,
        )
        await db_session.commit()

        assert len(db_messages) == 3
        assert db_messages[0].role == "user"
        assert db_messages[1].role == "assistant"
        assert db_messages[2].role == "user"

        # Verify conversation message count
        conv = await repository.get_conversation("batch-session")
        assert conv.message_count == 3

    @pytest.mark.asyncio
    async def test_get_messages(self, repository, db_session):
        """Test retrieving messages for a conversation."""
        # Add messages
        await repository.add_message("session-get", "user", "First")
        await repository.add_message("session-get", "assistant", "Second")
        await repository.add_message("session-get", "user", "Third")
        await db_session.commit()

        # Retrieve
        messages = await repository.get_messages("session-get")

        assert len(messages) == 3
        assert messages[0].content == "First"
        assert messages[1].content == "Second"
        assert messages[2].content == "Third"

    @pytest.mark.asyncio
    async def test_get_messages_empty(self, repository):
        """Test retrieving messages for a conversation that doesn't exist."""
        messages = await repository.get_messages("nonexistent")
        assert messages == []

    @pytest.mark.asyncio
    async def test_get_messages_with_limit(self, repository, db_session):
        """Test retrieving messages with a limit."""
        # Add 5 messages
        for i in range(5):
            await repository.add_message("session-limit", "user", f"Message {i}")
        await db_session.commit()

        # Get only 3
        messages = await repository.get_messages("session-limit", limit=3)

        assert len(messages) == 3
        assert messages[0].content == "Message 0"
        assert messages[2].content == "Message 2"

    @pytest.mark.asyncio
    async def test_get_messages_with_offset(self, repository, db_session):
        """Test retrieving messages with an offset."""
        # Add messages
        await repository.add_message("session-offset", "user", "First")
        await repository.add_message("session-offset", "user", "Second")
        await repository.add_message("session-offset", "user", "Third")
        await db_session.commit()

        # Skip first message
        messages = await repository.get_messages("session-offset", offset=1)

        assert len(messages) == 2
        assert messages[0].content == "Second"
        assert messages[1].content == "Third"

    @pytest.mark.asyncio
    async def test_get_messages_as_chat_messages(self, repository, db_session):
        """Test converting messages to ChatMessage format."""
        await repository.add_message("session-chat", "user", "Hello")
        await repository.add_message("session-chat", "assistant", "Hi!")
        await db_session.commit()

        chat_messages = await repository.get_messages_as_chat_messages("session-chat")

        assert len(chat_messages) == 2
        assert isinstance(chat_messages[0], ChatMessage)
        assert chat_messages[0].role == "user"
        assert chat_messages[0].content == "Hello"
        assert chat_messages[1].role == "assistant"

    @pytest.mark.asyncio
    async def test_count_messages(self, repository, db_session):
        """Test counting messages in a conversation."""
        # Add messages
        await repository.add_message("session-count", "user", "One")
        await repository.add_message("session-count", "assistant", "Two")
        await repository.add_message("session-count", "user", "Three")
        await db_session.commit()

        count = await repository.count_messages("session-count")
        assert count == 3

    @pytest.mark.asyncio
    async def test_count_messages_empty(self, repository):
        """Test counting messages for nonexistent conversation."""
        count = await repository.count_messages("nonexistent")
        assert count == 0

    @pytest.mark.asyncio
    async def test_clear_messages(self, repository, db_session):
        """Test clearing messages from a conversation."""
        # Add messages
        await repository.add_message("session-clear", "user", "Message 1")
        await repository.add_message("session-clear", "user", "Message 2")
        await db_session.commit()

        # Clear
        deleted_count = await repository.clear_messages("session-clear")
        await db_session.commit()

        assert deleted_count == 2

        # Verify messages are gone
        messages = await repository.get_messages("session-clear")
        assert len(messages) == 0

        # But conversation still exists
        conv = await repository.get_conversation("session-clear")
        assert conv is not None
        assert conv.message_count == 0

    @pytest.mark.asyncio
    async def test_delete_conversation(self, repository, db_session):
        """Test deleting a conversation and its messages."""
        # Create conversation with messages
        await repository.add_message("session-delete", "user", "Message")
        await db_session.commit()

        # Delete
        deleted = await repository.delete_conversation("session-delete")
        await db_session.commit()

        assert deleted is True

        # Verify it's gone
        conv = await repository.get_conversation("session-delete")
        assert conv is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_conversation(self, repository):
        """Test deleting a conversation that doesn't exist."""
        deleted = await repository.delete_conversation("nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_list_conversations(self, repository, db_session):
        """Test listing all conversations."""
        # Create conversations
        await repository.create_conversation("session-1")
        await repository.create_conversation("session-2")
        await repository.create_conversation("session-3")
        await db_session.commit()

        # List
        conversations = await repository.list_conversations()

        assert len(conversations) == 3
        session_ids = [c.session_id for c in conversations]
        assert "session-1" in session_ids
        assert "session-2" in session_ids
        assert "session-3" in session_ids

    @pytest.mark.asyncio
    async def test_list_conversations_with_limit(self, repository, db_session):
        """Test listing conversations with limit."""
        # Create 5 conversations
        for i in range(5):
            await repository.create_conversation(f"session-{i}")
        await db_session.commit()

        # Get only 3
        conversations = await repository.list_conversations(limit=3)
        assert len(conversations) == 3

    @pytest.mark.asyncio
    async def test_get_conversation_stats(self, repository, db_session):
        """Test getting conversation statistics."""
        # Create conversation with messages
        await repository.add_message("session-stats", "user", "Question 1")
        await repository.add_message("session-stats", "assistant", "Answer 1")
        await repository.add_message("session-stats", "user", "Question 2")
        await db_session.commit()

        # Get stats
        stats = await repository.get_conversation_stats("session-stats")

        assert stats["exists"] is True
        assert stats["session_id"] == "session-stats"
        assert stats["message_count"] == 3
        assert stats["user_messages"] == 2
        assert stats["assistant_messages"] == 1
        assert stats["system_messages"] == 0

    @pytest.mark.asyncio
    async def test_get_conversation_stats_nonexistent(self, repository):
        """Test getting stats for a conversation that doesn't exist."""
        stats = await repository.get_conversation_stats("nonexistent")

        assert stats["exists"] is False
        assert stats["session_id"] == "nonexistent"
