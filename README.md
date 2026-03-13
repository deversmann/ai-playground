# AI Chatbot Personal Assistant

A learning-focused project to build a production-quality AI chatbot with provider abstraction, memory systems, and modern Python architecture.

## Quick Start

```bash
# Install dependencies
poetry install

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
- **Practical**: Working chatbot with conversational abilities and persistent memory
- **Future-proof**: Provider abstraction for swapping between Claude, OpenAI, or local models
- **Progressive**: Multi-phase development approach

## Tech Stack

- **FastAPI**: Modern async web framework
- **Python 3.11+**: Latest Python features with type hints
- **Anthropic Claude**: Primary AI provider (swappable)
- **Poetry**: Dependency management
- **SQLAlchemy 2.0**: Async ORM (Phase 3+)
- **ChromaDB**: Vector database for semantic memory (Phase 4+)

## Project Structure

```
ai-chatbot/
├── src/chatbot/          # Main application package
│   ├── api/             # FastAPI routes and models
│   ├── core/            # Business logic
│   ├── providers/       # AI provider abstraction
│   ├── memory/          # Memory systems (Phase 2+)
│   ├── storage/         # Data persistence (Phase 3+)
│   └── utils/           # Shared utilities
├── cli/                 # CLI client
├── tests/               # Test suite
├── scripts/             # Utility scripts
└── docs/                # Documentation

```

## Development Phases

### ✅ Phase 1: Foundation (COMPLETE)
- ✅ Project scaffolding with Poetry
- ✅ Provider abstraction with Anthropic Claude
- ✅ Basic FastAPI server with `/health` and `/chat/send` endpoints
- ✅ Beautiful CLI client with Rich formatting
- ✅ Testing framework with pytest
- ✅ Type-safe configuration with Pydantic Settings

### ✅ Phase 2: Short-Term Memory (COMPLETE)
- ✅ In-memory conversation context using `collections.deque`
- ✅ Thread-safe session management with `asyncio.Lock`
- ✅ Multi-turn conversations with context
- ✅ ConversationService orchestration layer
- ✅ Token counting and context window management
- ✅ Enhanced CLI with `/new` command

### Phase 3: Persistent Storage
- SQLAlchemy ORM with SQLite
- Save/retrieve conversation history
- Repository pattern

### Phase 3: Persistent Storage
- SQLAlchemy ORM with SQLite
- Save/retrieve conversation history
- Repository pattern

### Phase 4: Semantic Memory
- ChromaDB vector database
- Embedding-based retrieval
- Intelligent context selection

### Phase 5: Multiple Providers
- OpenAI provider implementation
- Ollama (local models) support
- Runtime provider switching

### Phase 6: Advanced Features
- Streaming responses
- User preference learning
- Cost tracking
- Web UI (optional)

## Setup

### Prerequisites

- Python 3.11 or higher
- Poetry (installed via `curl -sSL https://install.python-poetry.org | python3 -`)

### Installation

1. Clone the repository and navigate to the project directory

2. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and add your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your-actual-api-key-here
   ```

4. Install dependencies:
   ```bash
   poetry install
   ```

5. Activate the virtual environment:
   ```bash
   poetry shell
   ```

## Usage

### Start the API server

```bash
poetry run uvicorn chatbot.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

Interactive API docs (Swagger UI): `http://localhost:8000/docs`

### Run the CLI client

```bash
poetry run python -m cli.main
```

### Run tests

```bash
poetry run pytest
```

## Configuration

All configuration is managed through environment variables (`.env` file):

- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)
- `API_HOST`: API server host (default: 0.0.0.0)
- `API_PORT`: API server port (default: 8000)
- `DEFAULT_MODEL`: Claude model to use (default: claude-sonnet-4-5)
- `DEFAULT_TEMPERATURE`: Response randomness 0.0-1.0 (default: 0.7)

## Learning Resources

### 📚 Educational Materials

- **[TEXTBOOK.md](TEXTBOOK.md)** - Comprehensive learning guide with detailed explanations of:
  - Python Protocols and structural typing
  - Async/await and FastAPI
  - Provider abstraction patterns
  - Configuration management with Pydantic
  - Testing strategies for async applications
  - **Updated after each phase with new concepts**

- **[CLAUDE.md](CLAUDE.md)** - Project context for continuing work:
  - Current state and architecture
  - Design decisions and rationale
  - Phase roadmap
  - Common tasks and patterns

### Key Concepts Covered

**Phase 1: Foundation**
- **Python Protocols**: Structural typing without inheritance
- **Async/await**: Non-blocking I/O for performance
- **FastAPI**: Modern async web framework with auto-docs
- **Dependency Injection**: Clean, testable architecture
- **Provider Abstraction**: Swappable AI providers (Anthropic ↔ OpenAI ↔ Ollama)
- **Type Safety**: Full type hints with Pydantic validation
- **Configuration Management**: Type-safe settings from environment variables

**Phase 2: Short-Term Memory**
- **collections.deque**: Fixed-size FIFO queues for conversation history
- **asyncio.Lock**: Thread-safe async operations
- **Session Management**: Multi-user conversation isolation
- **Prompt-Injected Memory**: Including context in AI requests
- **Orchestration Pattern**: Service layer for business logic
- **Token Estimation**: Context window management

## Development

### Code Quality

This project uses Ruff for linting and formatting:

```bash
# Check code
poetry run ruff check .

# Format code
poetry run ruff format .
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=chatbot

# Run specific test file
poetry run pytest tests/unit/test_providers.py
```

## License

MIT License - Educational project for learning purposes

## Acknowledgments

Built as a learning exercise to understand modern AI application architecture, async Python patterns, and production-ready code design.
