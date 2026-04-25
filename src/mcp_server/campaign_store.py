"""In-memory campaign state store.

In production this would be backed by Supabase/PostgreSQL, but for the MCP
integration MVP we keep an in-process dict keyed by campaign_id.
"""

from __future__ import annotations

import threading
from typing import Any

from src.mcp_server.models import (
    CampaignResponse,
    CampaignStatusResponse,
    PipelineStageStatus,
)

_lock = threading.Lock()
_campaigns: dict[str, dict[str, Any]] = {}

# The pipeline stages in execution order.
PIPELINE_STAGES = ["intake", "analysis", "strategize", "critique", "video", "publish", "report"]


def create_campaign(campaign_id: str, response: CampaignResponse) -> None:
    """Register a new campaign and initialise its stage tracking."""
    stages = [
        PipelineStageStatus(stage=s, status="pending")
        for s in PIPELINE_STAGES
    ]
    with _lock:
        _campaigns[campaign_id] = {
            "response": response,
            "overall_status": "queued",
            "stages": stages,
            "result_summary": "",
        }


def update_stage(campaign_id: str, stage: str, status: str, detail: str = "") -> None:
    """Update a single stage within a campaign."""
    with _lock:
        campaign = _campaigns.get(campaign_id)
        if not campaign:
            return
        for s in campaign["stages"]:
            if s.stage == stage:
                s.status = status
                s.detail = detail
                break
        # Derive overall status.
        statuses = {s.status for s in campaign["stages"]}
        if "failed" in statuses:
            campaign["overall_status"] = "failed"
        elif "running" in statuses:
            campaign["overall_status"] = "running"
        elif all(s == "completed" for s in statuses):
            campaign["overall_status"] = "completed"


def complete_campaign(campaign_id: str, summary: str) -> None:
    """Mark the entire campaign as completed with a summary."""
    with _lock:
        campaign = _campaigns.get(campaign_id)
        if not campaign:
            return
        campaign["overall_status"] = "completed"
        campaign["result_summary"] = summary


def get_campaign_status(campaign_id: str) -> CampaignStatusResponse | None:
    """Return the current status snapshot for a campaign."""
    with _lock:
        campaign = _campaigns.get(campaign_id)
        if not campaign:
            return None
        return CampaignStatusResponse(
            campaign_id=campaign_id,
            overall_status=campaign["overall_status"],
            stages=list(campaign["stages"]),
            result_summary=campaign["result_summary"],
        )
