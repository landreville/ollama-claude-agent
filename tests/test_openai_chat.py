"""Tests for OpenAI-compatible /v1/chat/completions endpoint."""

from unittest.mock import patch, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from ollama_claude.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _mock_chunks():
    yield "Hello"
    yield " world"


async def test_chat_completions_non_streaming(client):
    """POST /v1/chat/completions returns non-streaming response."""
    with patch(
        "ollama_claude.routers.openai_chat.claude_service"
    ) as mock_service:
        mock_service.chat = MagicMock(return_value=_mock_chunks())

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
        mock_service.chat = MagicMock(return_value=_mock_chunks())

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
