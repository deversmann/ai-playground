"""
Pydantic models for API requests and responses.

These models define the JSON structure for API endpoints.
FastAPI uses these to:
1. Validate incoming request data
2. Generate OpenAPI documentation
3. Provide type hints for development
4. Serialize response data

All validation happens automatically - invalid requests get 422 errors.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    Request model for chat endpoint.

    Attributes:
        message: The user's message text
        session_id: Unique identifier for this conversation session
        temperature: Response randomness (0.0-1.0), optional
        max_tokens: Maximum tokens in response, optional

    Example JSON:
        {
            "message": "What is Python?",
            "session_id": "user-123-session-1",
            "temperature": 0.7,
            "max_tokens": 500
        }
    """

    message: str = Field(
        ...,  # Required field
        min_length=1,
        max_length=10000,
        description="The user's message",
        examples=["What is Python?"],
    )

    session_id: str = Field(
        ...,  # Required field
        min_length=1,
        max_length=100,
        description="Unique session identifier",
        examples=["user-123-session-1"],
    )

    temperature: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Response randomness (0.0=focused, 1.0=creative). Uses server default if not specified.",
        examples=[0.7],
    )

    max_tokens: int | None = Field(
        default=None,
        ge=1,
        le=100000,
        description="Maximum tokens in response. Uses server default if not specified.",
        examples=[1000],
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "message": "Explain async/await in Python",
                "session_id": "user-123-session-1",
                "temperature": 0.7,
                "max_tokens": 500,
            }
        }


class TokenUsageResponse(BaseModel):
    """
    Token usage statistics in API response.

    Attributes:
        input_tokens: Tokens in the prompt
        output_tokens: Tokens in the response
        total_tokens: Total tokens used
    """

    input_tokens: int = Field(..., description="Tokens in the prompt", examples=[100])
    output_tokens: int = Field(..., description="Tokens in the response", examples=[50])
    total_tokens: int = Field(..., description="Total tokens used", examples=[150])


class ChatResponse(BaseModel):
    """
    Response model for chat endpoint.

    Attributes:
        response: The AI's response text
        model: The model that generated the response
        session_id: Echo of the request session_id
        usage: Token usage statistics

    Example JSON:
        {
            "response": "Python is a high-level programming language...",
            "model": "claude-3-5-sonnet-20241022",
            "session_id": "user-123-session-1",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 50,
                "total_tokens": 60
            }
        }
    """

    response: str = Field(..., description="The AI's response text")
    model: str = Field(..., description="The model that generated the response")
    session_id: str = Field(..., description="Session identifier")
    usage: TokenUsageResponse = Field(..., description="Token usage statistics")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "response": "Python is a high-level programming language...",
                "model": "claude-3-5-sonnet-20241022",
                "session_id": "user-123-session-1",
                "usage": {"input_tokens": 10, "output_tokens": 50, "total_tokens": 60},
            }
        }


class HealthResponse(BaseModel):
    """
    Response model for health check endpoint.

    Attributes:
        status: Health status ("healthy" or "unhealthy")
        version: API version
        provider: Currently configured AI provider

    Example JSON:
        {
            "status": "healthy",
            "version": "0.1.0",
            "provider": "anthropic"
        }
    """

    status: str = Field(..., description="Health status", examples=["healthy"])
    version: str = Field(..., description="API version", examples=["0.1.0"])
    provider: str = Field(..., description="Configured AI provider", examples=["anthropic"])


class ErrorResponse(BaseModel):
    """
    Error response model.

    Attributes:
        detail: Error message or details

    Example JSON:
        {
            "detail": "Invalid API key"
        }
    """

    detail: str = Field(..., description="Error message", examples=["Invalid API key"])
