"""
Repository pattern for conversation and message persistence.

The Repository Pattern separates data access logic from business logic.
This module provides a clean interface for CRUD operations on conversations.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from chatbot.providers.models import ChatMessage
from chatbot.storage.models import Conversation, Message


class ConversationRepository:
    """
    Repository for managing conversations and messages.

    This class provides all database operations for conversations:
    - Create/get/delete conversations
    - Add/retrieve messages
    - Count messages
    - List all conversations

    The repository pattern benefits:
    1. Single Responsibility - only handles data access
    2. Testability - easy to mock for testing
    3. Maintainability - all SQL in one place
    4. Swappable - could switch to different storage
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with a database session.

        Args:
            session: Active database session
        """
        self.session = session

    async def create_conversation(self, session_id: str) -> Conversation:
        """
        Create a new conversation.

        Args:
            session_id: Unique identifier for the conversation

        Returns:
            Conversation: The created conversation

        Raises:
            IntegrityError: If session_id already exists (unique constraint)
        """
        conversation = Conversation(
            session_id=session_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            message_count=0,
        )

        # Add to session (not yet in database)
        self.session.add(conversation)

        # Flush to database but don't commit yet
        # This generates the id but allows rollback if needed
        await self.session.flush()

        # Refresh to get any database defaults
        await self.session.refresh(conversation)

        return conversation

    async def get_conversation(self, session_id: str) -> Optional[Conversation]:
        """
        Get a conversation by session_id.

        Args:
            session_id: Unique conversation identifier

        Returns:
            Conversation if found, None otherwise
        """
        # SQLAlchemy 2.0 query style using select()
        stmt = select(Conversation).where(Conversation.session_id == session_id)

        # Execute and get result
        result = await self.session.execute(stmt)

        # scalar_one_or_none(): Get single result or None
        return result.scalar_one_or_none()

    async def get_or_create_conversation(self, session_id: str) -> Conversation:
        """
        Get existing conversation or create if it doesn't exist.

        This is a common pattern for lazy session creation.

        Args:
            session_id: Unique conversation identifier

        Returns:
            Conversation: Existing or newly created conversation
        """
        conversation = await self.get_conversation(session_id)

        if conversation is None:
            conversation = await self.create_conversation(session_id)

        return conversation

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        token_count: Optional[int] = None,
    ) -> Message:
        """
        Add a message to a conversation.

        If the conversation doesn't exist, it will be created.

        Args:
            session_id: Conversation identifier
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            token_count: Optional token count for tracking

        Returns:
            Message: The created message
        """
        # Get or create the conversation
        conversation = await self.get_or_create_conversation(session_id)

        # Create the message
        message = Message(
            conversation_id=conversation.id,
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
            token_count=token_count,
        )

        # Add to session
        self.session.add(message)

        # Update conversation metadata
        conversation.message_count += 1
        conversation.updated_at = datetime.utcnow()

        # Flush to database
        await self.session.flush()
        await self.session.refresh(message)

        return message

    async def add_messages_batch(
        self, session_id: str, messages: list[ChatMessage]
    ) -> list[Message]:
        """
        Add multiple messages at once (more efficient than one-by-one).

        Args:
            session_id: Conversation identifier
            messages: List of ChatMessage objects to add

        Returns:
            list[Message]: The created Message objects
        """
        # Get or create conversation
        conversation = await self.get_or_create_conversation(session_id)

        # Create Message objects
        db_messages = []
        for msg in messages:
            db_message = Message(
                conversation_id=conversation.id,
                role=msg.role,
                content=msg.content,
                timestamp=datetime.utcnow(),
                token_count=None,  # Could estimate from content length
            )
            db_messages.append(db_message)

        # Add all messages
        self.session.add_all(db_messages)

        # Update conversation metadata
        conversation.message_count += len(messages)
        conversation.updated_at = datetime.utcnow()

        # Flush and refresh
        await self.session.flush()
        for msg in db_messages:
            await self.session.refresh(msg)

        return db_messages

    async def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> list[Message]:
        """
        Get messages for a conversation in chronological order.

        Args:
            session_id: Conversation identifier
            limit: Maximum number of messages to return (None = all)
            offset: Number of messages to skip

        Returns:
            list[Message]: Messages in chronological order
        """
        # First get the conversation
        conversation = await self.get_conversation(session_id)

        if conversation is None:
            return []

        # Build query for messages
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.timestamp.asc())  # Chronological order
            .offset(offset)
        )

        # Add limit if specified
        if limit is not None:
            stmt = stmt.limit(limit)

        # Execute query
        result = await self.session.execute(stmt)

        # scalars(): Get list of Message objects (not tuples)
        # all(): Fetch all results
        return list(result.scalars().all())

    async def get_messages_as_chat_messages(
        self, session_id: str, limit: Optional[int] = None
    ) -> list[ChatMessage]:
        """
        Get messages converted to ChatMessage format.

        This is useful for sending to AI providers.

        Args:
            session_id: Conversation identifier
            limit: Maximum messages to return

        Returns:
            list[ChatMessage]: Messages in provider format
        """
        messages = await self.get_messages(session_id, limit=limit)

        # Convert to ChatMessage format
        return [ChatMessage(role=msg.role, content=msg.content) for msg in messages]

    async def count_messages(self, session_id: str) -> int:
        """
        Count messages in a conversation.

        Args:
            session_id: Conversation identifier

        Returns:
            int: Number of messages (0 if conversation doesn't exist)
        """
        conversation = await self.get_conversation(session_id)

        if conversation is None:
            return 0

        # Could use conversation.message_count (cached)
        # Or query for accuracy (in case of inconsistency)
        stmt = select(func.count(Message.id)).where(
            Message.conversation_id == conversation.id
        )

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def delete_conversation(self, session_id: str) -> bool:
        """
        Delete a conversation and all its messages.

        Due to cascade="all, delete-orphan" in the relationship,
        all messages are automatically deleted.

        Args:
            session_id: Conversation identifier

        Returns:
            bool: True if deleted, False if not found
        """
        conversation = await self.get_conversation(session_id)

        if conversation is None:
            return False

        # Delete the conversation (messages cascade automatically)
        await self.session.delete(conversation)
        await self.session.flush()

        return True

    async def clear_messages(self, session_id: str) -> int:
        """
        Clear all messages from a conversation (keep the conversation).

        Args:
            session_id: Conversation identifier

        Returns:
            int: Number of messages deleted
        """
        conversation = await self.get_conversation(session_id)

        if conversation is None:
            return 0

        # Delete all messages for this conversation
        stmt = delete(Message).where(Message.conversation_id == conversation.id)

        result = await self.session.execute(stmt)

        # Update conversation metadata
        conversation.message_count = 0
        conversation.updated_at = datetime.utcnow()

        await self.session.flush()

        # rowcount: number of rows affected
        return result.rowcount

    async def list_conversations(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> list[Conversation]:
        """
        List all conversations, ordered by most recent first.

        Args:
            limit: Maximum conversations to return
            offset: Number to skip (for pagination)

        Returns:
            list[Conversation]: Conversations ordered by updated_at desc
        """
        stmt = (
            select(Conversation)
            .order_by(Conversation.updated_at.desc())  # Most recent first
            .offset(offset)
        )

        if limit is not None:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_conversation_stats(self, session_id: str) -> dict:
        """
        Get statistics about a conversation.

        Args:
            session_id: Conversation identifier

        Returns:
            dict: Statistics (message_count, created_at, updated_at, etc.)
        """
        conversation = await self.get_conversation(session_id)

        if conversation is None:
            return {
                "exists": False,
                "session_id": session_id,
            }

        # Count messages by role
        stmt = (
            select(Message.role, func.count(Message.id))
            .where(Message.conversation_id == conversation.id)
            .group_by(Message.role)
        )

        result = await self.session.execute(stmt)
        role_counts = dict(result.all())

        return {
            "exists": True,
            "session_id": session_id,
            "message_count": conversation.message_count,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "user_messages": role_counts.get("user", 0),
            "assistant_messages": role_counts.get("assistant", 0),
            "system_messages": role_counts.get("system", 0),
        }


# Key Repository Pattern Benefits:
#
# 1. Single Responsibility
#    - ConversationRepository ONLY handles database operations
#    - Business logic stays in ConversationService
#    - Clear separation of concerns
#
# 2. Testability
#    - Easy to mock for unit tests
#    - Can test business logic without database
#    - Can test repository with real database
#
# 3. Maintainability
#    - All SQL queries in one place
#    - Easy to optimize queries
#    - Easy to add new operations
#
# 4. Type Safety
#    - Strong typing with SQLAlchemy 2.0
#    - Returns domain objects (Conversation, Message)
#    - IDE autocomplete works perfectly
#
# 5. Swappable Implementation
#    - Could switch to PostgreSQL, MongoDB, etc.
#    - Just change repository implementation
#    - Business logic unchanged
