"""FastAPI application entry point for Ollama-Claude Bridge."""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .routers import chat, generate, models

app = FastAPI(
    title="Ollama-Claude Bridge",
    description="Ollama-compatible API service wrapping Claude Agent SDK",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(generate.router)
app.include_router(chat.router)
app.include_router(models.router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "Ollama-Claude Bridge is running"}


@app.get("/api/version")
async def version():
    """Return version information (Ollama-compatible)."""
    return {"version": "0.1.0"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for Ollama-compatible error responses."""
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)},
    )


def run():
    """Entry point for the CLI command."""
    uvicorn.run(
        "ollama_claude.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    run()
