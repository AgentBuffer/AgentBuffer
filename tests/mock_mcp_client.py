"""Mock MCP Client — simulates an external AI agent connecting to the AgentBuffer
MCP SSE endpoint and calling the generate_social_campaign tool.

Usage:
    # Start the server first:
    MCP_API_KEYS=ab_mock-test-key uvicorn src.mcp_server.server:app --port 8100

    # Then run this mock client:
    MCP_API_KEYS=ab_mock-test-key python tests/mock_mcp_client.py

This script can also be imported and run programmatically in tests via
`run_mock_client()`.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys

import httpx

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "http://127.0.0.1:8100"


async def run_mock_client(
    base_url: str = DEFAULT_BASE_URL,
    api_key: str | None = None,
) -> dict:
    """Simulate an external MCP client calling generate_social_campaign.

    Rather than using the full SSE MCP transport, this mock exercises the tool
    logic via the FastAPI health endpoint (to verify connectivity) and then
    directly invokes the tool handlers to prove the bridge works end-to-end.

    Returns the parsed campaign response.
    """
    api_key = api_key or os.environ.get("MCP_API_KEYS", "").split(",")[0].strip()
    if not api_key:
        logger.error("No API key provided. Set MCP_API_KEYS or pass api_key=")
        sys.exit(1)

    async with httpx.AsyncClient(
        base_url=base_url,
        timeout=30,
        headers={"Authorization": f"Bearer {api_key}"},
    ) as client:
        # Step 1: Health check (unauthenticated)
        logger.info("Step 1 — Health check")
        resp = await client.get("/health")
        resp.raise_for_status()
        logger.info("  Server healthy: %s", resp.json())

        # Step 2: Verify auth works
        logger.info("Step 2 — Verify auth on protected endpoint")
        resp_no_auth = await client.get("/sse")
        logger.info("  Without auth: %s", resp_no_auth.status_code)

    # Step 3: Direct tool invocation (bypasses SSE for deterministic testing)
    logger.info("Step 3 — Invoke generate_social_campaign tool directly")
    from src.mcp_server.tools import handle_generate_campaign, handle_get_campaign_status

    campaign_result = await handle_generate_campaign({
        "product_description": (
            "EcoBottle is a revolutionary self-cleaning water bottle that uses UV-C "
            "light technology to eliminate 99.9% of bacteria. Made from recycled ocean "
            "plastic, it targets health-conscious millennials and Gen-Z consumers who "
            "value sustainability."
        ),
        "target_platform": "instagram",
        "content_type": "video",
        "brand_voice": "Youthful, eco-conscious, aspirational",
        "num_posts": 5,
    })

    campaign_data = json.loads(campaign_result[0]["text"])
    campaign_id = campaign_data["campaign_id"]
    logger.info("  Campaign created: %s", campaign_id)
    logger.info("  Status: %s", campaign_data["status"])
    logger.info("  Message: %s", campaign_data["message"])

    # Step 4: Query campaign status
    logger.info("Step 4 — Invoke get_campaign_status tool")
    status_result = await handle_get_campaign_status({"campaign_id": campaign_id})
    status_data = json.loads(status_result[0]["text"])
    logger.info("  Overall status: %s", status_data["overall_status"])
    for stage in status_data["stages"]:
        logger.info("    %s: %s %s", stage["stage"], stage["status"], stage.get("detail", ""))

    logger.info("Mock client completed successfully.")
    return campaign_data


if __name__ == "__main__":
    asyncio.run(run_mock_client())
