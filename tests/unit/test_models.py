"""
Unit tests for provider data models.

These tests verify that our data models (ChatMessage, TokenUsage, ChatResponse)
work correctly and validate data properly.
"""

import pytest

from chatbot.providers.models import ChatMessage, ChatResponse, TokenUsage


class TestChatMessage:
    """Tests for ChatMessage model."""

    def test_valid_message(self):
        """Test creating a valid message."""
        msg = ChatMessage(role="user", content="Hello!")
        assert msg.role == "user"
        assert msg.content == "Hello!"

    def test_all_valid_roles(self):
        """Test all valid role types."""
        for role in ["user", "assistant", "system"]:
            msg = ChatMessage(role=role, content="test")
            assert msg.role == role

    def test_invalid_role(self):
        """Test that invalid roles raise an error."""
        with pytest.raises(ValueError, match="Invalid role"):
            ChatMessage(role="invalid", content="test")

    def test_empty_content(self):
        """Test that empty content raises an error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            ChatMessage(role="user", content="")

    def test_whitespace_only_content(self):
        """Test that whitespace-only content raises an error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            ChatMessage(role="user", content="   ")


class TestTokenUsage:
    """Tests for TokenUsage model."""

    def test_calculates_total(self):
        """Test that total tokens are calculated correctly."""
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        assert usage.total_tokens == 150

    def test_from_dict_standard(self):
        """Test creating from standard dictionary format."""
        usage = TokenUsage.from_dict({"input_tokens": 100, "output_tokens": 50})
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.total_tokens == 150

    def test_from_dict_alternative_names(self):
        """Test creating from alternative key names (OpenAI format)."""
        usage = TokenUsage.from_dict({"prompt_tokens": 100, "completion_tokens": 50})
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50

    def test_from_dict_missing_keys(self):
        """Test handling missing keys defaults to 0."""
        usage = TokenUsage.from_dict({})
        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
        assert usage.total_tokens == 0


class TestChatResponse:
    """Tests for ChatResponse model."""

    def test_valid_response(self):
        """Test creating a valid response."""
        usage = TokenUsage(input_tokens=10, output_tokens=20)
        response = ChatResponse(
            content="Hello!", model="claude-3-5-sonnet", usage=usage, metadata={}
        )
        assert response.content == "Hello!"
        assert response.model == "claude-3-5-sonnet"
        assert response.usage.total_tokens == 30

    def test_empty_content_error(self):
        """Test that empty content raises an error."""
        usage = TokenUsage(input_tokens=10, output_tokens=20)
        with pytest.raises(ValueError, match="cannot be empty"):
            ChatResponse(content="", model="test", usage=usage)

    def test_empty_model_error(self):
        """Test that empty model name raises an error."""
        usage = TokenUsage(input_tokens=10, output_tokens=20)
        with pytest.raises(ValueError, match="must be provided"):
            ChatResponse(content="test", model="", usage=usage)

    def test_to_dict(self):
        """Test converting response to dictionary."""
        usage = TokenUsage(input_tokens=10, output_tokens=20)
        response = ChatResponse(
            content="Hello!",
            model="claude-3-5-sonnet",
            usage=usage,
            metadata={"id": "test-123"},
        )

        result = response.to_dict()

        assert result["content"] == "Hello!"
        assert result["model"] == "claude-3-5-sonnet"
        assert result["usage"]["input_tokens"] == 10
        assert result["usage"]["output_tokens"] == 20
        assert result["usage"]["total_tokens"] == 30
        assert result["metadata"]["id"] == "test-123"

    def test_default_metadata(self):
        """Test that metadata defaults to empty dict."""
        usage = TokenUsage(input_tokens=10, output_tokens=20)
        response = ChatResponse(content="test", model="test", usage=usage)
        assert response.metadata == {}
