"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Server settings
    host: str = "0.0.0.0"
    port: int = 11434  # Match Ollama's default port

    # Authentication
    api_key: str | None = None  # If set, requires Bearer token auth

    # Claude Agent SDK settings
    default_max_turns: int = 10

    # Default model if not specified
    default_model: str = "claude-sonnet-4-20250514"

    model_config = {
        "env_prefix": "OLLAMA_CLAUDE_",
        "env_file": ".env",
    }


settings = Settings()
