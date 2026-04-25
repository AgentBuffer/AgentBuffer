"""Publish trigger endpoint — stubbed with mock data."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel

from gateway.auth import OrgId

router = APIRouter(prefix="/api", tags=["publish"])


class TriggerPublishRequest(BaseModel):
    slot_ids: list[str]


@router.post("/trigger-publish")
async def trigger_publish(body: TriggerPublishRequest, org_id: OrgId) -> list[dict]:
    """Publish selected approved slots to their target platforms.

    Stub: returns simulated success for all requested slots.
    Real implementation: call publish_slots() from the Publisher agent,
    update content_slots in DB, write agent_messages.
    """
    results = []
    for slot_id in body.slot_ids:
        results.append(
            {
                "slot_id": slot_id,
                "platform": "linkedin",
                "success": True,
                "permalink": f"https://linkedin.com/posts/lumen-coffee_{slot_id}",
                "error": None,
                "idempotency_key": f"idem-{slot_id}-{uuid4().hex[:8]}",
            }
        )
    return results
