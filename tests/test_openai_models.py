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
