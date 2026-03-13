"""
Integration tests for the FastAPI application.

These tests verify that the API endpoints work correctly with mocked
provider dependencies.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from chatbot.core import ConversationService
from chatbot.main import app
from chatbot.memory import MemoryManager


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


def test_chat_endpoint_with_mock(mock_provider):
    """Test the chat endpoint with a mocked conversation service."""
    # Create a fresh test client
    from chatbot.api.dependencies import get_conversation_service
    from fastapi.testclient import TestClient

    # Create a mock conversation service with the mock provider
    memory_manager = MemoryManager()
    mock_service = ConversationService(
        provider=mock_provider,
        memory_manager=memory_manager,
    )

    # Override the dependency
    app.dependency_overrides[get_conversation_service] = lambda: mock_service

    try:
        client = TestClient(app)
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

    finally:
        # Clean up the override
        app.dependency_overrides.clear()


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
