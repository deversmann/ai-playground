"""
SQLAlchemy ORM models for persistent storage.

This module defines the database schema using SQLAlchemy 2.0's new declarative syntax
with Mapped types for better type safety.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """
    Base class for all ORM models.

    SQLAlchemy 2.0 uses DeclarativeBase instead of the old declarative_base() function.
    All models inherit from this to get ORM functionality.
    """

    pass


class Conversation(Base):
    """
    Represents a conversation session (metadata).

    This table stores metadata about each conversation:
    - Unique session identifier
    - Creation and last update timestamps
    - Message count for quick stats

    Each conversation has many messages (one-to-many relationship).
    """

    __tablename__ = "conversations"

    # Primary key - auto-incrementing integer
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Session ID - unique identifier for this conversation
    # indexed for fast lookups by session_id
    session_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    # Timestamps - when conversation was created and last updated
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Message count - cached count for performance
    # Incremented when messages are added
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationship to messages
    # - back_populates: creates bidirectional relationship
    # - cascade: when conversation is deleted, delete all its messages
    # - order_by: messages always returned in chronological order
    # - lazy="selectin": load messages efficiently with a single query
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.timestamp",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<Conversation(id={self.id}, session_id='{self.session_id}', "
            f"message_count={self.message_count})>"
        )


class Message(Base):
    """
    Individual message in a conversation.

    Messages are stored in chronological order with:
    - Role (user/assistant/system)
    - Content (the actual message text)
    - Timestamp (when it was created)
    - Token count (for cost tracking and context window management)
    """

    __tablename__ = "messages"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Foreign key to conversation
    # References the 'id' column of the conversations table
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id"), nullable=False
    )

    # Message role - 'user', 'assistant', or 'system'
    role: Mapped[str] = mapped_column(String(50), nullable=False)

    # Message content - can be very long, so we use Text instead of String
    # Text type has no length limit (unlike String which defaults to 255)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Timestamp - when this message was created
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Token count - optional field for tracking token usage
    # Nullable because we might not always have this information
    # Useful for:
    # - Cost tracking (tokens = money)
    # - Context window management (staying under limits)
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationship back to conversation
    # back_populates: creates bidirectional relationship
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

    # Indexes for efficient querying
    # Composite index on (conversation_id, timestamp) for chronological retrieval
    # Index on role for filtering by message type
    __table_args__ = (
        Index("idx_conversation_timestamp", "conversation_id", "timestamp"),
        Index("idx_role", "role"),
    )

    def __repr__(self) -> str:
        """String representation for debugging."""
        # Truncate content to 50 chars for readability
        content_preview = (
            self.content[:50] + "..." if len(self.content) > 50 else self.content
        )
        return (
            f"<Message(id={self.id}, role='{self.role}', "
            f"content='{content_preview}')>"
        )


# Key SQLAlchemy 2.0 Patterns Explained:
#
# 1. Mapped[type] - Type hints for ORM attributes
#    - Mapped[int] - Required integer field
#    - Mapped[Optional[int]] - Nullable integer field
#    - Mapped[list["Message"]] - One-to-many relationship
#
# 2. mapped_column() - Replaces Column() from SQLAlchemy 1.x
#    - Takes SQLAlchemy types (Integer, String, Text, DateTime)
#    - Configures nullable, default, index, etc.
#
# 3. relationship() - Defines relationships between tables
#    - back_populates: makes relationship bidirectional
#    - cascade: propagate operations (delete, update)
#    - order_by: default ordering for related objects
#    - lazy: how/when to load related objects
#
# 4. ForeignKey() - Creates foreign key constraint
#    - Links messages to their conversation
#    - Ensures referential integrity
#
# 5. Index() - Creates database indexes
#    - Speeds up queries on indexed columns
#    - Composite indexes for multi-column queries
#
# 6. DeclarativeBase - New base class in SQLAlchemy 2.0
#    - Replaces declarative_base()
#    - Better type checking support
