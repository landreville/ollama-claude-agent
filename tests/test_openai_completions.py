"""Tests for OpenAI-compatible /v1/completions endpoint."""

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


async def test_completions_non_streaming(client):
    """POST /v1/completions returns non-streaming response."""
    with patch(
        "ollama_claude.routers.openai_completions.claude_service"
    ) as mock_service:
        mock_service.generate = MagicMock(return_value=_mock_chunks())

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
        mock_service.generate = MagicMock(return_value=_mock_chunks())

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
