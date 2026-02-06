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
