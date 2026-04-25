"""Test that the mock MCP client's core tool invocations work end-to-end."""

from __future__ import annotations

import json

import pytest

from src.mcp_server.campaign_store import _campaigns
from src.mcp_server.tools import handle_generate_campaign, handle_get_campaign_status


@pytest.fixture(autouse=True)
def _clear():
    _campaigns.clear()
    yield
    _campaigns.clear()


@pytest.mark.asyncio
async def test_mock_client_generates_campaign():
    """Simulate the mock client flow: generate → check status."""
    # Step 1: Generate a campaign (same payload as mock_mcp_client.py)
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

    data = json.loads(campaign_result[0]["text"])
    assert data["campaign_id"].startswith("campaign-")
    assert data["platform"] == "instagram"
    assert data["num_posts"] == 5

    # Step 2: Check status
    status_result = await handle_get_campaign_status({"campaign_id": data["campaign_id"]})
    status_data = json.loads(status_result[0]["text"])
    assert status_data["campaign_id"] == data["campaign_id"]
    assert status_data["overall_status"] in ("queued", "running", "completed")
    assert len(status_data["stages"]) == 7

    # Verify store has the campaign
    assert data["campaign_id"] in _campaigns


@pytest.mark.asyncio
async def test_mock_client_full_round_trip():
    """Exercises the same flow as `python tests/mock_mcp_client.py` without HTTP."""
    # Multiple platforms
    for platform in ("linkedin", "tiktok", "youtube"):
        result = await handle_generate_campaign({
            "product_description": (
                "A premium dog food subscription for urban pet owners aged 25-40"
            ),
            "target_platform": platform,
            "num_posts": 3,
        })
        data = json.loads(result[0]["text"])
        assert data["platform"] == platform

        status = await handle_get_campaign_status({"campaign_id": data["campaign_id"]})
        assert "stages" in json.loads(status[0]["text"])
