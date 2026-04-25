"""Dead letter queue endpoint — stubbed with mock data."""

from __future__ import annotations

from fastapi import APIRouter, Query

from gateway.auth import OrgId

router = APIRouter(prefix="/api", tags=["dead-letters"])


@router.get("/dead-letters")
async def list_dead_letters(
    org_id: OrgId,
    resolved: bool = Query(default=False),
) -> list[dict]:
    """Return failed publish attempts for retry/debugging.

    Stub: returns an empty list (no failures).
    Real implementation: query dead_letters table in Supabase.
    """
    if resolved:
        return []
    return [
        {
            "id": "dl-001",
            "slot_id": "slot-003",
            "error_message": "Ayrshare API error: 429 — Rate limit exceeded",
            "error_code": "RATE_LIMIT",
            "retry_count": 2,
            "resolved": False,
            "created_at": "2026-04-28T14:20:00Z",
        }
    ]
