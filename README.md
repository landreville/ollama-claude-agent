# Ollama-Claude Agent

An Ollama-compatible API service that wraps the Claude Agent SDK, enabling any Ollama-compatible client (like N8N, Open WebUI, or custom applications) to interact with Claude models.

## Overview

This service acts as a bridge between the Ollama API specification and Claude's Agent SDK. It translates Ollama API requests into Claude Agent SDK calls and returns responses in Ollama's expected format, including support for streaming.

## Prerequisites

### For Docker (Recommended)

- Docker 20.10 or later
- Claude Code CLI credentials (authenticated via `claude` CLI)

### For Local Development

- Python 3.10 or later
- Node.js 20 or later (required for Claude CLI)
- Claude Code CLI installed and authenticated (`npm install -g @anthropic-ai/claude-code`)

## Installation

### Using Docker (Recommended)

1. **Build the image:**

   ```bash
   docker build -t ollama-claude-agent .
   ```

2. **Run the container:**

   ```bash
   docker run -d --name ollama-claude \
     -p 11434:11434 \
     -e OLLAMA_CLAUDE_API_KEY=your-secret-api-key \
     -v ~/.claude/.credentials.json:/home/appuser/.claude/.credentials.json:ro \
     ollama-claude-agent
   ```

   > **Note:** The `-v` flag mounts your Claude Code credentials into the container. This is required for the Claude Agent SDK to authenticate with Anthropic's API.

### Using pip (Local Development)

1. **Install the package:**

   ```bash
   pip install -e .
   ```

2. **Configure environment:**

   ```bash
   cp .env.example .env
   # Edit .env and set OLLAMA_CLAUDE_API_KEY
   ```

3. **Run the server:**

   ```bash
   ollama-claude
   ```

   Or directly with Python:

   ```bash
   python -m ollama_claude.main
   ```

## Configuration

Configuration is done via environment variables. All variables are prefixed with `OLLAMA_CLAUDE_`.

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_CLAUDE_HOST` | Server bind address | `0.0.0.0` |
| `OLLAMA_CLAUDE_PORT` | Server port | `11434` |
| `OLLAMA_CLAUDE_API_KEY` | API key for client authentication | (none - auth disabled if not set) |
| `OLLAMA_CLAUDE_CWD` | Working directory for Claude Agent | `.` |
| `OLLAMA_CLAUDE_DEFAULT_MAX_TURNS` | Maximum conversation turns | `10` |

## API Endpoints

### Health Check

```
GET /
```

Returns server status.

**Response:**
```json
{"status": "Ollama-Claude Bridge is running"}
```

### Version

```
GET /api/version
```

Returns version information.

**Response:**
```json
{"version": "0.1.0"}
```

### List Models

```
GET /api/tags
```

Lists available Claude models.

**Headers:**
- `Authorization: Bearer <api-key>` (required if API key is configured)

**Response:**
```json
{
  "models": [
    {
      "name": "claude-sonnet-4-20250514",
      "model": "claude-sonnet-4-20250514",
      "modified_at": "2025-01-01T00:00:00Z",
      "size": 0,
      "digest": "...",
      "details": {
        "format": "claude",
        "family": "claude-sonnet",
        "parameter_size": "medium",
        "quantization_level": "none"
      }
    }
  ]
}
```

### List Running Models

```
GET /api/ps
```

Lists "loaded" models. For Claude, this returns the same as `/api/tags` since models are API-based.

**Headers:**
- `Authorization: Bearer <api-key>` (required if API key is configured)

### Generate Completion

```
POST /api/generate
```

Generate a text completion.

**Headers:**
- `Authorization: Bearer <api-key>` (required if API key is configured)
- `Content-Type: application/json`

**Request Body:**
```json
{
  "model": "claude-sonnet-4-20250514",
  "prompt": "Why is the sky blue?",
  "system": "You are a helpful assistant.",
  "stream": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | Yes | Claude model ID |
| `prompt` | string | Yes | Input prompt |
| `system` | string | No | System prompt |
| `stream` | boolean | No | Enable streaming (default: `true`) |

**Response (non-streaming):**
```json
{
  "model": "claude-sonnet-4-20250514",
  "created_at": "2025-01-01T00:00:00Z",
  "response": "The sky appears blue because...",
  "done": true,
  "done_reason": "stop",
  "total_duration": 1234567890
}
```

**Response (streaming):**
Each line is a JSON object:
```json
{"model": "...", "created_at": "...", "response": "The ", "done": false}
{"model": "...", "created_at": "...", "response": "sky ", "done": false}
{"model": "...", "created_at": "...", "response": "", "done": true, "done_reason": "stop"}
```

### Chat Completion

```
POST /api/chat
```

Generate a chat completion with message history.

**Headers:**
- `Authorization: Bearer <api-key>` (required if API key is configured)
- `Content-Type: application/json`

**Request Body:**
```json
{
  "model": "claude-sonnet-4-20250514",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi there! How can I help?"},
    {"role": "user", "content": "What is 2+2?"}
  ],
  "stream": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | Yes | Claude model ID |
| `messages` | array | Yes | Array of message objects |
| `stream` | boolean | No | Enable streaming (default: `true`) |

**Message Object:**
| Field | Type | Description |
|-------|------|-------------|
| `role` | string | One of: `system`, `user`, `assistant`, `tool` |
| `content` | string | Message content |

**Response (non-streaming):**
```json
{
  "model": "claude-sonnet-4-20250514",
  "created_at": "2025-01-01T00:00:00Z",
  "message": {
    "role": "assistant",
    "content": "2 + 2 = 4"
  },
  "done": true,
  "done_reason": "stop",
  "total_duration": 1234567890
}
```

## Available Models

The following Claude models are available:

| Model ID | Family | Size |
|----------|--------|------|
| `claude-sonnet-4-20250514` | Sonnet | Medium |
| `claude-opus-4-20250514` | Opus | Large |
| `claude-3-5-haiku-20241022` | Haiku | Small |
| `claude-3-5-sonnet-20241022` | Sonnet | Medium |
| `claude-3-opus-20240229` | Opus | Large |
| `claude-3-sonnet-20240229` | Sonnet | Medium |
| `claude-3-haiku-20240307` | Haiku | Small |

## Usage Examples

### cURL

```bash
# List models
curl -H "Authorization: Bearer your-api-key" \
  http://localhost:11434/api/tags

# Chat completion
curl -X POST http://localhost:11434/api/chat \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": false
  }'

# Generate completion
curl -X POST http://localhost:11434/api/generate \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "prompt": "Explain quantum computing",
    "stream": false
  }'
```

### Python

```python
import requests

BASE_URL = "http://localhost:11434"
HEADERS = {
    "Authorization": "Bearer your-api-key",
    "Content-Type": "application/json"
}

# Chat completion
response = requests.post(
    f"{BASE_URL}/api/chat",
    headers=HEADERS,
    json={
        "model": "claude-sonnet-4-20250514",
        "messages": [{"role": "user", "content": "Hello!"}],
        "stream": False
    }
)
print(response.json()["message"]["content"])
```

### N8N Integration

1. Add an "Ollama" node to your workflow
2. Configure the base URL: `http://your-server:11434`
3. Set the model to a Claude model ID (e.g., `claude-sonnet-4-20250514`)
4. Add authentication header if required

## Docker Compose

```yaml
version: '3.8'

services:
  ollama-claude:
    build: .
    ports:
      - "11434:11434"
    environment:
      - OLLAMA_CLAUDE_API_KEY=your-secret-api-key
    volumes:
      - ~/.claude/.credentials.json:/home/appuser/.claude/.credentials.json:ro
    restart: unless-stopped
```

## Development

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Code Formatting

```bash
ruff check .
ruff format .
```

### Type Checking

```bash
mypy src/
```

## Troubleshooting

### "Authorization header required"

You need to include the `Authorization` header with your API key:
```bash
curl -H "Authorization: Bearer your-api-key" http://localhost:11434/api/tags
```

### "Claude Code not found"

The Claude CLI is not installed or not in the PATH. Install it with:
```bash
npm install -g @anthropic-ai/claude-code
```

### Authentication Errors from Claude

Ensure your Claude credentials are properly mounted:
```bash
docker run -v ~/.claude/.credentials.json:/home/appuser/.claude/.credentials.json:ro ...
```

Or authenticate the CLI locally:
```bash
claude auth login
```

## License

MIT
