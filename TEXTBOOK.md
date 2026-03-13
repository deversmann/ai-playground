# AI Chatbot Development Textbook

A comprehensive guide to building a production-quality AI chatbot with modern Python architecture.

**Project Goal**: Learn modern AI application development through hands-on implementation of a chatbot with provider abstraction, memory systems, and clean architecture.

---

## Table of Contents

- [Phase 1: Foundation](#phase-1-foundation)
  - [Python Protocols](#python-protocols)
  - [FastAPI and Async/Await](#fastapi-and-asyncawait)
  - [Provider Abstraction Pattern](#provider-abstraction-pattern)
  - [Configuration Management](#configuration-management)
  - [Testing Strategies](#testing-strategies)

- [Phase 2: Short-Term Memory](#phase-2-short-term-memory)
  - [collections.deque - Fixed-Size Queues](#collectionsdeque---fixed-size-queues)
  - [asyncio.Lock - Thread Safety in Async Code](#asynciolock---thread-safety-in-async-code)
  - [Session Management](#session-management)
  - [Prompt-Injected Memory](#prompt-injected-memory)
  - [Orchestration Pattern](#orchestration-pattern)

---

# Phase 1: Foundation

## Python Protocols

### What is a Protocol?

A **Protocol** is Python's way of defining an interface using **structural typing** (also called "duck typing with type checking"). Introduced in Python 3.8 via PEP 544.

### Traditional Approaches vs. Protocol

#### ❌ Approach 1: Duck Typing (No Type Checking)
```python
class Dog:
    def speak(self):
        return "Woof!"

class Cat:
    def speak(self):
        return "Meow!"

def make_sound(animal):  # No type hints - anything goes!
    return animal.speak()

make_sound(Dog())  # Works
make_sound(Cat())  # Works
make_sound("string")  # Runtime error! No .speak() method
```

**Problem**: No type checking at all. Errors only discovered at runtime.

#### ⚠️ Approach 2: Abstract Base Classes (ABC)
```python
from abc import ABC, abstractmethod

class Animal(ABC):  # Define abstract base class
    @abstractmethod
    def speak(self) -> str:
        pass

class Dog(Animal):  # MUST explicitly inherit
    def speak(self) -> str:
        return "Woof!"

class Cat(Animal):  # MUST explicitly inherit
    def speak(self) -> str:
        return "Meow!"

def make_sound(animal: Animal) -> str:
    return animal.speak()
```

**Problem**: Requires **explicit inheritance**. Third-party classes that have the right methods but don't inherit won't work.

```python
class Bird:  # Doesn't inherit from Animal
    def speak(self) -> str:
        return "Tweet!"

make_sound(Bird())  # Type checker ERROR! Bird is not an Animal subclass
```

#### ✅ Approach 3: Protocol (Structural Typing)
```python
from typing import Protocol

class Animal(Protocol):  # Define protocol
    def speak(self) -> str:
        ...  # Just signature, no implementation

class Dog:  # NO inheritance needed!
    def speak(self) -> str:
        return "Woof!"

class Cat:  # NO inheritance needed!
    def speak(self) -> str:
        return "Meow!"

class Bird:  # Works even if defined elsewhere!
    def speak(self) -> str:
        return "Tweet!"

def make_sound(animal: Animal) -> str:
    return animal.speak()

make_sound(Dog())   # ✅ Type checker happy
make_sound(Cat())   # ✅ Type checker happy
make_sound(Bird())  # ✅ Type checker happy - it has speak()!
```

**Benefits**:
- ✅ Type checking at development time
- ✅ No inheritance required
- ✅ Works with third-party classes
- ✅ More Pythonic ("if it quacks like a duck...")

### Real-World Example: AI Provider Protocol

```python
from typing import Protocol
from dataclasses import dataclass

@dataclass
class ChatMessage:
    role: str
    content: str

@dataclass
class ChatResponse:
    content: str
    model: str
    usage: dict

# Protocol defines the CONTRACT
class AIProvider(Protocol):
    async def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> ChatResponse:
        """All providers must implement this method"""
        ...

# Anthropic implementation - NO inheritance!
class AnthropicProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> ChatResponse:
        # Real implementation here
        ...

# OpenAI implementation - NO inheritance!
class OpenAIProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def chat(
        self,
        messages: list[ChatMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> ChatResponse:
        # Real implementation here
        ...

# Type-safe function that works with ANY provider
async def send_message(
    provider: AIProvider,  # Type hint: anything matching the protocol
    user_message: str
) -> str:
    messages = [ChatMessage(role="user", content=user_message)]
    response = await provider.chat(messages)
    return response.content

# Both work seamlessly!
anthropic = AnthropicProvider(api_key="...")
openai = OpenAIProvider(api_key="...")

await send_message(anthropic, "Hello")  # ✅ Works
await send_message(openai, "Hello")     # ✅ Works
```

### Key Takeaways

1. **Protocol = Interface**: Defines what methods a class must have
2. **Structural typing**: "If it looks like a duck and quacks like a duck, it's a duck"
3. **No inheritance needed**: Classes automatically match if they have the right methods
4. **Type checking**: Catches errors during development, not runtime
5. **Flexibility**: Perfect for designing swappable components

---

## FastAPI and Async/Await

### Part 1: Async/Await in Python

#### The Problem: Blocking I/O

In traditional synchronous code, I/O operations **block** execution:

```python
import time

def fetch_user(user_id):
    print(f"Fetching user {user_id}...")
    time.sleep(2)  # Simulates API call delay
    print(f"Got user {user_id}")
    return {"id": user_id, "name": f"User {user_id}"}

def fetch_posts(user_id):
    print(f"Fetching posts for {user_id}...")
    time.sleep(2)  # Simulates API call delay
    print(f"Got posts for {user_id}")
    return [{"post": 1}, {"post": 2}]

# Synchronous execution - SLOW!
start = time.time()
user = fetch_user(1)       # Waits 2 seconds
posts = fetch_posts(1)     # Waits another 2 seconds
print(f"Total time: {time.time() - start:.2f}s")  # ~4 seconds!
```

**Output:**
```
Fetching user 1...
Got user 1
Fetching posts for 1...
Got posts for 1
Total time: 4.00s
```

**Problem**: While waiting for the API response, the entire program is frozen.

#### The Solution: Async/Await

```python
import asyncio

async def fetch_user(user_id):
    print(f"Fetching user {user_id}...")
    await asyncio.sleep(2)  # Simulates API call - NON-BLOCKING!
    print(f"Got user {user_id}")
    return {"id": user_id, "name": f"User {user_id}"}

async def fetch_posts(user_id):
    print(f"Fetching posts for {user_id}...")
    await asyncio.sleep(2)  # Simulates API call - NON-BLOCKING!
    print(f"Got posts for {user_id}")
    return [{"post": 1}, {"post": 2}]

# Async execution - FAST!
async def main():
    start = time.time()

    # Run both concurrently!
    user, posts = await asyncio.gather(
        fetch_user(1),
        fetch_posts(1)
    )

    print(f"Total time: {time.time() - start:.2f}s")  # ~2 seconds!

asyncio.run(main())
```

**Output:**
```
Fetching user 1...
Fetching posts for 1...
Got user 1
Got posts for 1
Total time: 2.00s
```

#### Key Concepts

**1. `async def` - Defines a Coroutine**

```python
async def my_function():
    # This is a coroutine, not a regular function
    return "Hello"
```

- **Coroutine**: A function that can pause and resume execution
- Can only call coroutines with `await`
- Returns a coroutine object, not the result directly

**2. `await` - Pause and Resume**

```python
async def example():
    result = await some_async_function()  # Pause here, let other code run
    # Resumes when some_async_function() completes
    print(result)
```

- **`await`**: "Pause this coroutine until this operation completes"
- While paused, the event loop can run other tasks
- Can only use `await` inside `async def` functions

**3. Event Loop - The Orchestrator**

```python
import asyncio

# The event loop manages all async tasks
asyncio.run(main())  # Creates loop, runs main(), closes loop
```

Think of the event loop like a task scheduler:
- Keeps track of all async tasks
- When one task is waiting (I/O), runs another task
- Switches between tasks efficiently

#### Real-World Example: Calling Claude API

```python
import httpx

# ❌ Synchronous - blocks the entire program
def call_claude_sync(message: str) -> str:
    response = httpx.post(  # Program freezes here for 1-2 seconds
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": "..."},
        json={"messages": [{"role": "user", "content": message}]}
    )
    return response.json()

# ✅ Async - allows other work to happen
async def call_claude_async(message: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(  # Yields control while waiting
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": "..."},
            json={"messages": [{"role": "user", "content": message}]}
        )
        return response.json()
```

**Why this matters**:
- API calls to Claude take 1-2 seconds
- With async, the server can handle other requests while waiting
- One server can handle hundreds of concurrent users

### Part 2: FastAPI - Modern Async Web Framework

#### Why FastAPI?

FastAPI is built specifically for modern Python with async/await.

**Flask (Synchronous)**
```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/chat', methods=['POST'])
def chat():
    message = request.json['message']

    # Blocks the entire server during API call!
    response = call_claude_sync(message)

    return {"response": response}

# Can only handle ONE request at a time efficiently
```

**FastAPI (Async)**
```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

@app.post('/chat')
async def chat(request: ChatRequest):
    # Server can handle other requests while waiting!
    response = await call_claude_async(request.message)

    return {"response": response}

# Can handle HUNDREDS of concurrent requests
```

#### FastAPI Key Features

**1. Automatic Type Validation with Pydantic**

```python
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: str
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)

@app.post('/chat')
async def chat(request: ChatRequest):
    # FastAPI automatically:
    # 1. Validates JSON structure
    # 2. Checks types (message is str, temperature is float)
    # 3. Validates constraints (temperature between 0-1)
    # 4. Returns 422 error if invalid

    return {"message": request.message}
```

**2. Dependency Injection**

```python
from fastapi import Depends

# Dependency: gets or creates provider
def get_provider() -> AIProvider:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    return AnthropicProvider(api_key=api_key)

# Injected automatically!
@app.post('/chat')
async def chat(
    request: ChatRequest,
    provider: AIProvider = Depends(get_provider)  # Automatic injection
):
    response = await provider.chat([...])
    return {"response": response.content}
```

**Benefits**:
- **Separation of concerns**: Route doesn't create provider
- **Testability**: Easy to mock dependencies
- **Reusability**: Same dependency in multiple routes

**3. Automatic OpenAPI Documentation**

```python
@app.post('/chat',
    summary="Send a chat message",
    description="Send a message to the AI and get a response",
    response_description="The AI's response"
)
async def chat(request: ChatRequest) -> ChatResponse:
    ...
```

Visit `http://localhost:8000/docs` and you get:
- Interactive API playground
- Request/response schemas
- Try-it-out functionality
- Automatically updated when code changes

**4. Type Hints for Editor Support**

```python
@app.post('/chat')
async def chat(request: ChatRequest) -> ChatResponse:
    # Your editor knows:
    # - request.message is a string
    # - request.session_id is a string
    # - Return type must match ChatResponse

    # Autocomplete works perfectly!
    message_length = len(request.message)  # ✅ Editor suggests .message
```

### How FastAPI Handles Requests

1. **Request comes in**: `POST /chat`
2. **Parse JSON**: Convert to Python dict
3. **Validate**: Check against `ChatRequest` model
4. **Inject dependencies**: Call `get_provider()`, pass result
5. **Execute handler**: Run `chat()` function
6. **Validate response**: Check against `ChatResponse` model
7. **Serialize**: Convert to JSON
8. **Return**: Send to client

All of this happens **automatically**!

### Key Takeaways

**Async/Await**:
1. **Purpose**: Non-blocking I/O for better performance
2. **`async def`**: Defines a coroutine function
3. **`await`**: Pauses execution, allows other code to run
4. **Event loop**: Orchestrates all async tasks
5. **When to use**: I/O-bound operations (API calls, database, file I/O)

**FastAPI**:
1. **Built for async**: Native async/await support
2. **Type validation**: Pydantic models for automatic validation
3. **Dependency injection**: Clean, testable code
4. **Auto documentation**: OpenAPI/Swagger docs for free
5. **Performance**: Can handle many concurrent requests

---

## Async/Await Synchronization

### The Key Insight: Async ≠ Parallel Threads

**Async/await in Python runs in a single thread**, so you have fewer race conditions than with traditional multithreading. However, you still need synchronization at `await` points.

### Synchronization Primitives

**1. asyncio.Lock - Mutual Exclusion**

```python
import asyncio

shared_counter = 0
lock = asyncio.Lock()

async def increment():
    global shared_counter

    async with lock:  # Only one task can be here at a time
        current = shared_counter
        await asyncio.sleep(0.1)  # Even with await, others wait
        shared_counter = current + 1
```

**2. asyncio.Semaphore - Limit Concurrent Access**

```python
# Limit to 2 concurrent API calls
semaphore = asyncio.Semaphore(2)

async def call_api(user_id: int):
    async with semaphore:  # Max 2 at a time
        print(f"Calling API for user {user_id}")
        await asyncio.sleep(1)  # Simulate API call
```

**3. asyncio.Queue - Thread-Safe Queue**

```python
queue = asyncio.Queue(maxsize=10)

async def producer():
    for i in range(5):
        await queue.put(i)
        await asyncio.sleep(0.5)

async def consumer():
    while True:
        item = await queue.get()
        print(f"Consumed: {item}")
        queue.task_done()
```

### When Do You Need Synchronization?

**✅ You NEED synchronization when:**

1. **Shared mutable state** across async tasks
2. **Resource limits** (API rate limits, connection pools)
3. **Ordered operations** that must happen sequentially

**❌ You DON'T need synchronization when:**

1. **Request-scoped data** (each request has its own data)
2. **Read-only shared data** (immutable or constant)
3. **Database operations** (database handles locking)
4. **Independent async operations** (no shared state)

---

## Provider Abstraction Pattern

### Design Pattern: Protocol + Factory

**Why this pattern?**
- Allows swapping AI providers (Anthropic ↔ OpenAI ↔ Ollama)
- No changes needed in consuming code
- Type-safe with compile-time checking
- Easy to test (mock providers)

### Architecture

```
┌─────────────────────────────────┐
│    Application Code             │
│  (Routes, Services)             │
└────────────┬────────────────────┘
             │ uses
             ▼
┌─────────────────────────────────┐
│    AIProvider Protocol          │
│  + chat(messages) → response    │
│  + stream_chat() → chunks       │
└────────────┬────────────────────┘
             │ implemented by
      ┌──────┴──────┬──────────┐
      ▼             ▼          ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│Anthropic │  │ OpenAI   │  │ Ollama   │
│Provider  │  │ Provider │  │ Provider │
└──────────┘  └──────────┘  └──────────┘
```

### Implementation

**Step 1: Define Unified Data Models**

```python
from dataclasses import dataclass

@dataclass
class ChatMessage:
    role: str  # 'system', 'user', 'assistant'
    content: str

@dataclass
class ChatResponse:
    content: str
    model: str
    usage: TokenUsage
    metadata: dict
```

**Step 2: Define Protocol**

```python
from typing import Protocol, AsyncIterator

class AIProvider(Protocol):
    async def chat(
        self,
        messages: list[ChatMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ChatResponse:
        ...

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        ...
```

**Step 3: Implement Providers**

```python
class AnthropicProvider:
    """Implements AIProvider protocol (no explicit inheritance!)"""

    def __init__(self, api_key: str):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    async def chat(
        self,
        messages: list[ChatMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ChatResponse:
        # 1. Convert our format to Anthropic's format
        anthropic_messages, system = self._convert_to_anthropic(messages)

        # 2. Call Anthropic API
        api_params = {
            "model": "claude-sonnet-4-5",
            "messages": anthropic_messages,
            "temperature": temperature or 0.7,
            "max_tokens": max_tokens or 1000,
        }
        if system:
            api_params["system"] = system

        response = await self.client.messages.create(**api_params)

        # 3. Convert back to our format
        return self._convert_from_anthropic(response)
```

**Step 4: Factory Pattern**

```python
def create_provider(settings: Settings) -> AIProvider:
    """Factory function to create the right provider."""

    if settings.provider_type == "anthropic":
        return AnthropicProvider(
            api_key=settings.anthropic_api_key,
            default_model=settings.default_model
        )
    elif settings.provider_type == "openai":
        return OpenAIProvider(api_key=settings.openai_api_key)
    elif settings.provider_type == "ollama":
        return OllamaProvider(base_url=settings.ollama_base_url)
    else:
        raise ValueError(f"Unknown provider: {settings.provider_type}")
```

### Benefits

1. **Swappable**: Change provider with one config change
2. **Testable**: Easy to create mock providers
3. **Type-safe**: Compile-time checking
4. **Extensible**: Add new providers without changing existing code
5. **Clean**: Consumer code doesn't know about provider details

### Usage in Application

```python
# In FastAPI dependency
def get_ai_provider() -> AIProvider:
    settings = get_settings()
    return create_provider(settings)

# In route
@app.post('/chat')
async def chat(
    request: ChatRequest,
    provider: AIProvider = Depends(get_ai_provider)  # Any provider works!
):
    response = await provider.chat([
        ChatMessage(role="user", content=request.message)
    ])
    return {"response": response.content}
```

---

## Configuration Management

### Pydantic Settings - Type-Safe Configuration

**The Problem with Traditional Config:**

```python
import os

# ❌ Traditional approach - lots of problems
api_key = os.getenv("ANTHROPIC_API_KEY")  # Could be None!
port = os.getenv("API_PORT")  # Returns string "8000", not int
temperature = os.getenv("DEFAULT_TEMPERATURE")  # Returns string "0.7", not float

# Need manual conversion and validation
port = int(port) if port else 8000
temperature = float(temperature) if temperature else 0.7
```

**Pydantic Settings Solution:**

```python
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Type hints + automatic conversion!
    anthropic_api_key: str  # Required - will error if missing
    api_port: int = Field(default=8000, ge=1024, le=65535)
    default_temperature: float = Field(default=0.7, ge=0.0, le=1.0)

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )
```

### Key Features

**1. Type Hints with Validation**

```python
api_port: int = Field(
    default=8000,
    ge=1024,  # >= 1024 (avoid privileged ports)
    le=65535  # <= 65535 (max port number)
)
```

- Automatically converts `"8000"` string to integer `8000`
- Validates the port is in valid range
- Provides helpful error messages if invalid

**2. Literal Types for Enums**

```python
from typing import Literal

provider_type: Literal["anthropic", "openai", "ollama"] = "anthropic"
```

- Only allows these exact three values
- IDE autocomplete suggests valid options
- Type error if you try to use something else

**3. Singleton Pattern with @lru_cache**

```python
from functools import lru_cache

@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_provider_config()
    return settings
```

- Loads settings only once
- Reuses same instance everywhere
- More efficient, guarantees consistency

---

## Testing Strategies

### Testing Pyramid for Async Applications

```
        ╱╲
       ╱  ╲        E2E Tests (Few)
      ╱────╲       - Full system integration
     ╱      ╲      - Slow, comprehensive
    ╱────────╲
   ╱ Integration╲   Integration Tests (Some)
  ╱──────────────╲  - API endpoints with mocks
 ╱                ╲ - Database interactions
╱──────────────────╲
│   Unit Tests      │ Unit Tests (Many)
│    (Fast!)        │ - Individual functions/classes
└────────────────────┘ - No external dependencies
```

### Unit Tests

**Purpose**: Test individual components in isolation

```python
import pytest
from chatbot.providers.models import ChatMessage, TokenUsage

class TestChatMessage:
    """Tests for ChatMessage model."""

    def test_valid_message(self):
        """Test creating a valid message."""
        msg = ChatMessage(role="user", content="Hello!")
        assert msg.role == "user"
        assert msg.content == "Hello!"

    def test_invalid_role(self):
        """Test that invalid roles raise an error."""
        with pytest.raises(ValueError, match="Invalid role"):
            ChatMessage(role="invalid", content="test")
```

### Mock Providers for Testing

```python
@pytest.fixture
def mock_provider():
    """Create a mock AI provider for testing."""

    class MockProvider:
        async def chat(
            self,
            messages: list[ChatMessage],
            **kwargs
        ) -> ChatResponse:
            return ChatResponse(
                content=f"Mock response to: {messages[-1].content}",
                model="mock-model",
                usage=TokenUsage(input_tokens=10, output_tokens=20)
            )

    return MockProvider()
```

### Integration Tests

**Purpose**: Test how components work together

```python
from fastapi.testclient import TestClient

def test_chat_endpoint(client: TestClient, mock_provider):
    """Test the chat endpoint with mocked provider."""
    response = client.post(
        "/chat/send",
        json={
            "message": "Hello!",
            "session_id": "test-123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["session_id"] == "test-123"
```

### Testing Async Code

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test an async function."""
    result = await some_async_function()
    assert result == expected_value
```

**Key Points**:
- Use `@pytest.mark.asyncio` decorator
- Configure `pytest.ini` with `asyncio_mode = "auto"`
- Use `AsyncMock` from `unittest.mock` for async mocks

---

## Project Structure Best Practices

### Clean Architecture

```
src/chatbot/
├── api/              # HTTP layer
│   ├── routes/      # Endpoint handlers
│   ├── models.py    # Request/response models
│   └── dependencies.py
├── core/            # Business logic
│   └── conversation.py
├── providers/       # External integrations
│   ├── base.py     # Protocol definition
│   ├── anthropic.py
│   └── factory.py
├── storage/         # Data persistence
│   ├── models.py   # Database models
│   └── repositories/
└── utils/           # Shared utilities
```

### Separation of Concerns

1. **API Layer**: HTTP-specific code, validation, serialization
2. **Core Layer**: Business logic, orchestration
3. **Providers Layer**: External AI services
4. **Storage Layer**: Database, file system

**Benefits**:
- Easy to test (mock dependencies)
- Easy to change (swap implementations)
- Easy to understand (clear responsibilities)

---

## Key Takeaways - Phase 1

### Python Mastery
- ✅ Protocols for structural typing
- ✅ Async/await for non-blocking I/O
- ✅ Type hints for safety and documentation
- ✅ Dataclasses for clean data models

### Architecture Patterns
- ✅ Provider abstraction for swappable components
- ✅ Factory pattern for object creation
- ✅ Dependency injection for testability
- ✅ Clean architecture with separated concerns

### Modern Tools
- ✅ FastAPI for async web APIs
- ✅ Pydantic for validation and config
- ✅ Poetry for dependency management
- ✅ Rich for beautiful terminal UI
- ✅ pytest for testing

### AI/LLM Integration
- ✅ Provider abstraction patterns
- ✅ Message format conversion
- ✅ Token management
- ✅ Error handling

---

# Phase 2: Short-Term Memory

In Phase 2, we transformed the chatbot from **stateless** (each message independent) to **stateful** (remembers conversation context). We implemented in-memory conversation history that enables multi-turn conversations.

## The Problem: Stateless Conversations

In Phase 1, each request was completely independent:

```python
# Request 1
You: What's the capital of France?
AI: The capital of France is Paris.

# Request 2 - AI has NO memory of previous message
You: What's the population?
AI: I don't know what you're referring to...  ❌
```

The AI couldn't understand "What's the population?" because it had no context.

## The Solution: Conversation Memory

AI models like Claude don't have built-in memory. They process what you give them in each request. The solution is to **include the full conversation history** in every API call.

This is called **prompt-injected memory** - we inject the conversation context into the prompt.

```python
# Request 1
messages = [
    ChatMessage(role="user", content="What's the capital of France?")
]
# AI responds: "Paris"

# Request 2 - Include full conversation history!
messages = [
    ChatMessage(role="user", content="What's the capital of France?"),
    ChatMessage(role="assistant", content="The capital of France is Paris."),
    ChatMessage(role="user", content="What's the population?")
]
# AI responds: "Paris has approximately 2.2 million people..."  ✅
```

The AI sees the full conversation each time, so it knows "the population" refers to Paris!

---

## collections.deque - Fixed-Size Queues

### Why Not Use a List?

You might think: "Just use a Python list to store messages!"

```python
conversation = []  # List approach
conversation.append(msg1)
conversation.append(msg2)
# ... keeps growing forever ...
```

**Problems:**
1. **Unbounded growth**: List grows forever, eventually hitting token limits
2. **Manual management**: You have to manually remove old items
3. **Token limits**: Claude has a 200k token context window - we need to stay within it

### Enter: collections.deque

A **deque** (double-ended queue) is a list-like container that can automatically maintain a fixed size.

```python
from collections import deque

# Create a deque with maximum size of 3
conversation = deque(maxlen=3)

conversation.append("Message 1")  # ["Message 1"]
conversation.append("Message 2")  # ["Message 1", "Message 2"]
conversation.append("Message 3")  # ["Message 1", "Message 2", "Message 3"]
conversation.append("Message 4")  # ["Message 2", "Message 3", "Message 4"]
                                  # ↑ "Message 1" automatically removed!
```

**Key features:**
- **FIFO (First-In-First-Out)**: Oldest items automatically dropped
- **O(1) operations**: Appending and removing from either end is instant
- **Fixed size**: `maxlen` parameter ensures we never exceed limit
- **Built-in**: Part of Python's standard library

### Real-World Example

```python
from collections import deque
from chatbot.providers.models import ChatMessage

class ShortTermMemory:
    def __init__(self, max_messages: int = 50):
        # Deque automatically removes oldest when full
        self._messages = deque(maxlen=max_messages)

    def add_message(self, message: ChatMessage) -> None:
        """Add a message. If at capacity, oldest is auto-removed."""
        self._messages.append(message)

    def get_messages(self) -> list[ChatMessage]:
        """Get all messages in chronological order."""
        return list(self._messages)
```

### Why 50 Messages?

We default to 50 messages (25 user + 25 assistant turns) because:
- Average message: ~100 tokens
- 50 messages × 100 tokens = ~5,000 tokens
- Leaves plenty of room in Claude's 200k token window
- Recent context is most relevant anyway

---

## asyncio.Lock - Thread Safety in Async Code

### The Problem: Race Conditions in Async Code

Even though async/await runs in a **single thread**, it can still have race conditions at `await` points.

```python
# Two requests arrive simultaneously for the same session
# Without locking:

# Request 1 starts
messages = get_messages("session-123")  # Gets [msg1, msg2]
await call_ai(messages)  # ← Pauses here (await point)

# Request 2 starts while Request 1 is waiting
messages = get_messages("session-123")  # Gets same [msg1, msg2]
await call_ai(messages)  # ← Both see the same state!

# Request 1 resumes
add_message("session-123", response1)  # Adds response

# Request 2 resumes
add_message("session-123", response2)  # Adds response

# Result: Conversation order is corrupted! ❌
```

### The Solution: asyncio.Lock

An **asyncio.Lock** ensures only one async task can access shared state at a time.

```python
import asyncio

class MemoryManager:
    def __init__(self):
        self._sessions = {}
        self._locks = {}  # One lock per session

    async def add_message(self, session_id: str, message: ChatMessage):
        # Get or create lock for this session
        if session_id not in self._locks:
            self._locks[session_id] = asyncio.Lock()

        # Only one task can be in this block at a time per session
        async with self._locks[session_id]:
            # Safe! No other task can modify this session right now
            self._sessions[session_id].append(message)
```

### How Locks Work

```python
lock = asyncio.Lock()

# Task 1
async with lock:
    # Task 1 holds the lock
    await do_something()  # Even during await, Task 1 holds lock

# Task 2 (arrives while Task 1 is in the block)
async with lock:  # ← Waits here until Task 1 releases the lock
    await do_something_else()
```

**Key points:**
- **Mutual exclusion**: Only one task can hold the lock at a time
- **Survives await**: Lock held even when awaiting
- **Automatic release**: `async with` ensures lock is released
- **Per-session locking**: Different sessions can run in parallel!

### Why Per-Session Locks?

```python
# Dictionary of locks - one per session
self._locks = {
    "session-1": asyncio.Lock(),
    "session-2": asyncio.Lock(),
    "session-3": asyncio.Lock(),
}

# Multiple sessions can run in parallel ✅
# Same session is serialized ✅
```

This allows:
- User A and User B can chat simultaneously (different sessions)
- User A's two rapid requests are processed in order (same session)

---

## Session Management

### What is a Session?

A **session** is a unique conversation thread. Each session has:
- A unique identifier (`session_id`)
- Its own conversation history
- Independent context from other sessions

### Why Session Management?

Without sessions, all users would share one conversation:

```python
# Without sessions - everyone shares history ❌
User A: My name is Alice
AI: Hello Alice!

User B: What's my name?
AI: Your name is Alice!  ← Wrong! That was User A!
```

With sessions, each conversation is isolated:

```python
# With sessions - separate conversations ✅
# Session: "user-alice-123"
User A: My name is Alice
AI: Hello Alice!

# Session: "user-bob-456"
User B: What's my name?
AI: I don't know your name yet!  ← Correct!
```

### MemoryManager Architecture

```python
class MemoryManager:
    def __init__(self):
        # Dictionary: session_id → ShortTermMemory
        self._sessions = {
            "user-123-session-1": ShortTermMemory(),  # Alice's conversation
            "user-456-session-2": ShortTermMemory(),  # Bob's conversation
        }

        # Dictionary: session_id → asyncio.Lock
        self._locks = {
            "user-123-session-1": asyncio.Lock(),
            "user-456-session-2": asyncio.Lock(),
        }
```

### Session Lifecycle

```python
# Session creation (lazy - created on first message)
await memory_manager.add_message("new-session", msg)
# MemoryManager creates the session automatically

# Active usage
messages = await memory_manager.get_messages("new-session")
stats = await memory_manager.get_session_stats("new-session")

# Clear history (session remains)
await memory_manager.clear_session("new-session")
# Session exists but has no messages

# Delete completely (session removed)
await memory_manager.delete_session("new-session")
# Session no longer exists
```

### Session ID Strategies

**Option 1: User-scoped (one session per user)**
```python
session_id = f"user-{user_id}"
# All conversations for a user in one session
```

**Option 2: Conversation-scoped (multiple sessions per user)**
```python
session_id = f"user-{user_id}-conv-{uuid.uuid4()}"
# Each conversation is separate
# User can have multiple parallel conversations
```

**Option 3: Client-generated (our approach)**
```python
import uuid
session_id = str(uuid.uuid4())
# Client generates unique ID
# Simple and stateless
```

---

## Prompt-Injected Memory

### How AI "Memory" Actually Works

AI models like Claude are **stateless**. They don't remember previous conversations. Each API call is independent.

So how do we make them "remember"? We **include the conversation history in every request**.

### The Anatomy of a Request

```python
# First message
request_1 = {
    "messages": [
        {"role": "user", "content": "My name is Alex"}
    ]
}
response_1 = "Nice to meet you, Alex!"

# Second message - Include FULL conversation history
request_2 = {
    "messages": [
        {"role": "user", "content": "My name is Alex"},
        {"role": "assistant", "content": "Nice to meet you, Alex!"},
        {"role": "user", "content": "What's my name?"}
    ]
}
response_2 = "Your name is Alex!"
# ↑ AI knows because we sent the full conversation!
```

### Context Window Limits

Claude Sonnet has a **200,000 token** context window. That's roughly:
- ~150,000 words
- ~750 pages of text
- ~100-200 conversation turns

Our deque limit of 50 messages (~5,000 tokens) is conservative.

### Token Estimation

We use a simple approximation: **~4 characters per token**

```python
def estimate_tokens(self) -> int:
    """Estimate total tokens in conversation."""
    total_chars = sum(len(msg.content) for msg in self._messages)
    return total_chars // 4
```

**Why approximate?**
- Real tokenization requires the model's tokenizer
- Our approximation is good enough for context window management
- Easy to calculate, no external dependencies

For production, you'd use:
- Anthropic: `anthropic.count_tokens()`
- OpenAI: `tiktoken` library

### System Prompts

System prompts are **instructions** for the AI, not conversation:

```python
messages = [
    {"role": "system", "content": "You are a helpful Python tutor."},
    {"role": "user", "content": "What is a list?"},
    {"role": "assistant", "content": "A list is..."},
    {"role": "user", "content": "How do I append?"}
]
```

**Important**: System prompts are **not stored** in conversation history. They're added with each request but don't count as conversation messages.

---

## Orchestration Pattern

### What is Orchestration?

An **orchestrator** is a service that coordinates multiple subsystems to accomplish a task. It's the "conductor" that tells other components what to do.

### The Service Layer

```
┌─────────────────────────────────────┐
│         API Layer                   │  ← Handles HTTP requests
│  (Routes, request/response models)  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      ConversationService            │  ← Orchestration Layer
│   (Business logic coordinator)      │
└──────┬──────────────────────┬───────┘
       │                      │
       ▼                      ▼
┌─────────────┐      ┌─────────────────┐
│   Memory    │      │   AI Provider   │  ← Infrastructure
│   Manager   │      │   (Claude API)  │
└─────────────┘      └─────────────────┘
```

### ConversationService - The Orchestrator

```python
class ConversationService:
    """Orchestrates conversation flow."""

    def __init__(self, provider: AIProvider, memory_manager: MemoryManager):
        self.provider = provider
        self.memory_manager = memory_manager

    async def send_message(
        self,
        session_id: str,
        user_message: str
    ) -> ChatResponse:
        """
        Orchestrate the full conversation flow:
        1. Get conversation history
        2. Add user message
        3. Call AI provider with full context
        4. Save AI response
        5. Return response
        """
        # 1. Get history
        history = await self.memory_manager.get_messages(session_id)

        # 2. Build full message list
        messages = history + [ChatMessage(role="user", content=user_message)]

        # 3. Call AI
        ai_response = await self.provider.chat(messages)

        # 4. Save both messages
        await self.memory_manager.add_message(
            session_id,
            ChatMessage(role="user", content=user_message)
        )
        await self.memory_manager.add_message(
            session_id,
            ChatMessage(role="assistant", content=ai_response.content)
        )

        # 5. Return
        return ai_response
```

### Benefits of Orchestration Layer

**1. Separation of Concerns**
- API layer: HTTP-specific logic
- Service layer: Business logic
- Infrastructure: Memory, AI providers

**2. Testability**
```python
# Easy to test with mocks
mock_provider = MockProvider()
mock_memory = MemoryManager()
service = ConversationService(mock_provider, mock_memory)

# Test business logic without HTTP or real APIs
response = await service.send_message("session", "Hello")
```

**3. Reusability**
```python
# Same service used by:
# - REST API
# - GraphQL API
# - CLI client
# - Background jobs
# - Anything that needs chat functionality
```

**4. Single Responsibility**
Each component has one job:
- `ShortTermMemory`: Manage message queue
- `MemoryManager`: Manage multiple sessions
- `ConversationService`: Orchestrate the flow
- API routes: Handle HTTP

### Dependency Injection in FastAPI

```python
# dependencies.py
@lru_cache()
def get_conversation_service() -> ConversationService:
    provider = get_ai_provider()
    memory = get_memory_manager()
    return ConversationService(provider, memory)

# routes/chat.py
@app.post("/chat/send")
async def send_message(
    request: ChatRequest,
    service: ConversationService = Depends(get_conversation_service)
):
    # Service is automatically injected!
    response = await service.send_message(
        session_id=request.session_id,
        user_message=request.message
    )
    return response
```

**Benefits:**
- Routes don't know how services are created
- Easy to swap implementations
- Singleton pattern via `@lru_cache()`
- Testing: override dependencies

---

## Key Takeaways - Phase 2

### Concepts Mastered

**1. collections.deque**
- Fixed-size FIFO queues
- Automatic old-item removal
- O(1) append/remove
- Perfect for conversation history

**2. asyncio.Lock**
- Thread safety in async code
- Mutual exclusion
- Per-resource locking
- Automatic cleanup with `async with`

**3. Session Management**
- Isolate conversations
- Per-session state
- Lazy creation
- CRUD operations

**4. Prompt-Injected Memory**
- AI models are stateless
- Include full history in each request
- Context window management
- Token estimation

**5. Orchestration Pattern**
- Service layer for business logic
- Coordinate multiple subsystems
- Separation of concerns
- Dependency injection

### Architecture Patterns

**Before (Phase 1):**
```
API Route → AI Provider
```

**After (Phase 2):**
```
API Route → ConversationService → Memory Manager → AI Provider
                                 ↓
                         ShortTermMemory (deque)
```

### Python Features Used

- `collections.deque` - Fixed-size queues
- `asyncio.Lock` - Async synchronization
- `async/await` - Non-blocking I/O
- Type hints - Static type checking
- Dependency injection - Clean architecture
- Singleton pattern - `@lru_cache()`

### Testing Strategy

- **Unit tests**: Individual components in isolation
- **Integration tests**: Components working together
- **Mock providers**: Test without real API calls
- **Session isolation**: Test concurrent access

### What We Built

1. **ShortTermMemory** - Single conversation queue
2. **MemoryManager** - Multi-session coordinator
3. **ConversationService** - Orchestration layer
4. **Updated API** - Uses service pattern
5. **Enhanced CLI** - `/new` command, memory awareness
6. **Comprehensive tests** - 48 tests passing

---

## Next Phase: Persistent Storage

In Phase 3, we'll add **database persistence**:
- SQLAlchemy 2.0 async ORM
- SQLite for local development
- Repository pattern for data access
- Save/retrieve full conversation history
- Conversations survive server restarts

Phase 2 gave us **short-term memory in RAM**. Phase 3 will make it **persistent on disk**!

---

*This textbook will be updated after each phase with new concepts and learnings.*
