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
