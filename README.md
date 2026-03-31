# AI Chatbot Personal Assistant

A learning-focused project to build a production-quality AI chatbot with provider abstraction, memory systems, persistent storage, and modern Python architecture.

## Quick Start

```bash
# Install dependencies
poetry install

# Apply database migrations
poetry run alembic upgrade head

# Start the API server
poetry run uvicorn chatbot.main:app --reload

# In another terminal, run the CLI
poetry run python -m cli.main

# Run tests
poetry run pytest
```

**API Documentation**: http://localhost:8000/docs

## Project Goals

- **Educational**: Deep understanding of modern AI application architecture
- **Practical**: Working chatbot with conversational memory and persistent storage
- **Future-proof**: Provider abstraction for swapping between Claude, OpenAI, or local models
- **Progressive**: Multi-phase development approach focusing on learning concepts

## Tech Stack

- **Python 3.12**: Recommended version (3.11-3.13 supported)
- **FastAPI**: Modern async web framework
- **Anthropic Claude**: Primary AI provider (`claude-sonnet-4-6`)
- **Poetry**: Dependency management
- **SQLAlchemy 2.0**: Async ORM with SQLite (dev) or PostgreSQL (production)
- **Alembic**: Database migrations
- **Rich + Prompt Toolkit**: Beautiful CLI interface

## Project Structure

```
ai-playground/
├── src/chatbot/          # Main application package
│   ├── api/             # FastAPI routes and models
│   ├── core/            # Business logic (ConversationService)
│   ├── providers/       # AI provider abstraction
│   ├── memory/          # Memory systems (ShortTermMemory, MemoryManager)
│   ├── storage/         # Data persistence (SQLAlchemy, repositories)
│   ├── config.py        # Type-safe settings with Pydantic
│   └── main.py          # FastAPI application entry point
├── cli/                 # CLI client with Rich UI
├── tests/               # Test suite (82 tests)
│   ├── unit/           # Unit tests
│   └── integration/    # Integration tests
├── alembic/            # Database migrations
├── docs/               # Documentation
├── TEXTBOOK.md         # Comprehensive learning guide
├── CLAUDE.md           # Project context and roadmap
└── README.md           # This file
```

## Development Phases

### ✅ Phase 1: Foundation (COMPLETE)
- ✅ Project scaffolding with Poetry
- ✅ Provider abstraction with Anthropic Claude
- ✅ Basic FastAPI server with `/health` and `/chat/send` endpoints
- ✅ Beautiful CLI client with Rich formatting
- ✅ Testing framework with pytest
- ✅ Type-safe configuration with Pydantic Settings

**Key Concepts**: Python Protocols, async/await, FastAPI, dependency injection

### ✅ Phase 2: Short-Term Memory (COMPLETE)
- ✅ In-memory conversation context using `collections.deque`
- ✅ Thread-safe session management with `asyncio.Lock`
- ✅ Multi-turn conversations with context
- ✅ ConversationService orchestration layer
- ✅ Token counting and context window management
- ✅ Enhanced CLI with `/new` command

**Key Concepts**: deque, asyncio.Lock, session management, prompt-injected memory

### ✅ Phase 3: Persistent Storage (COMPLETE)
- ✅ SQLAlchemy 2.0 async ORM
- ✅ SQLite database (local development)
- ✅ Repository pattern for data access
- ✅ Save/retrieve conversation history
- ✅ Alembic migrations for schema versioning
- ✅ Two-tier memory architecture (RAM + Database)
- ✅ Connection pooling and async sessions
- ✅ FastAPI lifecycle integration (startup/shutdown)

**Key Concepts**: ORM, repository pattern, database migrations, two-tier memory

### ✅ Phase 3.5: Warm Start (COMPLETE)
- ✅ Intelligent database-to-RAM loading on first access after restart
- ✅ Lazy loading (only when session is accessed, not all sessions)
- ✅ Respects context limits (loads most recent N messages)
- ✅ CLI session persistence (conversations survive CLI restarts)
- ✅ Observability with warm start logging and session stats
- ✅ Chronological order preservation with efficient queries

**Key Concepts**: Cache warming, lazy loading, cache-aside pattern, observability

### 🔜 Phase 4: Semantic Memory (NEXT)
- ChromaDB vector database integration
- Embedding generation for messages
- Semantic search across conversations
- Intelligent context retrieval ("We talked about this before")
- Cross-session knowledge discovery

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
- Rate limiting

## Setup

### Prerequisites

- **Python 3.12** (recommended) or 3.11-3.13
  - Python 3.14+ not currently supported (library compatibility issues)
  - Install via pyenv: `pyenv install 3.12.0`
- **Poetry**: `curl -sSL https://install.python-poetry.org | python3 -`

### Installation

1. Clone the repository and navigate to the project directory

2. Set Python version (if using pyenv):
   ```bash
   pyenv install 3.12.0
   cd /path/to/ai-playground
   poetry env use 3.12
   ```

3. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

4. Edit `.env` and add your Anthropic API key:
   ```env
   ANTHROPIC_API_KEY=your-actual-api-key-here
   DEFAULT_MODEL=claude-sonnet-4-6
   ```

5. Install dependencies:
   ```bash
   poetry install
   ```

6. Run database migrations:
   ```bash
   poetry run alembic upgrade head
   ```

## Usage

### Start the API server

```bash
poetry run uvicorn chatbot.main:app --reload
```

The API will be available at `http://localhost:8000`

**API Endpoints:**
- `GET /` - API info and status
- `GET /health` - Health check
- `POST /chat/send` - Send a chat message
- `GET /docs` - Interactive API documentation (Swagger UI)

### Run the CLI client

```bash
poetry run python -m cli.main
```

**CLI Features:**
- Beautiful Rich terminal UI with Markdown rendering
- Conversation memory (remembers context)
- Session persistence (survives CLI restarts!)
- Commands: `/help`, `/stats`, `/new`, `/clear`, `/quit`
- Command history (Up/Down arrows)

**Session Persistence:**
Your session ID is stored in `~/.cache/ai-chatbot/session_id`. This allows you to:
- Exit the CLI and resume the same conversation later
- Have conversations that survive both API and CLI restarts (thanks to warm start!)
- Use `/new` to start a fresh conversation (creates new session ID)

Each user account gets their own session file (isolated conversations).

### Run tests

```bash
# Run all tests (82 tests)
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run specific test file
poetry run pytest tests/unit/test_providers.py

# Run with coverage
poetry run pytest --cov=chatbot
```

### Database Management

```bash
# Apply migrations (upgrade to latest)
poetry run alembic upgrade head

# Create a new migration (after changing models)
poetry run alembic revision --autogenerate -m "Description of change"

# Rollback one migration
poetry run alembic downgrade -1

# View migration history
poetry run alembic history

# Inspect database directly
sqlite3 chatbot.db
```

## Configuration

All configuration is managed through environment variables (`.env` file):

### Required
- `ANTHROPIC_API_KEY`: Your Anthropic API key

### Optional (with defaults)
- `PROVIDER_TYPE`: AI provider (`anthropic` - default)
- `DEFAULT_MODEL`: Claude model (`claude-sonnet-4-6` - default)
- `DEFAULT_TEMPERATURE`: Response randomness 0.0-1.0 (default: `0.7`)
- `DEFAULT_MAX_TOKENS`: Max tokens in response (default: `1000`)
- `API_HOST`: API server host (default: `0.0.0.0`)
- `API_PORT`: API server port (default: `8000`)
- `API_RELOAD`: Auto-reload on code changes (default: `true`)
- `DATABASE_URL`: Database connection string (default: `sqlite+aiosqlite:///./chatbot.db`)
- `SHORT_TERM_MAX_MESSAGES`: Max messages in RAM (default: `50`)

## Learning Resources

### 📚 Educational Materials

- **[TEXTBOOK.md](TEXTBOOK.md)** - Comprehensive learning guide (3400+ lines!) with detailed explanations of:
  - **Phase 1**: Python Protocols, async/await, FastAPI, provider abstraction
  - **Phase 2**: collections.deque, asyncio.Lock, session management, prompt-injected memory
  - **Phase 3**: SQLAlchemy 2.0 async ORM, repository pattern, Alembic migrations, connection pooling
  - **Phase 3.5**: Warm start pattern, cache warming, lazy loading, cache coherency strategies
  - Real-world examples and code walkthroughs
  - Production patterns and best practices

- **[CLAUDE.md](CLAUDE.md)** - Project context for resuming work:
  - Current architecture and state
  - Design decisions and rationale
  - Phase roadmap and TODOs
  - Common tasks and commands

### Key Learning Outcomes

By completing this project, you'll understand:

**Python Mastery:**
- Protocols for structural typing (duck typing with type safety)
- Async/await for non-blocking I/O
- Type hints and Pydantic validation
- Modern Python patterns (3.11+)

**Architecture Patterns:**
- Provider abstraction for swappable components
- Repository pattern for data access
- Orchestration pattern for business logic
- Dependency injection for testability
- Two-tier memory architecture (RAM + Database)

**Modern Tools:**
- FastAPI for async web APIs with auto-docs
- SQLAlchemy 2.0 for async database operations
- Alembic for database version control
- Poetry for dependency management
- Rich for beautiful terminal UIs
- pytest for testing async code

**AI/LLM Integration:**
- Provider abstraction patterns
- Conversation context management
- Token estimation and limits
- Persistent conversation history
- Intelligent cache warming

**Production Patterns:**
- Multi-tier caching (RAM + Database)
- Lazy vs eager loading trade-offs
- Cache coherency strategies
- Observability and logging
- Database migrations
- Connection pooling

## Development

### Code Quality

This project uses Ruff for linting and formatting:

```bash
# Check code
poetry run ruff check .

# Format code
poetry run ruff format .
```

### Project Statistics

- **Version**: 0.4.0 (Phase 3.5 Complete)
- **Tests**: 82 passing
  - 14 provider/model tests
  - 19 memory system tests
  - 16 conversation service tests (including 5 warm start tests)
  - 6 storage model tests
  - 23 repository tests
  - 4 API tests
- **Lines of Code**: ~3,000 (application)
- **Documentation**: ~3,400 lines (TEXTBOOK.md)

## Current State (Phase 3.5)

✅ **What Works:**
1. Full AI chat functionality with Anthropic Claude
2. Multi-turn conversations with context memory
3. Persistent storage (conversations survive server restarts)
4. Intelligent warm start (loads recent context from database)
5. Beautiful CLI with session persistence
6. Per-user session isolation
7. Token tracking and management
8. Database migrations with Alembic
9. Comprehensive test suite
10. Auto-generated API documentation

🔜 **Coming in Phase 4:**
- Vector embeddings for semantic search
- ChromaDB integration
- "We talked about this before" feature
- Cross-session knowledge retrieval

## Known Issues

- **Deprecation Warnings** (non-blocking):
  - Pydantic `Config` class (should migrate to `ConfigDict`)
  - FastAPI `on_event` (should migrate to lifespan handlers)
  - `datetime.utcnow()` (should use `datetime.now(datetime.UTC)`)

These will be addressed in a future refactoring phase.

## License

MIT License - Educational project for learning purposes

## Acknowledgments

Built as a learning exercise to understand modern AI application architecture, async Python patterns, production-ready code design, and multi-tier caching systems.

Special thanks to:
- **Anthropic** for Claude API
- **FastAPI** for the excellent async framework
- **SQLAlchemy** team for the powerful ORM
- **Rich** for making CLIs beautiful

---

**Ready to learn?** Start with Phase 1 in [TEXTBOOK.md](TEXTBOOK.md) or jump straight in with the Quick Start above!
