#!/bin/sh
set -e

echo "Installing package in editable mode..."
pip install -e ".[dev]" --quiet

exec python -m uvicorn ollama_claude.main:app \
    --host 0.0.0.0 --port 11434 \
    --reload --reload-dir /app/src
