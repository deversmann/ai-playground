"""
Integration tests for the FastAPI application.

These tests verify that the API endpoints work correctly with mocked
provider dependencies.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from chatbot.main import app
from chatbot.providers import ChatMessage, ChatResponse, TokenUsage


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def test_root_endpoint(client):
    """Test the root endpoint returns API info."""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["version"] == "0.1.0"


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "provider" in data


@pytest.mark.asyncio
async def test_chat_endpoint_with_mock(client, mock_provider):
    """Test the chat endpoint with a mocked provider."""
    # Mock the get_ai_provider dependency to return our mock
    with patch("chatbot.api.routes.chat.get_ai_provider", return_value=mock_provider):
        response = client.post(
            "/chat/send",
            json={
                "message": "Hello, AI!",
                "session_id": "test-session-123",
                "temperature": 0.7,
                "max_tokens": 100,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "response" in data
        assert "Mock response" in data["response"]
        assert data["session_id"] == "test-session-123"
        assert "usage" in data
        assert data["usage"]["total_tokens"] == 30  # 10 input + 20 output from mock


def test_chat_endpoint_validation_errors(client):
    """Test that the chat endpoint validates request data."""
    # Missing required fields
    response = client.post("/chat/send", json={})
    assert response.status_code == 422  # Validation error

    # Empty message
    response = client.post(
        "/chat/send", json={"message": "", "session_id": "test"}
    )
    assert response.status_code == 422

    # Invalid temperature
    response = client.post(
        "/chat/send",
        json={"message": "test", "session_id": "test", "temperature": 5.0},
    )
    assert response.status_code == 422

    # Invalid max_tokens
    response = client.post(
        "/chat/send",
        json={"message": "test", "session_id": "test", "max_tokens": -1},
    )
    assert response.status_code == 422
