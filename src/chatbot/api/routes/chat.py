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

from chatbot.core import ConversationService
from chatbot.storage import ConversationRepository
from ..dependencies import get_conversation_repository, get_conversation_service
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
    service: ConversationService = Depends(get_conversation_service),
    repository: ConversationRepository = Depends(get_conversation_repository),
) -> ChatResponse:
    """
    Send a message to the AI and get a response with conversation context.

    Phase 2: This endpoint now maintains conversation history! Each message
    is sent with the full conversation context, enabling multi-turn
    conversations where the AI remembers what was said before.

    Args:
        request: Chat request with message and session details
        service: Conversation service (injected by FastAPI)

    Returns:
        ChatResponse with the AI's reply and metadata

    Raises:
        HTTPException: 500 error if AI provider fails

    Example:
        Request 1:
            POST /chat/send
            {
                "message": "What's the capital of France?",
                "session_id": "user-123-session-1",
                "temperature": 0.7
            }

        Response 1:
            {
                "response": "The capital of France is Paris.",
                "model": "claude-sonnet-4-5",
                "session_id": "user-123-session-1",
                "usage": {...}
            }

        Request 2 (same session):
            POST /chat/send
            {
                "message": "What's the population?",
                "session_id": "user-123-session-1"
            }

        Response 2:
            {
                "response": "Paris has approximately 2.2 million people...",
                ...
            }

        Notice the AI knows "What's the population?" refers to Paris!

    How It Works (Phase 2):
        1. Service retrieves conversation history for session_id
        2. User's new message is added to context
        3. Full conversation sent to AI provider
        4. AI's response includes context from previous messages
        5. Both user message and AI response saved to memory

    Note (Phase 3):
        In Phase 3, we'll also save to database for persistence:
        - Conversations survive server restarts
        - Can retrieve historical conversations
        - Can analyze conversation patterns

    Note (Phase 4):
        In Phase 4, we'll add semantic search:
        - Find relevant past conversations
        - Inject related context from other sessions
        - Smart context management for better responses
    """
    try:
        # Phase 3: Conversation service handles RAM + Database!
        # It manages in-memory history, calls provider, stores in RAM,
        # and persists to database for permanent storage
        ai_response = await service.send_message(
            session_id=request.session_id,
            user_message=request.message,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            repository=repository,  # Phase 3: Database persistence
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
