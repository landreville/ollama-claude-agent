"""Router for GET /api/tags and /api/ps endpoints."""

import hashlib
import logging
import time
from datetime import datetime, timedelta, timezone

from anthropic import Anthropic
from fastapi import APIRouter, Depends

from ..auth import verify_token
from ..models import (
    LoadedModelInfo,
    ModelDetails,
    ModelInfo,
    PSResponse,
    TagsResponse,
)

logger = logging.getLogger(__name__)

# Cache for models list (model_id -> display_name)
_models_cache: dict[str, str] = {}
_cache_timestamp: float = 0
_CACHE_TTL_SECONDS = 3600  # Refresh cache every hour

router = APIRouter()


def get_available_models() -> dict[str, str]:
    """Fetch available models from the Anthropic API with caching.

    Returns:
        Dict mapping model ID to display name.
    """
    global _models_cache, _cache_timestamp

    current_time = time.time()
    if _models_cache and (current_time - _cache_timestamp) < _CACHE_TTL_SECONDS:
        return _models_cache

    try:
        client = Anthropic()
        models: dict[str, str] = {}
        for model in client.models.list():
            models[model.id] = model.display_name
        _models_cache = models
        _cache_timestamp = current_time
        logger.info(f"Fetched {len(models)} models from Anthropic API")
        return models
    except Exception as e:
        logger.error(f"Failed to fetch models from Anthropic API: {e}")
        # Return cached models if available, otherwise empty
        if _models_cache:
            return _models_cache
        return {}


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
    available_models = get_available_models()
    models = []
    for model_id in available_models:
        models.append(
            ModelInfo(
                name=model_id,
                model=model_id,
                modified_at=get_iso_timestamp(),
                size=0,  # Not applicable for Claude API
                digest=generate_model_digest(model_id),
                details=get_model_details(model_id),
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
    available_models = get_available_models()
    models = []
    expires_at = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()

    for model_id in available_models:
        models.append(
            LoadedModelInfo(
                name=model_id,
                model=model_id,
                size=0,
                digest=generate_model_digest(model_id),
                details=get_model_details(model_id),
                expires_at=expires_at,
                size_vram=0,
            )
        )

    return PSResponse(models=models)
