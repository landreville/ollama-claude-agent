# syntax=docker/dockerfile:1

FROM python:3.12-slim

# Install Node.js (required for Claude CLI) and other dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Claude CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ src/

# Install Python dependencies
RUN pip install --no-cache-dir .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Create .claude directory for credentials mount
RUN mkdir -p /home/appuser/.claude && chown -R appuser:appuser /home/appuser/.claude

USER appuser

# Expose the default Ollama port
EXPOSE 11434

# Set environment variables
ENV OLLAMA_CLAUDE_HOST=0.0.0.0
ENV OLLAMA_CLAUDE_PORT=11434

# Run the application
CMD ["ollama-claude"]
