"""Asset generation endpoints — stubbed with mock data."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel

from gateway.auth import OrgId

router = APIRouter(prefix="/api", tags=["assets"])


class GenerateAssetsRequest(BaseModel):
    slot_ids: list[str]
    asset_type: str = "auto"  # carousel | video | auto


@router.post("/assets/generate", status_code=202)
async def generate_assets(body: GenerateAssetsRequest, org_id: OrgId) -> dict:
    """Trigger carousel or video generation for approved slots.

    Stub: returns a mock job_id immediately.
    Real implementation: route to Carousel Creator or Video Creator,
    update content_slots with generated asset URLs.
    """
    job_id = f"asset-job-{uuid4().hex[:8]}"
    return {
        "job_id": job_id,
        "status": "queued",
        "slots_queued": len(body.slot_ids),
    }
