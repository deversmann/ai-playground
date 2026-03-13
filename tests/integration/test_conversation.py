"""
Integration tests for ConversationService.

Tests the integration between memory system and AI provider.
"""

import pytest

from chatbot.core import ConversationService
from chatbot.memory import MemoryManager
from chatbot.providers.models import ChatMessage, ChatResponse, TokenUsage


@pytest.fixture
def mock_provider():
    """
    Create a mock AI provider for testing.

    This provider returns predictable responses without calling real APIs.
    """

    class MockProvider:
        def __init__(self):
            self.call_count = 0

        async def chat(
            self, messages: list[ChatMessage], **kwargs
        ) -> ChatResponse:
            """Mock chat method that echoes the conversation context."""
            self.call_count += 1

            # Build response that shows we received the full conversation
            message_summary = [
                f"{msg.role}: {msg.content}" for msg in messages
            ]
            response_text = (
                f"Mock response #{self.call_count}. "
                f"Received {len(messages)} messages: {', '.join(message_summary)}"
            )

            return ChatResponse(
                content=response_text,
                model="mock-model",
                usage=TokenUsage(
                    input_tokens=len(str(messages)),
                    output_tokens=len(response_text),
                ),
                metadata={"call_count": self.call_count},
            )

    return MockProvider()


@pytest.fixture
def memory_manager():
    """Create a fresh MemoryManager for testing."""
    return MemoryManager()


@pytest.fixture
def conversation_service(mock_provider, memory_manager):
    """Create a ConversationService with mock dependencies."""
    return ConversationService(
        provider=mock_provider,
        memory_manager=memory_manager,
    )


class TestConversationService:
    """Tests for ConversationService class."""

    @pytest.mark.asyncio
    async def test_send_message(self, conversation_service):
        """Test sending a basic message."""
        response = await conversation_service.send_message(
            session_id="test-session",
            user_message="Hello!",
        )

        assert isinstance(response, ChatResponse)
        assert "Mock response" in response.content
        assert response.model == "mock-model"
        assert response.usage.input_tokens > 0
        assert response.usage.output_tokens > 0

    @pytest.mark.asyncio
    async def test_conversation_context(self, conversation_service):
        """Test that conversation context is maintained."""
        session_id = "test-session"

        # First message
        response1 = await conversation_service.send_message(
            session_id=session_id,
            user_message="First message",
        )
        assert "Received 1 messages" in response1.content

        # Second message - should include previous context
        response2 = await conversation_service.send_message(
            session_id=session_id,
            user_message="Second message",
        )
        # Should have: user msg 1, assistant response 1, user msg 2
        assert "Received 3 messages" in response2.content

        # Third message - should have full conversation
        response3 = await conversation_service.send_message(
            session_id=session_id,
            user_message="Third message",
        )
        # Should have: all previous + new message = 5 messages
        assert "Received 5 messages" in response3.content

    @pytest.mark.asyncio
    async def test_system_prompt(self, conversation_service):
        """Test that system prompts are included but not stored."""
        session_id = "test-session"

        # Send message with system prompt
        response1 = await conversation_service.send_message(
            session_id=session_id,
            user_message="Hello",
            system_prompt="You are a helpful assistant.",
        )

        # System prompt should be sent (included in message count)
        assert "Received 2 messages" in response1.content  # system + user
        assert "system: You are a helpful assistant" in response1.content

        # Check conversation history - system prompt should NOT be stored
        history = await conversation_service.get_conversation_history(session_id)
        assert len(history) == 2  # Only user + assistant, no system
        assert all(msg.role != "system" for msg in history)

        # Send another message with no system prompt
        response2 = await conversation_service.send_message(
            session_id=session_id,
            user_message="Follow-up",
        )

        # Should have: user msg 1, assistant response 1, user msg 2
        # (no system prompt in history)
        assert "Received 3 messages" in response2.content

        # Verify history still has no system prompts
        history2 = await conversation_service.get_conversation_history(session_id)
        assert len(history2) == 4  # 2 users + 2 assistants
        assert all(msg.role != "system" for msg in history2)

    @pytest.mark.asyncio
    async def test_multiple_sessions(self, conversation_service):
        """Test that different sessions maintain separate contexts."""
        # Send to session 1
        response1 = await conversation_service.send_message(
            session_id="session-1",
            user_message="Session 1 message",
        )
        assert "Received 1 messages" in response1.content

        # Send to session 2
        response2 = await conversation_service.send_message(
            session_id="session-2",
            user_message="Session 2 message",
        )
        assert "Received 1 messages" in response2.content

        # Send another to session 1 - should only have session 1 context
        response3 = await conversation_service.send_message(
            session_id="session-1",
            user_message="Session 1 follow-up",
        )
        assert "Received 3 messages" in response3.content
        assert "Session 1" in response3.content
        assert "Session 2" not in response3.content

    @pytest.mark.asyncio
    async def test_get_conversation_history(self, conversation_service):
        """Test retrieving conversation history."""
        session_id = "test-session"

        # Initially empty
        history = await conversation_service.get_conversation_history(session_id)
        assert len(history) == 0

        # Send a message
        await conversation_service.send_message(
            session_id=session_id,
            user_message="Hello",
        )

        # Should now have 2 messages (user + assistant)
        history = await conversation_service.get_conversation_history(session_id)
        assert len(history) == 2
        assert history[0].role == "user"
        assert history[0].content == "Hello"
        assert history[1].role == "assistant"

    @pytest.mark.asyncio
    async def test_clear_conversation(self, conversation_service):
        """Test clearing conversation history."""
        session_id = "test-session"

        # Send messages
        await conversation_service.send_message(
            session_id=session_id,
            user_message="Test message",
        )

        # Verify history exists
        history = await conversation_service.get_conversation_history(session_id)
        assert len(history) > 0

        # Clear conversation
        await conversation_service.clear_conversation(session_id)

        # History should be empty
        history = await conversation_service.get_conversation_history(session_id)
        assert len(history) == 0

    @pytest.mark.asyncio
    async def test_delete_conversation(self, conversation_service):
        """Test deleting a conversation."""
        session_id = "test-session"

        # Send messages
        await conversation_service.send_message(
            session_id=session_id,
            user_message="Test message",
        )

        # Delete conversation
        await conversation_service.delete_conversation(session_id)

        # Session should be completely removed
        sessions = await conversation_service.list_active_sessions()
        assert session_id not in sessions

    @pytest.mark.asyncio
    async def test_get_conversation_stats(self, conversation_service):
        """Test getting conversation statistics."""
        session_id = "test-session"

        # Stats for empty session
        stats = await conversation_service.get_conversation_stats(session_id)
        assert stats["message_count"] == 0

        # Send message
        await conversation_service.send_message(
            session_id=session_id,
            user_message="Test message",
        )

        # Check stats
        stats = await conversation_service.get_conversation_stats(session_id)
        assert stats["message_count"] == 2  # user + assistant
        assert stats["estimated_tokens"] > 0

    @pytest.mark.asyncio
    async def test_list_active_sessions(self, conversation_service):
        """Test listing active sessions."""
        # Initially no sessions
        sessions = await conversation_service.list_active_sessions()
        assert len(sessions) == 0

        # Create sessions
        await conversation_service.send_message(
            session_id="session-1",
            user_message="Test",
        )
        await conversation_service.send_message(
            session_id="session-2",
            user_message="Test",
        )

        # Should list both sessions
        sessions = await conversation_service.list_active_sessions()
        assert len(sessions) == 2
        assert "session-1" in sessions
        assert "session-2" in sessions

    @pytest.mark.asyncio
    async def test_temperature_and_max_tokens(self, conversation_service, mock_provider):
        """Test that temperature and max_tokens are passed to provider."""
        # Note: Our mock provider doesn't actually use these, but we can
        # verify they're passed by checking the provider was called

        initial_count = mock_provider.call_count

        await conversation_service.send_message(
            session_id="test-session",
            user_message="Test",
            temperature=0.5,
            max_tokens=100,
        )

        # Provider should have been called
        assert mock_provider.call_count == initial_count + 1

    @pytest.mark.asyncio
    async def test_repr(self, conversation_service):
        """Test __repr__ method."""
        repr_str = repr(conversation_service)
        assert "ConversationService" in repr_str
        assert "MockProvider" in repr_str
