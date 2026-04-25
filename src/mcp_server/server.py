"""AgentBuffer MCP Server — SSE transport over FastAPI.

Exposes internal agent capabilities as standardised MCP Tools so that
external enterprise AI agents can trigger and monitor marketing campaigns.

Run:
    MCP_API_KEYS=<key1>,<key2> uvicorn src.mcp_server.server:app --host 0.0.0.0 --port 8100
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool
from starlette.responses import Response
from starlette.routing import Route

from src.mcp_server.auth import APIKeyMiddleware
from src.mcp_server.models import CampaignRequest, CampaignStatusRequest
from src.mcp_server.tools import handle_generate_campaign, handle_get_campaign_status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── MCP Server instance ──

mcp_server = Server("agentbuffer-mcp", version="0.1.0")

# ── Tool definitions ──

TOOLS: list[Tool] = [
    Tool(
        name="generate_social_campaign",
        description=(
            "Generate a social media marketing campaign for a product or business. "
            "Triggers the AgentBuffer multi-agent pipeline: brand analysis, content "
            "strategy, quality review, video/carousel generation, and publishing. "
            "Returns a campaign_id you can poll with get_campaign_status."
        ),
        inputSchema=CampaignRequest.model_json_schema(),
    ),
    Tool(
        name="get_campaign_status",
        description=(
            "Query the status of an ongoing or completed marketing campaign pipeline. "
            "Provide the campaign_id returned by generate_social_campaign. Returns "
            "per-stage status (intake, analysis, strategize, critique, video, publish, "
            "report) and a final summary when the campaign completes."
        ),
        inputSchema=CampaignStatusRequest.model_json_schema(),
    ),
]


@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """Return the catalogue of available MCP tools."""
    return TOOLS


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict | None) -> list[dict]:
    """Dispatch an MCP tool call to the appropriate handler."""
    arguments = arguments or {}
    if name == "generate_social_campaign":
        return await handle_generate_campaign(arguments)
    if name == "get_campaign_status":
        return await handle_get_campaign_status(arguments)
    return [{"type": "text", "text": f"Unknown tool: {name}", "isError": True}]


# ── FastAPI + SSE transport ──

sse_transport = SseServerTransport("/messages/")


async def handle_sse(request: Request) -> Response:
    """SSE GET endpoint — clients connect here to open an MCP session."""
    async with sse_transport.connect_sse(
        request.scope, request._receive, request._send
    ) as (read_stream, write_stream):
        await mcp_server.run(read_stream, write_stream, mcp_server.create_initialization_options())


async def handle_messages(request: Request) -> Response:
    """POST endpoint — clients send MCP messages here."""
    return await sse_transport.handle_post_message(request.scope, request._receive, request._send)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Wire up the MCP server to the SSE transport on startup."""
    logger.info("AgentBuffer MCP Server v0.1.0 starting")
    yield
    logger.info("AgentBuffer MCP Server shutting down")


app = FastAPI(
    title="AgentBuffer MCP Server",
    description="Model Context Protocol server for the AgentBuffer AI marketing agency.",
    version="0.1.0",
    lifespan=lifespan,
)

# Auth middleware — enforces API key on all non-public paths.
app.add_middleware(APIKeyMiddleware)


@app.get("/health")
async def health() -> dict:
    """Unauthenticated health check endpoint."""
    return {"status": "ok", "server": "agentbuffer-mcp", "version": "0.1.0"}


# Mount the SSE transport endpoints as Starlette routes.
app.router.routes.append(Route("/sse", endpoint=handle_sse))
app.router.routes.append(Route("/messages/", endpoint=handle_messages, methods=["POST"]))
