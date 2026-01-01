"""Router for GET /api/tags and /api/ps endpoints."""

import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from ..auth import verify_token
from ..config import settings
from ..models import (
    LoadedModelInfo,
    ModelDetails,
    ModelInfo,
    PSResponse,
    TagsResponse,
)

router = APIRouter()


def generate_model_digest(model_name: str) -> str:
    """Generate a consistent digest for a model name.

    Args:
        model_name: The model name.

    Returns:
        SHA256 hash of the model name.
    """
    return hashlib.sha256(model_name.encode()).hexdigest()


def get_iso_timestamp() -> str:
    """Get current ISO 8601 timestamp."""
    return datetime.now(timezone.utc).isoformat()


def get_model_details(model_name: str) -> ModelDetails:
    """Get model details based on model name.

    Args:
        model_name: The model name.

    Returns:
        ModelDetails with family and size info.
    """
    if "opus" in model_name:
        return ModelDetails(
            format="claude",
            family="claude-opus",
            parameter_size="large",
            quantization_level="none",
        )
    elif "sonnet" in model_name:
        return ModelDetails(
            format="claude",
            family="claude-sonnet",
            parameter_size="medium",
            quantization_level="none",
        )
    elif "haiku" in model_name:
        return ModelDetails(
            format="claude",
            family="claude-haiku",
            parameter_size="small",
            quantization_level="none",
        )
    else:
        return ModelDetails(
            format="claude",
            family="claude",
            parameter_size="unknown",
            quantization_level="none",
        )


@router.get("/api/tags")
async def list_tags(
    _: str | None = Depends(verify_token),
) -> TagsResponse:
    """List available models (Ollama-compatible).

    Args:
        _: Verified token (unused, just for auth).

    Returns:
        List of available Claude models.
    """
    models = []
    for model_name in settings.available_models:
        models.append(
            ModelInfo(
                name=model_name,
                model=model_name,
                modified_at=get_iso_timestamp(),
                size=0,  # Not applicable for Claude API
                digest=generate_model_digest(model_name),
                details=get_model_details(model_name),
            )
        )

    return TagsResponse(models=models)


@router.get("/api/ps")
async def list_loaded_models(
    _: str | None = Depends(verify_token),
) -> PSResponse:
    """List currently loaded models (Ollama-compatible).

    For Claude, returns all available models since they're not "loaded" locally.

    Args:
        _: Verified token (unused, just for auth).

    Returns:
        List of available Claude models with expiry info.
    """
    # Claude models are always "available" since they're API-based
    # We return them all with a far-future expiry
    models = []
    expires_at = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()

    for model_name in settings.available_models:
        models.append(
            LoadedModelInfo(
                name=model_name,
                model=model_name,
                size=0,
                digest=generate_model_digest(model_name),
                details=get_model_details(model_name),
                expires_at=expires_at,
                size_vram=0,
            )
        )

    return PSResponse(models=models)
