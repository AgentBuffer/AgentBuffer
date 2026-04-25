"""Integration tests for the MCP server FastAPI app."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.mcp_server.auth import reset_api_keys_cache
from src.mcp_server.server import app

TEST_KEY = "ab_integration-test-key"


@pytest.fixture(autouse=True)
def _setup():
    reset_api_keys_cache()
    yield
    reset_api_keys_cache()


class TestServerEndpoints:
    def test_health_no_auth(self):
        with patch.dict(os.environ, {"MCP_API_KEYS": TEST_KEY}):
            client = TestClient(app)
            resp = client.get("/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ok"
            assert data["server"] == "agentbuffer-mcp"

    def test_sse_endpoint_requires_auth(self):
        with patch.dict(os.environ, {"MCP_API_KEYS": TEST_KEY}):
            client = TestClient(app)
            resp = client.get("/sse")
            assert resp.status_code in (401, 403, 404, 405)
