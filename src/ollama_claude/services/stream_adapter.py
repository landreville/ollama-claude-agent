"""Streaming format translation between Claude SDK and Ollama NDJSON."""

import json
import time
from collections.abc import AsyncIterator
from datetime import datetime, timezone


def get_iso_timestamp() -> str:
    """Get current ISO 8601 timestamp."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def get_nano_time() -> int:
    """Get current time in nanoseconds."""
    return int(time.time() * 1_000_000_000)


async def adapt_generate_stream(
    claude_stream: AsyncIterator[str],
    model: str,
) -> AsyncIterator[str]:
    """Adapt Claude Agent SDK stream to Ollama /api/generate streaming format.

    Args:
        claude_stream: Async iterator yielding text chunks from Claude.
        model: The model name for the response.

    Yields:
        NDJSON lines in Ollama format.
    """
    start_time = get_nano_time()
    eval_count = 0

    async for text_chunk in claude_stream:
        eval_count += 1

        chunk = {
            "model": model,
            "created_at": get_iso_timestamp(),
            "response": text_chunk,
            "done": False,
        }
        yield json.dumps(chunk) + "\n"

    # Final chunk with done=True and metrics
    end_time = get_nano_time()
    final_chunk = {
        "model": model,
        "created_at": get_iso_timestamp(),
        "response": "",
        "done": True,
        "done_reason": "stop",
        "total_duration": end_time - start_time,
        "load_duration": 0,  # Not applicable for Claude
        "prompt_eval_count": 0,  # Not tracked
        "prompt_eval_duration": 0,
        "eval_count": eval_count,
        "eval_duration": end_time - start_time,
    }
    yield json.dumps(final_chunk) + "\n"


async def adapt_chat_stream(
    claude_stream: AsyncIterator[str],
    model: str,
) -> AsyncIterator[str]:
    """Adapt Claude Agent SDK stream to Ollama /api/chat streaming format.

    Args:
        claude_stream: Async iterator yielding text chunks from Claude.
        model: The model name for the response.

    Yields:
        NDJSON lines in Ollama format.
    """
    start_time = get_nano_time()
    eval_count = 0

    async for text_chunk in claude_stream:
        eval_count += 1

        chunk = {
            "model": model,
            "created_at": get_iso_timestamp(),
            "message": {
                "role": "assistant",
                "content": text_chunk,
            },
            "done": False,
        }
        yield json.dumps(chunk) + "\n"

    # Final chunk with done=True and metrics
    end_time = get_nano_time()
    final_chunk = {
        "model": model,
        "created_at": get_iso_timestamp(),
        "message": {
            "role": "assistant",
            "content": "",
        },
        "done": True,
        "done_reason": "stop",
        "total_duration": end_time - start_time,
        "load_duration": 0,
        "prompt_eval_count": 0,
        "prompt_eval_duration": 0,
        "eval_count": eval_count,
        "eval_duration": end_time - start_time,
    }
    yield json.dumps(final_chunk) + "\n"


def build_generate_response(
    text: str,
    model: str,
    duration_ns: int,
) -> dict:
    """Build non-streaming generate response.

    Args:
        text: The complete response text.
        model: The model name.
        duration_ns: Total duration in nanoseconds.

    Returns:
        Response dictionary in Ollama format.
    """
    return {
        "model": model,
        "created_at": get_iso_timestamp(),
        "response": text,
        "done": True,
        "done_reason": "stop",
        "total_duration": duration_ns,
        "load_duration": 0,
        "prompt_eval_count": 0,
        "prompt_eval_duration": 0,
        "eval_count": 1,
        "eval_duration": duration_ns,
    }


def build_chat_response(
    text: str,
    model: str,
    duration_ns: int,
) -> dict:
    """Build non-streaming chat response.

    Args:
        text: The complete response text.
        model: The model name.
        duration_ns: Total duration in nanoseconds.

    Returns:
        Response dictionary in Ollama format.
    """
    return {
        "model": model,
        "created_at": get_iso_timestamp(),
        "message": {
            "role": "assistant",
            "content": text,
        },
        "done": True,
        "done_reason": "stop",
        "total_duration": duration_ns,
        "load_duration": 0,
        "prompt_eval_count": 0,
        "prompt_eval_duration": 0,
        "eval_count": 1,
        "eval_duration": duration_ns,
    }
