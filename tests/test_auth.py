"""Unit tests for API key authentication middleware."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.mcp_server.auth import (
    APIKeyMiddleware,
    generate_api_key,
    reset_api_keys_cache,
    validate_api_key,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_KEY = "ab_test-key-alpha"
VALID_KEY_2 = "ab_test-key-beta"


@pytest.fixture(autouse=True)
def _reset_cache():
    """Reset the API key cache before and after every test."""
    reset_api_keys_cache()
    yield
    reset_api_keys_cache()


def _make_app() -> FastAPI:
    """Create a minimal FastAPI app with the auth middleware."""
    test_app = FastAPI()
    test_app.add_middleware(APIKeyMiddleware)

    @test_app.get("/protected")
    async def protected():
        return {"status": "ok"}

    @test_app.get("/health")
    async def health():
        return {"status": "healthy"}

    return test_app


# ---------------------------------------------------------------------------
# validate_api_key unit tests
# ---------------------------------------------------------------------------


class TestValidateAPIKey:
    def test_valid_key_accepted(self):
        with patch.dict(os.environ, {"MCP_API_KEYS": VALID_KEY}):
            assert validate_api_key(VALID_KEY) is True

    def test_invalid_key_rejected(self):
        with patch.dict(os.environ, {"MCP_API_KEYS": VALID_KEY}):
            assert validate_api_key("wrong-key") is False

    def test_empty_env_rejects_all(self):
        with patch.dict(os.environ, {"MCP_API_KEYS": ""}):
            assert validate_api_key("anything") is False

    def test_missing_env_rejects_all(self):
        env = os.environ.copy()
        env.pop("MCP_API_KEYS", None)
        with patch.dict(os.environ, env, clear=True):
            assert validate_api_key("anything") is False

    def test_multiple_keys(self):
        keys = f"{VALID_KEY},{VALID_KEY_2}"
        with patch.dict(os.environ, {"MCP_API_KEYS": keys}):
            assert validate_api_key(VALID_KEY) is True
            reset_api_keys_cache()
        with patch.dict(os.environ, {"MCP_API_KEYS": keys}):
            assert validate_api_key(VALID_KEY_2) is True

    def test_whitespace_trimmed(self):
        keys = f"  {VALID_KEY} , {VALID_KEY_2}  "
        with patch.dict(os.environ, {"MCP_API_KEYS": keys}):
            assert validate_api_key(VALID_KEY) is True


# ---------------------------------------------------------------------------
# generate_api_key
# ---------------------------------------------------------------------------


class TestGenerateAPIKey:
    def test_format(self):
        key = generate_api_key()
        assert key.startswith("ab_")
        assert len(key) > 10

    def test_uniqueness(self):
        keys = {generate_api_key() for _ in range(100)}
        assert len(keys) == 100


# ---------------------------------------------------------------------------
# Middleware integration tests (via TestClient)
# ---------------------------------------------------------------------------


class TestAPIKeyMiddleware:
    def test_missing_auth_header_returns_401(self):
        with patch.dict(os.environ, {"MCP_API_KEYS": VALID_KEY}):
            client = TestClient(_make_app())
            resp = client.get("/protected")
            assert resp.status_code == 401
            assert "Missing" in resp.json()["detail"]

    def test_malformed_auth_header_returns_401(self):
        with patch.dict(os.environ, {"MCP_API_KEYS": VALID_KEY}):
            client = TestClient(_make_app())
            resp = client.get("/protected", headers={"Authorization": "Basic abc123"})
            assert resp.status_code == 401

    def test_invalid_key_returns_403(self):
        with patch.dict(os.environ, {"MCP_API_KEYS": VALID_KEY}):
            client = TestClient(_make_app())
            resp = client.get("/protected", headers={"Authorization": "Bearer wrong"})
            assert resp.status_code == 403
            assert "Invalid" in resp.json()["detail"]

    def test_valid_key_passes(self):
        with patch.dict(os.environ, {"MCP_API_KEYS": VALID_KEY}):
            client = TestClient(_make_app())
            resp = client.get("/protected", headers={"Authorization": f"Bearer {VALID_KEY}"})
            assert resp.status_code == 200
            assert resp.json()["status"] == "ok"

    def test_health_endpoint_bypasses_auth(self):
        with patch.dict(os.environ, {"MCP_API_KEYS": VALID_KEY}):
            client = TestClient(_make_app())
            resp = client.get("/health")
            assert resp.status_code == 200

    def test_no_keys_configured_rejects_all(self):
        with patch.dict(os.environ, {"MCP_API_KEYS": ""}):
            client = TestClient(_make_app())
            resp = client.get("/protected", headers={"Authorization": "Bearer anything"})
            assert resp.status_code == 403
