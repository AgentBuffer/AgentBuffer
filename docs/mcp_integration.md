# MCP Server Integration — Architecture & Usage

## Overview

AgentBuffer exposes its internal multi-agent marketing pipeline as a
**Model Context Protocol (MCP)** server. This allows external enterprise AI
agents (Claude, GPT, custom LLM orchestrators) to programmatically trigger
and monitor marketing campaigns via a standardised tool-calling interface.

```
External LLM Agent
       │
       │  MCP protocol (SSE transport)
       ▼
┌──────────────────────────────┐
│  FastAPI + SSE Transport     │  ← API Key auth middleware
│  src/mcp_server/server.py    │
├──────────────────────────────┤
│  MCP Tool Handlers           │
│  src/mcp_server/tools.py     │
├──────────────────────────────┤
│  Internal Agent Pipeline     │
│  services/head_agent/ →      │
│    Strategist → Critic →     │
│    Video Creator → Publisher  │
└──────────────────────────────┘
```

## Transport Layer

The server uses **Server-Sent Events (SSE)** over HTTP as the MCP transport.
SSE provides a persistent, one-directional stream from server to client,
while the client sends requests via standard HTTP POST. This is the
recommended transport for remote MCP servers that need to work across
networks and firewalls.

| Endpoint | Method | Description |
|---|---|---|
| `GET  /health` | GET | Unauthenticated health check |
| `GET  /sse` | GET | SSE stream (MCP session) |
| `POST /messages/` | POST | MCP message ingestion |

## Authentication

Every request (except `/health`) must include a valid API key:

```
Authorization: Bearer ab_<your_api_key>
```

API keys are configured via the `MCP_API_KEYS` environment variable
(comma-separated for multiple clients):

```bash
export MCP_API_KEYS="ab_key1,ab_key2"
```

Generate a new key:

```python
from src.mcp_server.auth import generate_api_key
print(generate_api_key())  # e.g. ab_7x9K...
```

## Available MCP Tools

### `generate_social_campaign`

Triggers the full AgentBuffer marketing pipeline for a product.

**Input Schema:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `product_description` | string (10-5000 chars) | Yes | Detailed description of the product/business |
| `target_platform` | enum | Yes | `linkedin`, `x`, `instagram`, `tiktok`, `youtube` |
| `content_type` | enum | No | `video`, `carousel`, `image`, `auto` (default: `auto`) |
| `brand_voice` | string | No | Optional tone/voice guidance |
| `num_posts` | integer (1-30) | No | Number of content pieces (default: 7) |

**Output:** Returns a `campaign_id` and status message. Poll with
`get_campaign_status` to track progress.

### `get_campaign_status`

Query the status of a running or completed campaign.

**Input Schema:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `campaign_id` | string | Yes | ID from `generate_social_campaign` |

**Output:** Per-stage status (intake → analysis → strategize → critique →
video → publish → report) plus a final summary when complete.

## Running the Server

```bash
# 1. Activate the virtual environment
source .venv/bin/activate

# 2. Set API keys
export MCP_API_KEYS="ab_your_key_here"

# 3. Start the server
PYTHONPATH=. uvicorn src.mcp_server.server:app --host 0.0.0.0 --port 8100
```

## Connecting an External AI Agent

Any MCP-compatible client can connect. Example using the Python MCP SDK:

```python
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

async with sse_client(
    url="http://your-server:8100/sse",
    headers={"Authorization": "Bearer ab_your_key"},
) as (read_stream, write_stream):
    async with ClientSession(read_stream, write_stream) as session:
        await session.initialize()

        # List available tools
        tools = await session.list_tools()

        # Trigger a campaign
        result = await session.call_tool(
            "generate_social_campaign",
            arguments={
                "product_description": "EcoBottle — a self-cleaning water bottle...",
                "target_platform": "instagram",
            },
        )
```

## Security Considerations

- **Request validation**: All tool inputs are validated against strict Pydantic
  schemas before reaching the agent pipeline. Malformed or oversized payloads
  are rejected with descriptive error messages.
- **Constant-time comparison**: API keys are compared using HMAC-based
  constant-time comparison to prevent timing attacks.
- **Rate limiting**: Not yet implemented. Recommended for production via a
  reverse proxy (nginx, Cloudflare) or FastAPI middleware.
- **TLS**: The server itself runs plain HTTP. Deploy behind a TLS-terminating
  reverse proxy for production use.

## Project Structure

```
src/mcp_server/
├── __init__.py          # Package marker
├── server.py            # FastAPI app + MCP Server + SSE transport
├── tools.py             # MCP tool handlers (generate_social_campaign, get_campaign_status)
├── models.py            # Pydantic request/response schemas
├── auth.py              # API key middleware
└── campaign_store.py    # In-memory campaign state (swap for DB in prod)

tests/
├── test_auth.py         # API key middleware unit tests
└── mock_mcp_client.py   # End-to-end mock client for SSE endpoint
```
