"""API Key authentication middleware for the MCP SSE transport layer."""

from __future__ import annotations

import hmac
import os
import secrets

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

# Keys are loaded from the MCP_API_KEYS env var (comma-separated).
# If the env var is empty the middleware rejects all requests.
_VALID_API_KEYS: set[str] | None = None

# Paths that bypass authentication (health check, OpenAPI docs).
PUBLIC_PATHS: set[str] = {"/health", "/docs", "/openapi.json", "/redoc"}


def _load_api_keys() -> set[str]:
    """Load API keys from the environment (comma-separated)."""
    raw = os.environ.get("MCP_API_KEYS", "")
    keys = {k.strip() for k in raw.split(",") if k.strip()}
    return keys


def get_valid_api_keys() -> set[str]:
    """Return the cached set of valid API keys, loading on first access."""
    global _VALID_API_KEYS
    if _VALID_API_KEYS is None:
        _VALID_API_KEYS = _load_api_keys()
    return _VALID_API_KEYS


def reset_api_keys_cache() -> None:
    """Reset the cached API keys (useful for testing)."""
    global _VALID_API_KEYS
    _VALID_API_KEYS = None


def _constant_time_compare(a: str, b: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks."""
    return hmac.compare_digest(a.encode(), b.encode())


def validate_api_key(api_key: str) -> bool:
    """Check whether *api_key* is in the set of valid keys."""
    valid_keys = get_valid_api_keys()
    if not valid_keys:
        return False
    return any(_constant_time_compare(api_key, vk) for vk in valid_keys)


def generate_api_key() -> str:
    """Generate a cryptographically secure API key."""
    return f"ab_{secrets.token_urlsafe(32)}"


class APIKeyMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware that enforces Bearer-token API key auth on every request.

    Usage:
        app.add_middleware(APIKeyMiddleware)

    Clients must send:
        Authorization: Bearer <api_key>
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Allow public paths through without auth.
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Missing or malformed Authorization header."
                    " Expected: Bearer <api_key>"
                },
            )

        token = auth_header[len("Bearer "):]
        if not validate_api_key(token):
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid API key."},
            )

        return await call_next(request)
