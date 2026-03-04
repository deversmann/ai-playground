# Project Context for Claude

This file provides context for continuing this project in future Claude Code sessions.

---

## Project Overview

**Name**: AI Chatbot Personal Assistant
**Purpose**: Learning-focused project to build a production-quality AI chatbot from scratch
**Current Phase**: Phase 1 Complete ✅
**Next Phase**: Phase 2 - Short-Term Memory

### User Background
- Has coding background
- Learning focus: wants to understand WHY decisions are made, not just WHAT to build
- Prefers **explain first, then implement** approach
- Special interest in: FastAPI/async patterns, vector databases & embeddings
- Uses pyenv virtualenv, but we're using Poetry's automatic venv management

### Development Preferences
- **Container Runtime**: Prefers Podman over Docker (from global CLAUDE.md)
- **Virtual Environment**: Poetry's automatic management (not manual pyenv virtualenv)
- **Pace**: One phase per week for deep learning
- **Learning Style**: Explanations before implementation, inline comments, thorough concept discussions

---

## Project Architecture

### Core Design Principles

1. **Provider Abstraction**: Python Protocol-based interface for swappable AI providers
2. **Clean Architecture**: Separated concerns (api/core/providers/storage)
3. **Type Safety**: Full type hints, Pydantic validation
4. **Async-First**: FastAPI + async/await throughout
5. **Educational**: Code is heavily documented with explanations

### Technology Stack

- **Language**: Python 3.11+
- **Web Framework**: FastAPI (async REST API)
- **AI Provider**: Anthropic Claude (currently `claude-sonnet-4-5`)
- **Dependency Management**: Poetry
- **Configuration**: Pydantic Settings with .env
- **CLI**: Rich + Prompt Toolkit
- **HTTP Client**: httpx (async)
- **Testing**: pytest with pytest-asyncio

### Project Structure

```
ai-playground/
├── src/chatbot/           # Main API application
│   ├── config.py         # Type-safe settings (Pydantic)
│   ├── main.py           # FastAPI app entry point
│   ├── api/              # REST API layer
│   │   ├── routes/       # chat.py, health.py
│   │   ├── models.py     # Pydantic request/response models
│   │   └── dependencies.py  # Dependency injection
│   ├── providers/        # AI provider abstraction
│   │   ├── base.py       # Protocol definition
│   │   ├── models.py     # Shared data models
│   │   ├── anthropic.py  # Anthropic implementation
│   │   └── factory.py    # Provider factory
│   ├── core/             # Business logic (Phase 2+)
│   ├── memory/           # Memory systems (Phase 2+)
│   └── storage/          # Database layer (Phase 3+)
├── cli/                   # CLI client
│   ├── main.py           # Entry point
│   ├── client.py         # HTTP client
│   └── interface.py      # Interactive UI with Rich
├── tests/                 # Test suite
│   ├── conftest.py       # Shared fixtures
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── pyproject.toml        # Poetry dependencies
├── .env                  # Environment configuration
├── README.md             # Project documentation
├── TEXTBOOK.md           # Learning materials
└── CLAUDE.md             # This file
```

---

## Current State (Phase 1 Complete)

### What Works ✅

1. **Provider Abstraction Layer**
   - Protocol-based `AIProvider` interface
   - `AnthropicProvider` implementation
   - Unified `ChatMessage`, `ChatResponse`, `TokenUsage` models
   - Factory pattern for provider creation

2. **FastAPI REST API**
   - `GET /health` - Health check
   - `POST /chat/send` - Chat endpoint
   - `GET /` - API info
   - Auto-generated docs at `/docs`
   - CORS enabled
   - Dependency injection for providers

3. **CLI Client**
   - Beautiful Rich terminal UI
   - Markdown rendering for AI responses
   - Commands: `/help`, `/stats`, `/clear`, `/quit`
   - Token usage tracking
   - Command history (Up/Down arrows)

4. **Configuration**
   - Type-safe Pydantic Settings
   - `.env` file loading
   - Validation with helpful errors

5. **Testing**
   - Unit tests for models (14 tests passing)
   - Integration tests for API
   - Mock provider fixtures
   - pytest with async support

### Known Issues / Technical Debt

1. **Integration Test**: One test fails due to dependency mocking complexity (not critical)
2. **Deprecation Warnings**:
   - Pydantic `Config` class (should migrate to `ConfigDict`)
   - FastAPI `on_event` (should migrate to lifespan handlers)
3. **Model Name**: Currently using `claude-sonnet-4-5` (works with current API key)

### Environment Configuration

**Important `.env` settings:**
```bash
PROVIDER_TYPE=anthropic
ANTHROPIC_API_KEY=sk-ant-api03-...  # User has valid key
DEFAULT_MODEL=claude-sonnet-4-5      # Current working model
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=1000
API_PORT=8000
```

---

## How to Resume Work

### Quick Start Commands

```bash
# Start API server
poetry run uvicorn chatbot.main:app --reload

# Run CLI client
poetry run python -m cli.main

# Run tests
poetry run pytest

# Run tests with verbose output
poetry run pytest -v
```

### Before Starting New Phase

1. **Review TEXTBOOK.md** for concepts learned
2. **Check plan file** at `~/.claude/plans/polymorphic-booping-babbage.md`
3. **Verify tests pass**: `poetry run pytest`
4. **Confirm API works**: Start server and test `/health` endpoint

---

## Phase Roadmap

### ✅ Phase 1: Foundation (COMPLETE)
- Project scaffolding with Poetry
- Provider abstraction with Anthropic Claude
- Basic FastAPI server with chat endpoint
- Simple CLI client with Rich
- Testing framework

### 🔜 Phase 2: Short-Term Memory (NEXT)
- In-memory conversation context using `collections.deque`
- Session management for multiple conversations
- Token counting to stay within context windows
- Multi-turn conversations (Claude remembers context)
- `asyncio.Lock` for thread-safe session storage

**Key Files to Create**:
- `src/chatbot/memory/short_term.py` - Deque-based memory
- `src/chatbot/memory/manager.py` - Memory orchestration
- `src/chatbot/core/conversation.py` - Conversation service

### Phase 3: Persistent Storage
- SQLAlchemy 2.0 async ORM
- SQLite database (local development)
- Repository pattern for data access
- Save/retrieve conversation history
- Alembic migrations

### Phase 4: Semantic Memory
- ChromaDB vector database integration
- Embedding generation for messages
- Semantic search across conversations
- Intelligent context retrieval
- Memory manager coordinating all memory types

### Phase 5: Multiple Providers
- OpenAI provider implementation
- Ollama provider (local models)
- Runtime provider switching
- Model comparison features

### Phase 6: Advanced Features
- Streaming responses (Server-Sent Events)
- User preference learning
- Cost tracking and monitoring
- Web UI (optional)
- Rate limiting with semaphores

---

## Key Design Decisions (Context for Future Work)

### Why Protocol over ABC?
- Structural typing (duck typing with type checking)
- No explicit inheritance required
- More Pythonic and flexible
- Easy to add third-party providers

### Why FastAPI over Flask?
- Built for async/await
- Automatic OpenAPI documentation
- Better performance with async
- Native Pydantic integration

### Why Custom Abstraction vs LangChain?
- LangChain abstracts too much for learning
- Building our own teaches interface design
- Can add LangChain later as one provider option
- Full control over architecture

### Why SQLite → PostgreSQL?
- SQLite: zero setup, perfect for learning
- PostgreSQL: production-ready migration path
- SQLAlchemy makes switching transparent

---

## Common Tasks

### Adding a New API Endpoint

1. Create route in `src/chatbot/api/routes/`
2. Define Pydantic models in `src/chatbot/api/models.py`
3. Add dependencies if needed in `dependencies.py`
4. Include router in `main.py`
5. Write tests in `tests/integration/`

### Adding a New Provider

1. Implement `AIProvider` protocol in `src/chatbot/providers/`
2. Add conversion methods for provider's API format
3. Update factory in `factory.py`
4. Add provider-specific config in `config.py`
5. Write unit tests

### Adding Configuration

1. Add field to `Settings` class in `config.py`
2. Add to `.env.example`
3. Document in README.md
4. Use via `get_settings()` dependency

---

## Testing Strategy

### Unit Tests
- Focus: Individual functions/classes
- No external dependencies
- Fast execution
- Located in `tests/unit/`

### Integration Tests
- Focus: API endpoints with mocked dependencies
- Test FastAPI routes
- Validate request/response formats
- Located in `tests/integration/`

### E2E Tests (Future)
- Focus: Full system with real AI provider
- Expensive (uses API credits)
- Run sparingly
- Optional for learning project

---

## Important Notes for Future Sessions

1. **Always explain concepts first** before implementing (user preference)
2. **User has coding background** - can handle technical depth
3. **Learning is the goal** - prioritize understanding over speed
4. **Keep detailed comments** - code should be self-documenting
5. **Update TEXTBOOK.md** after each phase with new concepts
6. **Use TodoWrite** to track multi-step tasks
7. **Model name**: `claude-sonnet-4-5` works with user's API key

---

## Questions to Ask When Resuming

If starting Phase 2:
1. "Ready to start Phase 2 (Short-Term Memory)?"
2. "Any questions about Phase 1 concepts before we continue?"
3. "Would you like me to explain deque-based memory before we implement?"

If user asks to modify Phase 1:
1. "What would you like to change or improve?"
2. "Any concepts from TEXTBOOK.md you'd like me to clarify?"

---

## Resources

- **Anthropic API Docs**: https://docs.anthropic.com/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Pydantic Docs**: https://docs.pydantic.dev/
- **Poetry Docs**: https://python-poetry.org/docs/

---

*Last Updated: Phase 1 Complete - 2026-03-04*
