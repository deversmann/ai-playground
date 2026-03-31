"""
Unit tests for storage models.

Tests the SQLAlchemy ORM models for basic functionality without
requiring a full database connection.
"""

from datetime import datetime

import pytest

from chatbot.storage.models import Conversation, Message


class TestConversationModel:
    """Test the Conversation ORM model."""

    def test_conversation_creation(self):
        """Test creating a Conversation instance."""
        conv = Conversation(
            session_id="test-session-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            message_count=0,
        )

        assert conv.session_id == "test-session-123"
        assert conv.message_count == 0
        assert isinstance(conv.created_at, datetime)
        assert isinstance(conv.updated_at, datetime)

    def test_conversation_repr(self):
        """Test Conversation string representation."""
        conv = Conversation(
            id=1,
            session_id="test-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            message_count=5,
        )

        repr_str = repr(conv)
        assert "Conversation" in repr_str
        assert "test-123" in repr_str
        assert "5" in repr_str


class TestMessageModel:
    """Test the Message ORM model."""

    def test_message_creation(self):
        """Test creating a Message instance."""
        msg = Message(
            conversation_id=1,
            role="user",
            content="Hello, AI!",
            timestamp=datetime.utcnow(),
        )

        assert msg.conversation_id == 1
        assert msg.role == "user"
        assert msg.content == "Hello, AI!"
        assert isinstance(msg.timestamp, datetime)
        assert msg.token_count is None  # Optional field

    def test_message_with_token_count(self):
        """Test creating a Message with token count."""
        msg = Message(
            conversation_id=1,
            role="assistant",
            content="Hello! How can I help?",
            timestamp=datetime.utcnow(),
            token_count=25,
        )

        assert msg.token_count == 25

    def test_message_repr(self):
        """Test Message string representation."""
        msg = Message(
            id=1,
            conversation_id=1,
            role="user",
            content="This is a test message that is quite long and should be truncated",
            timestamp=datetime.utcnow(),
        )

        repr_str = repr(msg)
        assert "Message" in repr_str
        assert "user" in repr_str
        # Should be truncated
        assert "..." in repr_str

    def test_message_repr_short_content(self):
        """Test Message string representation with short content."""
        msg = Message(
            id=1,
            conversation_id=1,
            role="assistant",
            content="Short message",
            timestamp=datetime.utcnow(),
        )

        repr_str = repr(msg)
        assert "Message" in repr_str
        assert "assistant" in repr_str
        assert "Short message" in repr_str
        assert "..." not in repr_str  # Not truncated
