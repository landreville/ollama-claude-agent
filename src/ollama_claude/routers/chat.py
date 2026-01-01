"""Router for POST /api/chat endpoint."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse, JSONResponse

from ..auth import verify_token
from ..models import ChatRequest
from ..services.claude_service import claude_service
from ..services.stream_adapter import (
    adapt_chat_stream,
    build_chat_response,
    get_nano_time,
)

router = APIRouter()


@router.post("/api/chat")
async def chat(
    request: ChatRequest,
    _: str | None = Depends(verify_token),
):
    """Chat completion with messages (Ollama-compatible).

    Args:
        request: The chat request body.
        _: Verified token (unused, just for auth).

    Returns:
        Streaming or non-streaming response in Ollama format.
    """
    model = request.model

    # Convert messages to dict format
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

    if request.stream:
        # Streaming response
        async def stream_generator():
            claude_stream = claude_service.chat(
                messages=messages,
                model=model,
            )
            async for chunk in adapt_chat_stream(claude_stream, model):
                yield chunk

        return StreamingResponse(
            stream_generator(),
            media_type="application/x-ndjson",
        )
    else:
        # Non-streaming response
        start_time = get_nano_time()
        full_text = ""

        async for text_chunk in claude_service.chat(
            messages=messages,
            model=model,
        ):
            full_text += text_chunk

        end_time = get_nano_time()
        duration = end_time - start_time

        return JSONResponse(content=build_chat_response(full_text, model, duration))
