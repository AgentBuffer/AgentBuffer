"""Unit tests for MCP tool handlers."""

from __future__ import annotations

import json

import pytest

from src.mcp_server.campaign_store import _campaigns
from src.mcp_server.tools import handle_generate_campaign, handle_get_campaign_status


@pytest.fixture(autouse=True)
def _clear_store():
    """Reset the in-memory campaign store between tests."""
    _campaigns.clear()
    yield
    _campaigns.clear()


# ---------------------------------------------------------------------------
# generate_social_campaign
# ---------------------------------------------------------------------------


class TestGenerateCampaign:
    @pytest.mark.asyncio
    async def test_valid_request_returns_campaign_id(self):
        result = await handle_generate_campaign({
            "product_description": "EcoBottle — a self-cleaning water bottle that uses UV-C light",
            "target_platform": "instagram",
        })
        assert len(result) == 1
        data = json.loads(result[0]["text"])
        assert data["campaign_id"].startswith("campaign-")
        assert data["status"] == "queued"
        assert data["platform"] == "instagram"
        assert data["num_posts"] == 7

    @pytest.mark.asyncio
    async def test_custom_num_posts(self):
        result = await handle_generate_campaign({
            "product_description": "SaaS analytics dashboard for small businesses",
            "target_platform": "linkedin",
            "num_posts": 3,
        })
        data = json.loads(result[0]["text"])
        assert data["num_posts"] == 3

    @pytest.mark.asyncio
    async def test_invalid_platform_raises(self):
        with pytest.raises(Exception):
            await handle_generate_campaign({
                "product_description": "Some product description here for testing",
                "target_platform": "facebook",  # not supported
            })

    @pytest.mark.asyncio
    async def test_short_description_raises(self):
        with pytest.raises(Exception):
            await handle_generate_campaign({
                "product_description": "short",
                "target_platform": "x",
            })

    @pytest.mark.asyncio
    async def test_campaign_is_stored(self):
        result = await handle_generate_campaign({
            "product_description": "Premium dog food delivery subscription service",
            "target_platform": "tiktok",
        })
        data = json.loads(result[0]["text"])
        assert data["campaign_id"] in _campaigns


# ---------------------------------------------------------------------------
# get_campaign_status
# ---------------------------------------------------------------------------


class TestGetCampaignStatus:
    @pytest.mark.asyncio
    async def test_existing_campaign(self):
        # Create a campaign first
        gen_result = await handle_generate_campaign({
            "product_description": "AI-powered resume builder for job seekers worldwide",
            "target_platform": "linkedin",
        })
        campaign_id = json.loads(gen_result[0]["text"])["campaign_id"]

        status_result = await handle_get_campaign_status({"campaign_id": campaign_id})
        data = json.loads(status_result[0]["text"])
        assert data["campaign_id"] == campaign_id
        assert data["overall_status"] in ("queued", "running", "completed")
        assert len(data["stages"]) == 7

    @pytest.mark.asyncio
    async def test_nonexistent_campaign(self):
        result = await handle_get_campaign_status({"campaign_id": "campaign-doesnotexist"})
        assert result[0].get("isError") is True
        assert "No campaign found" in result[0]["text"]

    @pytest.mark.asyncio
    async def test_missing_campaign_id_raises(self):
        with pytest.raises(Exception):
            await handle_get_campaign_status({})
