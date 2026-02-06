# OpenAI API Compatibility Design

## Goal

Add OpenAI-compatible API endpoints alongside the existing Ollama API, both backed by the Claude Agent SDK. This allows tools that speak the OpenAI API (most LLM clients) to use Claude models through this service.

## Scope

### Endpoints to implement

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/v1/chat/completions` | Chat completions (streaming + non-streaming) |
| POST | `/v1/completions` | Text completions (streaming + non-streaming) |
| GET | `/v1/models` | List available models |
| GET | `/v1/models/{model}` | Get specific model info |

### Out of scope

- `/v1/embeddings` - Claude Agent SDK doesn't provide embeddings
- `/v1/images/generations` - Not applicable
- `/v1/responses` - Responses API not needed

## Architecture Decisions

1. **Separate router modules** - New files under `routers/` for OpenAI endpoints, keeping Ollama and OpenAI concerns separated.
2. **Reuse existing auth** - Same `verify_token` dependency as Ollama endpoints. If `OLLAMA_CLAUDE_API_KEY` is set it's enforced; otherwise any key is accepted.
3. **Pass-through model names** - No mapping from OpenAI model names. Users configure their client to use `opus`, `sonnet`, or `haiku`.
4. **Reuse ClaudeService unchanged** - The existing service layer works for both API formats.

## New Files

```
src/ollama_claude/
├── routers/
│   ├── openai_chat.py        # POST /v1/chat/completions
│   ├── openai_completions.py # POST /v1/completions
│   └── openai_models.py      # GET /v1/models, /v1/models/{model}
├── models.py                 # Add OpenAI request/response Pydantic models
├── services/
│   └── stream_adapter.py     # Add OpenAI SSE stream adapter functions
└── main.py                   # Register new routers
```

## Data Models

### Request models

**OpenAIChatRequest:**
- `model` (str, required)
- `messages` (list of `{role, content}`)
- `max_tokens` (int, optional)
- `temperature` (float, optional)
- `top_p` (float, optional)
- `stream` (bool, default false)
- `stop` (str or list, optional)
- `frequency_penalty` (float, optional)
- `presence_penalty` (float, optional)
- `response_format` (object, optional)
- `seed` (int, optional)

**OpenAICompletionRequest:**
- `model` (str, required)
- `prompt` (str, required)
- `max_tokens` (int, optional)
- `temperature` (float, optional)
- `top_p` (float, optional)
- `stream` (bool, default false)
- `stop` (str or list, optional)
- `suffix` (str, optional)

### Response format (non-streaming)

**Chat completion:**
```json
{
  "id": "chatcmpl-<uuid>",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "sonnet",
  "choices": [{
    "index": 0,
    "message": {"role": "assistant", "content": "..."},
    "finish_reason": "stop"
  }],
  "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
}
```

**Text completion:**
```json
{
  "id": "cmpl-<uuid>",
  "object": "text_completion",
  "created": 1234567890,
  "model": "sonnet",
  "choices": [{
    "index": 0,
    "text": "...",
    "finish_reason": "stop"
  }],
  "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
}
```

### Streaming format

Uses **SSE** (`text/event-stream`), not NDJSON:

**Chat streaming chunk:**
```
data: {"id":"chatcmpl-<uuid>","object":"chat.completion.chunk","created":1234567890,"model":"sonnet","choices":[{"index":0,"delta":{"content":"..."},"finish_reason":null}]}

```

**End of stream:**
```
data: [DONE]

```

### Token usage

Token counts returned as 0 since the Claude Agent SDK doesn't expose these values. Most tools don't depend on them.

### Models response

**GET /v1/models:**
```json
{
  "object": "list",
  "data": [
    {"id": "opus", "object": "model", "created": 1234567890, "owned_by": "anthropic"},
    {"id": "sonnet", "object": "model", "created": 1234567890, "owned_by": "anthropic"},
    {"id": "haiku", "object": "model", "created": 1234567890, "owned_by": "anthropic"}
  ]
}
```

**GET /v1/models/{model}:** Returns single model object, or 404 if not found.

## Implementation Steps

1. Add OpenAI Pydantic models to `models.py`
2. Add OpenAI SSE stream adapter functions to `stream_adapter.py`
3. Create `routers/openai_models.py` (GET /v1/models, GET /v1/models/{model})
4. Create `routers/openai_chat.py` (POST /v1/chat/completions)
5. Create `routers/openai_completions.py` (POST /v1/completions)
6. Register new routers in `main.py`
