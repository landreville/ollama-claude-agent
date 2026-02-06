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
