# OpenAI API Compatibility Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add OpenAI-compatible API endpoints (`/v1/chat/completions`, `/v1/completions`, `/v1/models`) alongside the existing Ollama API, backed by the same Claude Agent SDK service layer.

**Architecture:** New router modules under `routers/` for OpenAI endpoints. New Pydantic models in `models.py`. New SSE stream adapter functions in `stream_adapter.py`. ClaudeService unchanged. All registered in `main.py`.

**Tech Stack:** FastAPI, Pydantic v2, claude-agent-sdk, pytest + httpx for testing

**Design doc:** `docs/plans/2026-02-05-openai-api-compatibility-design.md`

---

### Task 1: Add OpenAI Pydantic models

**Files:**
- Modify: `src/ollama_claude/models.py:151` (append after existing models)

**Step 1: Add OpenAI models to `models.py`**

Append to end of `src/ollama_claude/models.py`:

```python
# === OpenAI-Compatible Endpoint Models ===


class OpenAIChatMessage(BaseModel):
    """Message in OpenAI chat request/response."""

    role: Literal["system", "user", "assistant"]
    content: str


class OpenAIChatRequest(BaseModel):
    """Request body for POST /v1/chat/completions."""

    model: str
    messages: list[OpenAIChatMessage]
    max_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    stream: bool = False
    stop: str | list[str] | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    response_format: dict[str, Any] | None = None
    seed: int | None = None


class OpenAICompletionRequest(BaseModel):
    """Request body for POST /v1/completions."""

    model: str
    prompt: str
    max_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    stream: bool = False
    stop: str | list[str] | None = None
    suffix: str | None = None


class OpenAIUsage(BaseModel):
    """Token usage in OpenAI responses."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class OpenAIChatChoice(BaseModel):
    """Choice in OpenAI chat completion response."""

    index: int = 0
    message: OpenAIChatMessage
    finish_reason: str = "stop"


class OpenAIChatResponse(BaseModel):
    """Response for POST /v1/chat/completions (non-streaming)."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[OpenAIChatChoice]
    usage: OpenAIUsage = OpenAIUsage()


class OpenAIChatStreamDelta(BaseModel):
    """Delta in OpenAI chat streaming chunk."""

    role: str | None = None
    content: str | None = None


class OpenAIChatStreamChoice(BaseModel):
    """Choice in OpenAI chat streaming chunk."""

    index: int = 0
    delta: OpenAIChatStreamDelta
    finish_reason: str | None = None


class OpenAIChatStreamChunk(BaseModel):
    """Streaming chunk for POST /v1/chat/completions."""

    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: list[OpenAIChatStreamChoice]


class OpenAICompletionChoice(BaseModel):
    """Choice in OpenAI text completion response."""

    index: int = 0
    text: str
    finish_reason: str = "stop"


class OpenAICompletionResponse(BaseModel):
    """Response for POST /v1/completions (non-streaming)."""

    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: list[OpenAICompletionChoice]
    usage: OpenAIUsage = OpenAIUsage()


class OpenAICompletionStreamChoice(BaseModel):
    """Choice in OpenAI text completion streaming chunk."""

    index: int = 0
    text: str
    finish_reason: str | None = None


class OpenAICompletionStreamChunk(BaseModel):
    """Streaming chunk for POST /v1/completions."""

    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: list[OpenAICompletionStreamChoice]


class OpenAIModel(BaseModel):
    """Model object in OpenAI /v1/models response."""

    id: str
    object: str = "model"
    created: int
    owned_by: str = "anthropic"


class OpenAIModelList(BaseModel):
    """Response for GET /v1/models."""

    object: str = "list"
    data: list[OpenAIModel]
```

**Step 2: Verify syntax**

Run: `python -c "from ollama_claude.models import OpenAIChatRequest, OpenAIModelList; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add src/ollama_claude/models.py
git commit -m "feat: add OpenAI-compatible Pydantic models"
```

---

### Task 2: Add OpenAI SSE stream adapters

**Files:**
- Modify: `src/ollama_claude/services/stream_adapter.py:176` (append after existing functions)

**Step 1: Add OpenAI stream adapter functions**

Append to end of `src/ollama_claude/services/stream_adapter.py`:

```python
# === OpenAI-Compatible Stream Adapters ===


def get_unix_timestamp() -> int:
    """Get current Unix timestamp as integer."""
    return int(time.time())


async def adapt_openai_chat_stream(
    claude_stream: AsyncIterator[str],
    model: str,
    request_id: str,
) -> AsyncIterator[str]:
    """Adapt Claude Agent SDK stream to OpenAI /v1/chat/completions SSE format.

    Args:
        claude_stream: Async iterator yielding text chunks from Claude.
        model: The model name for the response.
        request_id: Unique ID for this request.

    Yields:
        SSE lines in OpenAI format.
    """
    created = get_unix_timestamp()

    # First chunk includes role
    first = True
    async for text_chunk in claude_stream:
        delta = {"content": text_chunk}
        if first:
            delta["role"] = "assistant"
            first = False

        chunk = {
            "id": request_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{"index": 0, "delta": delta, "finish_reason": None}],
        }
        yield f"data: {json.dumps(chunk)}\n\n"

    # Final chunk with finish_reason
    final_chunk = {
        "id": request_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    yield f"data: {json.dumps(final_chunk)}\n\n"
    yield "data: [DONE]\n\n"


async def adapt_openai_completion_stream(
    claude_stream: AsyncIterator[str],
    model: str,
    request_id: str,
) -> AsyncIterator[str]:
    """Adapt Claude Agent SDK stream to OpenAI /v1/completions SSE format.

    Args:
        claude_stream: Async iterator yielding text chunks from Claude.
        model: The model name for the response.
        request_id: Unique ID for this request.

    Yields:
        SSE lines in OpenAI format.
    """
    created = get_unix_timestamp()

    async for text_chunk in claude_stream:
        chunk = {
            "id": request_id,
            "object": "text_completion",
            "created": created,
            "model": model,
            "choices": [{"index": 0, "text": text_chunk, "finish_reason": None}],
        }
        yield f"data: {json.dumps(chunk)}\n\n"

    # Final chunk with finish_reason
    final_chunk = {
        "id": request_id,
        "object": "text_completion",
        "created": created,
        "model": model,
        "choices": [{"index": 0, "text": "", "finish_reason": "stop"}],
    }
    yield f"data: {json.dumps(final_chunk)}\n\n"
    yield "data: [DONE]\n\n"


def build_openai_chat_response(
    text: str,
    model: str,
    request_id: str,
) -> dict:
    """Build non-streaming OpenAI chat completion response.

    Args:
        text: The complete response text.
        model: The model name.
        request_id: Unique ID for this request.

    Returns:
        Response dictionary in OpenAI format.
    """
    return {
        "id": request_id,
        "object": "chat.completion",
        "created": get_unix_timestamp(),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


def build_openai_completion_response(
    text: str,
    model: str,
    request_id: str,
) -> dict:
    """Build non-streaming OpenAI text completion response.

    Args:
        text: The complete response text.
        model: The model name.
        request_id: Unique ID for this request.

    Returns:
        Response dictionary in OpenAI format.
    """
    return {
        "id": request_id,
        "object": "text_completion",
        "created": get_unix_timestamp(),
        "model": model,
        "choices": [
            {
                "index": 0,
                "text": text,
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }
```

**Step 2: Verify syntax**

Run: `python -c "from ollama_claude.services.stream_adapter import adapt_openai_chat_stream, build_openai_chat_response; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add src/ollama_claude/services/stream_adapter.py
git commit -m "feat: add OpenAI SSE stream adapter functions"
```

---

### Task 3: Create OpenAI models router

**Files:**
- Create: `src/ollama_claude/routers/openai_models.py`

**Step 1: Write the router**

Create `src/ollama_claude/routers/openai_models.py`:

```python
"""Router for GET /v1/models endpoints (OpenAI-compatible)."""

import time

from fastapi import APIRouter, Depends, HTTPException

from ..auth import verify_token

router = APIRouter()

AVAILABLE_MODELS = ["opus", "sonnet", "haiku"]


def _build_model_object(model_id: str) -> dict:
    """Build an OpenAI model object."""
    return {
        "id": model_id,
        "object": "model",
        "created": int(time.time()),
        "owned_by": "anthropic",
    }


@router.get("/v1/models")
async def list_models(
    _: str | None = Depends(verify_token),
):
    """List available models (OpenAI-compatible)."""
    return {
        "object": "list",
        "data": [_build_model_object(m) for m in AVAILABLE_MODELS],
    }


@router.get("/v1/models/{model}")
async def get_model(
    model: str,
    _: str | None = Depends(verify_token),
):
    """Get a specific model (OpenAI-compatible)."""
    if model not in AVAILABLE_MODELS:
        raise HTTPException(status_code=404, detail=f"Model '{model}' not found")
    return _build_model_object(model)
```

**Step 2: Verify syntax**

Run: `python -c "from ollama_claude.routers.openai_models import router; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add src/ollama_claude/routers/openai_models.py
git commit -m "feat: add OpenAI-compatible /v1/models endpoints"
```

---

### Task 4: Create OpenAI chat completions router

**Files:**
- Create: `src/ollama_claude/routers/openai_chat.py`

**Step 1: Write the router**

Create `src/ollama_claude/routers/openai_chat.py`:

```python
"""Router for POST /v1/chat/completions endpoint (OpenAI-compatible)."""

import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse, JSONResponse

from ..auth import verify_token
from ..models import OpenAIChatRequest
from ..services.claude_service import claude_service
from ..services.stream_adapter import (
    adapt_openai_chat_stream,
    build_openai_chat_response,
)

router = APIRouter()


@router.post("/v1/chat/completions")
async def chat_completions(
    request: OpenAIChatRequest,
    _: str | None = Depends(verify_token),
):
    """Chat completion (OpenAI-compatible).

    Args:
        request: The chat completion request body.
        _: Verified token (unused, just for auth).

    Returns:
        Streaming SSE or non-streaming JSON response in OpenAI format.
    """
    model = request.model
    request_id = f"chatcmpl-{uuid.uuid4().hex[:29]}"

    # Convert messages to dict format for ClaudeService
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

    if request.stream:
        async def stream_generator():
            claude_stream = claude_service.chat(
                messages=messages,
                model=model,
            )
            async for chunk in adapt_openai_chat_stream(claude_stream, model, request_id):
                yield chunk

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
        )
    else:
        full_text = ""
        async for text_chunk in claude_service.chat(
            messages=messages,
            model=model,
        ):
            full_text += text_chunk

        return JSONResponse(
            content=build_openai_chat_response(full_text, model, request_id)
        )
```

**Step 2: Verify syntax**

Run: `python -c "from ollama_claude.routers.openai_chat import router; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add src/ollama_claude/routers/openai_chat.py
git commit -m "feat: add OpenAI-compatible /v1/chat/completions endpoint"
```

---

### Task 5: Create OpenAI completions router

**Files:**
- Create: `src/ollama_claude/routers/openai_completions.py`

**Step 1: Write the router**

Create `src/ollama_claude/routers/openai_completions.py`:

```python
"""Router for POST /v1/completions endpoint (OpenAI-compatible)."""

import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse, JSONResponse

from ..auth import verify_token
from ..models import OpenAICompletionRequest
from ..services.claude_service import claude_service
from ..services.stream_adapter import (
    adapt_openai_completion_stream,
    build_openai_completion_response,
)

router = APIRouter()


@router.post("/v1/completions")
async def completions(
    request: OpenAICompletionRequest,
    _: str | None = Depends(verify_token),
):
    """Text completion (OpenAI-compatible).

    Args:
        request: The completion request body.
        _: Verified token (unused, just for auth).

    Returns:
        Streaming SSE or non-streaming JSON response in OpenAI format.
    """
    model = request.model
    request_id = f"cmpl-{uuid.uuid4().hex[:29]}"

    if request.stream:
        async def stream_generator():
            claude_stream = claude_service.generate(
                prompt=request.prompt,
                model=model,
            )
            async for chunk in adapt_openai_completion_stream(
                claude_stream, model, request_id
            ):
                yield chunk

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
        )
    else:
        full_text = ""
        async for text_chunk in claude_service.generate(
            prompt=request.prompt,
            model=model,
        ):
            full_text += text_chunk

        return JSONResponse(
            content=build_openai_completion_response(full_text, model, request_id)
        )
```

**Step 2: Verify syntax**

Run: `python -c "from ollama_claude.routers.openai_completions import router; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add src/ollama_claude/routers/openai_completions.py
git commit -m "feat: add OpenAI-compatible /v1/completions endpoint"
```

---

### Task 6: Register new routers in main.py

**Files:**
- Modify: `src/ollama_claude/main.py:9` (import) and `src/ollama_claude/main.py:29` (register)

**Step 1: Update imports**

In `src/ollama_claude/main.py`, change line 9:

```python
from .routers import chat, generate, models
```

to:

```python
from .routers import chat, generate, models, openai_chat, openai_completions, openai_models
```

**Step 2: Register new routers**

After line 29 (`app.include_router(models.router)`), add:

```python
app.include_router(openai_chat.router)
app.include_router(openai_completions.router)
app.include_router(openai_models.router)
```

**Step 3: Verify the app starts**

Run: `python -c "from ollama_claude.main import app; print([r.path for r in app.routes])"`
Expected: Should include `/v1/chat/completions`, `/v1/completions`, `/v1/models`, `/v1/models/{model}` alongside existing routes.

**Step 4: Commit**

```bash
git add src/ollama_claude/main.py
git commit -m "feat: register OpenAI-compatible routers in app"
```

---

### Task 7: Write tests for OpenAI models endpoint

**Files:**
- Create: `tests/test_openai_models.py`

**Step 1: Write tests**

Create `tests/test_openai_models.py`:

```python
"""Tests for OpenAI-compatible /v1/models endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from ollama_claude.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_list_models(client):
    """GET /v1/models returns list of models."""
    response = await client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert len(data["data"]) == 3
    model_ids = [m["id"] for m in data["data"]]
    assert "opus" in model_ids
    assert "sonnet" in model_ids
    assert "haiku" in model_ids
    for m in data["data"]:
        assert m["object"] == "model"
        assert m["owned_by"] == "anthropic"
        assert isinstance(m["created"], int)


async def test_get_model(client):
    """GET /v1/models/{model} returns a single model."""
    response = await client.get("/v1/models/sonnet")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "sonnet"
    assert data["object"] == "model"
    assert data["owned_by"] == "anthropic"


async def test_get_model_not_found(client):
    """GET /v1/models/{model} returns 404 for unknown model."""
    response = await client.get("/v1/models/gpt-4")
    assert response.status_code == 404
```

**Step 2: Run tests to verify they pass**

Run: `python -m pytest tests/test_openai_models.py -v`
Expected: 3 tests PASS

**Step 3: Commit**

```bash
git add tests/test_openai_models.py
git commit -m "test: add tests for OpenAI /v1/models endpoints"
```

---

### Task 8: Write tests for OpenAI chat completions endpoint

**Files:**
- Create: `tests/test_openai_chat.py`

**Step 1: Write tests**

Create `tests/test_openai_chat.py`:

```python
"""Tests for OpenAI-compatible /v1/chat/completions endpoint."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from ollama_claude.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def mock_chat_stream(*args, **kwargs):
    """Mock ClaudeService.chat that yields text chunks."""
    yield "Hello"
    yield " world"


async def test_chat_completions_non_streaming(client):
    """POST /v1/chat/completions returns non-streaming response."""
    with patch(
        "ollama_claude.routers.openai_chat.claude_service"
    ) as mock_service:
        mock_service.chat = AsyncMock(side_effect=mock_chat_stream)

        response = await client.post(
            "/v1/chat/completions",
            json={
                "model": "sonnet",
                "messages": [{"role": "user", "content": "Hi"}],
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "chat.completion"
    assert data["id"].startswith("chatcmpl-")
    assert data["model"] == "sonnet"
    assert len(data["choices"]) == 1
    assert data["choices"][0]["message"]["role"] == "assistant"
    assert data["choices"][0]["message"]["content"] == "Hello world"
    assert data["choices"][0]["finish_reason"] == "stop"
    assert "usage" in data


async def test_chat_completions_streaming(client):
    """POST /v1/chat/completions returns SSE streaming response."""
    with patch(
        "ollama_claude.routers.openai_chat.claude_service"
    ) as mock_service:
        mock_service.chat = AsyncMock(side_effect=mock_chat_stream)

        response = await client.post(
            "/v1/chat/completions",
            json={
                "model": "sonnet",
                "messages": [{"role": "user", "content": "Hi"}],
                "stream": True,
            },
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    lines = response.text.strip().split("\n\n")
    # Should have: role+content chunk, content chunk, finish chunk, [DONE]
    assert lines[-1] == "data: [DONE]"
```

**Step 2: Run tests to verify they pass**

Run: `python -m pytest tests/test_openai_chat.py -v`
Expected: 2 tests PASS

**Step 3: Commit**

```bash
git add tests/test_openai_chat.py
git commit -m "test: add tests for OpenAI /v1/chat/completions endpoint"
```

---

### Task 9: Write tests for OpenAI completions endpoint

**Files:**
- Create: `tests/test_openai_completions.py`

**Step 1: Write tests**

Create `tests/test_openai_completions.py`:

```python
"""Tests for OpenAI-compatible /v1/completions endpoint."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from ollama_claude.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def mock_generate_stream(*args, **kwargs):
    """Mock ClaudeService.generate that yields text chunks."""
    yield "Hello"
    yield " world"


async def test_completions_non_streaming(client):
    """POST /v1/completions returns non-streaming response."""
    with patch(
        "ollama_claude.routers.openai_completions.claude_service"
    ) as mock_service:
        mock_service.generate = AsyncMock(side_effect=mock_generate_stream)

        response = await client.post(
            "/v1/completions",
            json={
                "model": "sonnet",
                "prompt": "Hello",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "text_completion"
    assert data["id"].startswith("cmpl-")
    assert data["model"] == "sonnet"
    assert len(data["choices"]) == 1
    assert data["choices"][0]["text"] == "Hello world"
    assert data["choices"][0]["finish_reason"] == "stop"
    assert "usage" in data


async def test_completions_streaming(client):
    """POST /v1/completions returns SSE streaming response."""
    with patch(
        "ollama_claude.routers.openai_completions.claude_service"
    ) as mock_service:
        mock_service.generate = AsyncMock(side_effect=mock_generate_stream)

        response = await client.post(
            "/v1/completions",
            json={
                "model": "sonnet",
                "prompt": "Hello",
                "stream": True,
            },
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    lines = response.text.strip().split("\n\n")
    assert lines[-1] == "data: [DONE]"
```

**Step 2: Run tests to verify they pass**

Run: `python -m pytest tests/test_openai_completions.py -v`
Expected: 2 tests PASS

**Step 3: Commit**

```bash
git add tests/test_openai_completions.py
git commit -m "test: add tests for OpenAI /v1/completions endpoint"
```

---

### Task 10: Run full test suite and final verification

**Step 1: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: All 7 tests PASS

**Step 2: Run ruff linter**

Run: `ruff check src/ tests/`
Expected: No errors

**Step 3: Commit any fixes if needed, then final commit**

```bash
git add -A
git commit -m "feat: complete OpenAI API compatibility layer"
```
