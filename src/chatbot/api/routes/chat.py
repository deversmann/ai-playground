"""
Chat endpoint.

This is the main API endpoint for sending messages to the AI and receiving
responses. In Phase 1, it's stateless - each request is independent.

Future phases will add:
- Phase 2: Session-based conversation context (short-term memory)
- Phase 3: Persistent conversation history (database)
- Phase 4: Semantic memory retrieval
- Phase 6: Streaming responses

Example:
    $ curl -X POST http://localhost:8000/chat/send \
        -H "Content-Type: application/json" \
        -d '{"message": "Hello!", "session_id": "test-123"}'
"""

from fastapi import APIRouter, Depends, HTTPException, status

from chatbot.providers import AIProvider, ChatMessage
from ..dependencies import get_ai_provider
from ..models import ChatRequest, ChatResponse, TokenUsageResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "/send",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a chat message",
    description="Send a message to the AI and receive a response",
    response_description="The AI's response with metadata",
    responses={
        200: {
            "description": "Successful response",
            "content": {
                "application/json": {
                    "example": {
                        "response": "Hello! How can I help you today?",
                        "model": "claude-3-5-sonnet-20241022",
                        "session_id": "test-123",
                        "usage": {
                            "input_tokens": 10,
                            "output_tokens": 8,
                            "total_tokens": 18,
                        },
                    }
                }
            },
        },
        422: {"description": "Validation error (invalid request format)"},
        500: {"description": "Server error (AI provider failure)"},
    },
)
async def send_message(
    request: ChatRequest,
    provider: AIProvider = Depends(get_ai_provider),
) -> ChatResponse:
    """
    Send a message to the AI and get a response.

    Phase 1: This is a stateless endpoint. Each message is independent
    with no conversation context. The session_id is accepted but not
    yet used - it will be used in Phase 2 for conversation history.

    Args:
        request: Chat request with message and session details
        provider: AI provider instance (injected by FastAPI)

    Returns:
        ChatResponse with the AI's reply and metadata

    Raises:
        HTTPException: 500 error if AI provider fails

    Example:
        Request:
            POST /chat/send
            {
                "message": "What is async/await in Python?",
                "session_id": "user-123-session-1",
                "temperature": 0.7,
                "max_tokens": 500
            }

        Response:
            200 OK
            {
                "response": "Async/await is a Python feature for...",
                "model": "claude-3-5-sonnet-20241022",
                "session_id": "user-123-session-1",
                "usage": {
                    "input_tokens": 15,
                    "output_tokens": 120,
                    "total_tokens": 135
                }
            }

    Note (Phase 2):
        In Phase 2, we'll retrieve conversation history for the session_id
        and include it in the context:

        # Get conversation history
        context = await memory.get_messages(request.session_id)
        messages = context + [ChatMessage(role="user", content=request.message)]

    Note (Phase 3):
        In Phase 3, we'll save the conversation to the database:

        # Save to database
        await conversation_repo.save_message(
            session_id=request.session_id,
            role="user",
            content=request.message
        )
    """
    try:
        # Phase 1: Simple request/response - no conversation history
        # Just send the user's message directly to the AI
        messages = [
            ChatMessage(
                role="user",
                content=request.message,
            )
        ]

        # Call the AI provider
        ai_response = await provider.chat(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        # Convert to API response format
        return ChatResponse(
            response=ai_response.content,
            model=ai_response.model,
            session_id=request.session_id,
            usage=TokenUsageResponse(
                input_tokens=ai_response.usage.input_tokens,
                output_tokens=ai_response.usage.output_tokens,
                total_tokens=ai_response.usage.total_tokens,
            ),
        )

    except Exception as e:
        # Log the error (in production, use proper logging)
        print(f"Error in chat endpoint: {type(e).__name__}: {e}")

        # Return 500 error to client
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI provider error: {str(e)}",
        ) from e
