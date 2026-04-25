"""ASI:One slot ranking endpoint — stubbed with mock data."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from gateway.auth import OrgId

router = APIRouter(prefix="/api", tags=["ranking"])


class RankSlotsRequest(BaseModel):
    slot_ids: list[str]


MOCK_RANKINGS = [
    {
        "slot_id": "slot-001",
        "rank": 1,
        "reasoning": "Strong brand voice alignment with ritual narrative.",
    },
    {
        "slot_id": "slot-005",
        "rank": 2,
        "reasoning": "Authentic craft-forward messaging drives engagement.",
    },
]


@router.post("/rank-slots")
async def rank_slots(body: RankSlotsRequest, org_id: OrgId) -> list[dict]:
    """Rank approved slots by predicted performance using ASI:One.

    Stub: returns mock rankings for the first two requested slot_ids.
    Real implementation: call ASI:One LLM with slot + brand context.
    """
    results = []
    for i, slot_id in enumerate(body.slot_ids[:5]):
        results.append(
            {
                "slot_id": slot_id,
                "rank": i + 1,
                "reasoning": MOCK_RANKINGS[i]["reasoning"]
                if i < len(MOCK_RANKINGS)
                else "Good content with solid brand alignment.",
            }
        )
    return results
