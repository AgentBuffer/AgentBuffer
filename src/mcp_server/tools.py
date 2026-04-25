"""MCP Tool definitions — the bridge between external LLM agents and internal pipelines."""

from __future__ import annotations

import logging
from uuid import uuid4

from src.mcp_server.campaign_store import (
    create_campaign,
    update_stage,
)
from src.mcp_server.campaign_store import (
    get_campaign_status as _store_get_status,
)
from src.mcp_server.models import (
    CampaignRequest,
    CampaignResponse,
    CampaignStatusRequest,
)

logger = logging.getLogger(__name__)


async def trigger_parent_agent(campaign_id: str, request: CampaignRequest) -> None:
    """Dispatch the campaign to the internal Head Agent pipeline.

    In a fully wired deployment this would send a ChatMessage to the Head Agent
    via Agentverse.  For the MCP MVP we simulate the hand-off by updating the
    campaign store, which keeps the MCP layer decoupled from uAgents internals.
    """
    update_stage(campaign_id, "intake", "running", "Parsing product description")
    logger.info(
        "Campaign %s dispatched to parent agent for platform=%s",
        campaign_id,
        request.target_platform,
    )
    # The actual integration point would be:
    #   from services.head_agent.agent import handle_message
    #   await handle_message(ctx, sender, chat_msg)
    # For now we mark intake as completed to prove the bridge works.
    update_stage(campaign_id, "intake", "completed", "Payload accepted")
    update_stage(campaign_id, "analysis", "running", "Generating marketing analysis")


async def handle_generate_campaign(arguments: dict) -> list[dict]:
    """MCP tool handler: generate_social_campaign.

    Validates the incoming payload via Pydantic, creates a campaign record,
    and triggers the parent agent pipeline.
    """
    request = CampaignRequest(**arguments)

    campaign_id = f"campaign-{uuid4().hex[:12]}"
    response = CampaignResponse(
        campaign_id=campaign_id,
        status="queued",
        message=(
            f"Campaign queued for {request.target_platform.value}. "
            f"Generating {request.num_posts} content piece(s). "
            f"Use get_campaign_status with campaign_id='{campaign_id}' to track progress."
        ),
        platform=request.target_platform,
        num_posts=request.num_posts,
    )

    create_campaign(campaign_id, response)
    await trigger_parent_agent(campaign_id, request)

    return [{"type": "text", "text": response.model_dump_json(indent=2)}]


async def handle_get_campaign_status(arguments: dict) -> list[dict]:
    """MCP tool handler: get_campaign_status.

    Returns the current pipeline status for a given campaign_id.
    """
    req = CampaignStatusRequest(**arguments)
    status = _store_get_status(req.campaign_id)

    if status is None:
        return [
            {
                "type": "text",
                "text": f"No campaign found with id '{req.campaign_id}'. "
                "Please provide a valid campaign_id from a previous generate_social_campaign call.",
                "isError": True,
            }
        ]

    return [{"type": "text", "text": status.model_dump_json(indent=2)}]
