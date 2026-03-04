"""
FastAPI application entry point.

This module creates and configures the FastAPI application.
It's the main entry point for running the API server.

To run the server:
    poetry run uvicorn chatbot.main:app --reload

The server will start at http://localhost:8000
Interactive docs available at http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chatbot.api.routes import chat, health
from chatbot.config import get_settings

# Load settings
settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title="AI Chatbot API",
    description="""
    AI Chatbot Personal Assistant API with provider abstraction and memory systems.

    ## Features (Phase 1)
    * **Chat**: Send messages to AI and get responses
    * **Health Check**: Verify API status
    * **Provider Abstraction**: Swappable AI providers (currently: Anthropic Claude)

    ## Coming Soon
    * **Phase 2**: Short-term memory (conversation context)
    * **Phase 3**: Persistent storage (conversation history)
    * **Phase 4**: Semantic memory (intelligent context retrieval)
    * **Phase 5**: Multiple providers (OpenAI, Ollama)
    * **Phase 6**: Streaming responses, advanced features

    ## Authentication
    Currently no authentication required. This is a learning project.
    Production deployments should add proper authentication.
    """,
    version="0.1.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc alternative docs
    openapi_url="/openapi.json",  # OpenAPI schema
)

# CORS middleware - allows requests from different origins
# Important for web UIs running on different ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include routers
app.include_router(health.router)
app.include_router(chat.router)


@app.on_event("startup")
async def startup_event():
    """
    Run on application startup.

    This is a good place to:
    - Initialize database connections (Phase 3)
    - Load ML models
    - Start background tasks
    - Log startup info
    """
    print("=" * 60)
    print("AI Chatbot API starting...")
    print(f"Provider: {settings.provider_type}")
    print(f"Model: {settings.default_model}")
    print(f"Temperature: {settings.default_temperature}")
    print(f"Max Tokens: {settings.default_max_tokens}")
    print("=" * 60)
    print("API running at:")
    print(f"  - http://{settings.api_host}:{settings.api_port}")
    print(f"  - Docs: http://{settings.api_host}:{settings.api_port}/docs")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Run on application shutdown.

    This is a good place to:
    - Close database connections (Phase 3)
    - Save state
    - Cleanup resources
    - Log shutdown info
    """
    print("\nShutting down AI Chatbot API...")
    print("Cleanup complete. Goodbye!")


# Root endpoint - just for fun
@app.get(
    "/",
    tags=["root"],
    summary="Root endpoint",
    description="Welcome message and basic API info",
)
async def root():
    """
    Root endpoint with welcome message.

    Returns:
        dict: Welcome message and useful links

    Example:
        >>> # HTTP GET /
        >>> {
        ...     "message": "AI Chatbot API",
        ...     "version": "0.1.0",
        ...     "docs": "/docs"
        ... }
    """
    return {
        "message": "AI Chatbot API - Phase 1: Foundation",
        "version": "0.1.0",
        "provider": settings.provider_type,
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "chat": "/chat/send",
        },
    }


# For development: allow running directly
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "chatbot.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
