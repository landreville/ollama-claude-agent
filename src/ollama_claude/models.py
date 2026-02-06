"""Pydantic models for Ollama-compatible request/response formats."""

from typing import Any, Literal

from pydantic import BaseModel


# === Generate Endpoint Models ===


class GenerateRequest(BaseModel):
    """Request body for POST /api/generate."""

    model: str
    prompt: str
    system: str | None = None
    template: str | None = None
    context: list[int] | None = None
    stream: bool = True
    raw: bool = False
    format: str | None = None  # "json" or JSON schema
    options: dict[str, Any] | None = None
    keep_alive: str | None = "5m"


class GenerateResponse(BaseModel):
    """Response for POST /api/generate (non-streaming or final chunk)."""

    model: str
    created_at: str  # ISO 8601 timestamp
    response: str
    done: bool
    done_reason: str | None = None
    context: list[int] | None = None
    total_duration: int | None = None  # nanoseconds
    load_duration: int | None = None
    prompt_eval_count: int | None = None
    prompt_eval_duration: int | None = None
    eval_count: int | None = None
    eval_duration: int | None = None


class GenerateStreamChunk(BaseModel):
    """Streaming chunk for POST /api/generate."""

    model: str
    created_at: str
    response: str
    done: bool


# === Chat Endpoint Models ===


class ChatMessage(BaseModel):
    """Individual chat message."""

    role: Literal["system", "user", "assistant", "tool"]
    content: str
    images: list[str] | None = None  # Base64 encoded images


class ChatRequest(BaseModel):
    """Request body for POST /api/chat."""

    model: str
    messages: list[ChatMessage]
    stream: bool = True
    format: str | None = None
    options: dict[str, Any] | None = None
    keep_alive: str | None = "5m"


class ChatResponseMessage(BaseModel):
    """Message in chat response."""

    role: str = "assistant"
    content: str


class ChatResponse(BaseModel):
    """Response for POST /api/chat (non-streaming or final chunk)."""

    model: str
    created_at: str
    message: ChatResponseMessage
    done: bool
    done_reason: str | None = None
    total_duration: int | None = None
    load_duration: int | None = None
    prompt_eval_count: int | None = None
    prompt_eval_duration: int | None = None
    eval_count: int | None = None
    eval_duration: int | None = None


class ChatStreamChunk(BaseModel):
    """Streaming chunk for POST /api/chat."""

    model: str
    created_at: str
    message: ChatResponseMessage
    done: bool


# === Models Endpoint Models ===


class ModelDetails(BaseModel):
    """Model details in /api/tags response."""

    format: str = "claude"
    family: str = "claude"
    parameter_size: str = "unknown"
    quantization_level: str = "none"


class ModelInfo(BaseModel):
    """Model information in /api/tags response."""

    name: str
    model: str
    modified_at: str
    size: int = 0  # Not applicable for Claude
    digest: str
    details: ModelDetails


class TagsResponse(BaseModel):
    """Response for GET /api/tags."""

    models: list[ModelInfo]


class LoadedModelInfo(BaseModel):
    """Model information in /api/ps response."""

    name: str
    model: str
    size: int = 0
    digest: str
    details: ModelDetails
    expires_at: str
    size_vram: int = 0


class PSResponse(BaseModel):
    """Response for GET /api/ps."""

    models: list[LoadedModelInfo]


# === OpenAI-Compatible Endpoint Models ===


class OpenAIChatMessage(BaseModel):
    """Message in OpenAI chat request/response."""

    role: Literal["system", "user", "assistant"]
    content: str


class OpenAIChatRequest(BaseModel):
    """Request body for POST /v1/chat/completions."""

    model: str
    messages: list[OpenAIChatMessage]
    max_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    stream: bool = False
    stop: str | list[str] | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    response_format: dict[str, Any] | None = None
    seed: int | None = None


class OpenAICompletionRequest(BaseModel):
    """Request body for POST /v1/completions."""

    model: str
    prompt: str
    max_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    stream: bool = False
    stop: str | list[str] | None = None
    suffix: str | None = None


class OpenAIUsage(BaseModel):
    """Token usage in OpenAI responses."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class OpenAIChatChoice(BaseModel):
    """Choice in OpenAI chat completion response."""

    index: int = 0
    message: OpenAIChatMessage
    finish_reason: str = "stop"


class OpenAIChatResponse(BaseModel):
    """Response for POST /v1/chat/completions (non-streaming)."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[OpenAIChatChoice]
    usage: OpenAIUsage = OpenAIUsage()


class OpenAIChatStreamDelta(BaseModel):
    """Delta in OpenAI chat streaming chunk."""

    role: str | None = None
    content: str | None = None


class OpenAIChatStreamChoice(BaseModel):
    """Choice in OpenAI chat streaming chunk."""

    index: int = 0
    delta: OpenAIChatStreamDelta
    finish_reason: str | None = None


class OpenAIChatStreamChunk(BaseModel):
    """Streaming chunk for POST /v1/chat/completions."""

    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: list[OpenAIChatStreamChoice]


class OpenAICompletionChoice(BaseModel):
    """Choice in OpenAI text completion response."""

    index: int = 0
    text: str
    finish_reason: str = "stop"


class OpenAICompletionResponse(BaseModel):
    """Response for POST /v1/completions (non-streaming)."""

    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: list[OpenAICompletionChoice]
    usage: OpenAIUsage = OpenAIUsage()


class OpenAICompletionStreamChoice(BaseModel):
    """Choice in OpenAI text completion streaming chunk."""

    index: int = 0
    text: str
    finish_reason: str | None = None


class OpenAICompletionStreamChunk(BaseModel):
    """Streaming chunk for POST /v1/completions."""

    id: str
    object: str = "text_completion"
    created: int
    model: str
    choices: list[OpenAICompletionStreamChoice]


class OpenAIModel(BaseModel):
    """Model object in OpenAI /v1/models response."""

    id: str
    object: str = "model"
    created: int
    owned_by: str = "anthropic"


class OpenAIModelList(BaseModel):
    """Response for GET /v1/models."""

    object: str = "list"
    data: list[OpenAIModel]
