"""Router for POST /api/generate endpoint."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse, JSONResponse

from ..auth import verify_token
from ..models import GenerateRequest
from ..services.claude_service import claude_service
from ..services.stream_adapter import (
    adapt_generate_stream,
    build_generate_response,
    get_nano_time,
)

router = APIRouter()


@router.post("/api/generate")
async def generate(
    request: GenerateRequest,
    _: str | None = Depends(verify_token),
):
    """Generate text completion (Ollama-compatible).

    Args:
        request: The generate request body.
        _: Verified token (unused, just for auth).

    Returns:
        Streaming or non-streaming response in Ollama format.
    """
    model = request.model
    system_prompt = request.system

    if request.stream:
        # Streaming response
        async def stream_generator():
            claude_stream = claude_service.generate(
                prompt=request.prompt,
                model=model,
                system_prompt=system_prompt,
            )
            async for chunk in adapt_generate_stream(claude_stream, model):
                yield chunk

        return StreamingResponse(
            stream_generator(),
            media_type="application/x-ndjson",
        )
    else:
        # Non-streaming response
        start_time = get_nano_time()
        full_text = ""

        async for text_chunk in claude_service.generate(
            prompt=request.prompt,
            model=model,
            system_prompt=system_prompt,
        ):
            full_text += text_chunk

        end_time = get_nano_time()
        duration = end_time - start_time

        return JSONResponse(content=build_generate_response(full_text, model, duration))
