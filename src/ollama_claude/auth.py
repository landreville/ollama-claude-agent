"""Authentication middleware for Bearer token verification."""

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import settings

security = HTTPBearer(auto_error=False)


async def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str | None:
    """Verify Bearer token if API key is configured.

    Args:
        credentials: The HTTP authorization credentials from the request.

    Returns:
        The validated token if authentication succeeded, or None if no auth required.

    Raises:
        HTTPException: If authentication is required but fails.
    """
    # If no API key is configured, allow all requests
    if not settings.api_key:
        return None

    # API key is configured, require valid Bearer token
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required",
        )

    if credentials.credentials != settings.api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    return credentials.credentials
