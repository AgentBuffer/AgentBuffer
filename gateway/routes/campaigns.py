"""Campaign management endpoints — stubbed with mock data."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel

from gateway.auth import OrgId

router = APIRouter(prefix="/api", tags=["campaigns"])


class GenerateCampaignRequest(BaseModel):
    brand_id: str
    product_description: str
    target_platform: str = "linkedin"
    content_type: str = "auto"
    num_posts: int = 7


@router.post("/campaigns/generate", status_code=202)
async def generate_campaign(body: GenerateCampaignRequest, org_id: OrgId) -> dict:
    """Trigger the full Head Agent pipeline from the web UI.

    Stub: returns a mock campaign_id immediately.
    Real implementation: create campaigns row in Supabase,
    dispatch to Head Agent via ChatMessage or inline call.
    """
    campaign_id = f"campaign-{uuid4().hex[:12]}"
    return {
        "campaign_id": campaign_id,
        "status": "queued",
        "message": (
            f"Campaign queued for {body.target_platform}. "
            f"Generating {body.num_posts} content piece(s). "
            f"Poll GET /api/campaigns/{campaign_id}/status to track progress."
        ),
    }


@router.get("/campaigns/{campaign_id}/status")
async def campaign_status(campaign_id: str, org_id: OrgId) -> dict:
    """Poll campaign progress.

    Stub: returns a partially-completed pipeline.
    Real implementation: read from campaigns table in Supabase.
    """
    return {
        "campaign_id": campaign_id,
        "overall_status": "running",
        "stages": [
            {"stage": "intake", "status": "completed", "detail": "Payload accepted"},
            {
                "stage": "analysis",
                "status": "completed",
                "detail": "Marketing analysis generated",
            },
            {
                "stage": "strategize",
                "status": "running",
                "detail": "Generating 7-slot content slate...",
            },
            {"stage": "critique", "status": "pending", "detail": ""},
            {"stage": "video", "status": "pending", "detail": ""},
            {"stage": "publish", "status": "pending", "detail": ""},
            {"stage": "report", "status": "pending", "detail": ""},
        ],
        "result_summary": "",
    }
