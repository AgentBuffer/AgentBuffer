"""Agent message feed endpoint — stubbed with mock data."""

from __future__ import annotations

from fastapi import APIRouter, Query

from gateway.auth import OrgId

router = APIRouter(prefix="/api", tags=["messages"])

MOCK_MESSAGES = [
    {
        "id": "msg-001",
        "from_agent": "strategist",
        "to_agent": "critic",
        "envelope_type": "slate_proposal",
        "payload": {"slate_id": "slate-001", "slot_count": 7},
        "signature": "0xab3f...e721",
        "created_at": "2026-04-28T14:14:00Z",
    },
    {
        "id": "msg-002",
        "from_agent": "critic",
        "to_agent": "strategist",
        "envelope_type": "rejection_notice",
        "payload": {"rejected_slots": [3], "reason": "Below 3.5 threshold"},
        "signature": "0xcd91...f482",
        "created_at": "2026-04-28T14:14:30Z",
    },
    {
        "id": "msg-003",
        "from_agent": "strategist",
        "to_agent": "critic",
        "envelope_type": "slate_revision",
        "payload": {"slate_id": "slate-001", "revised_slots": [3]},
        "signature": "0xef22...a193",
        "created_at": "2026-04-28T14:15:00Z",
    },
    {
        "id": "msg-004",
        "from_agent": "critic",
        "to_agent": "publisher",
        "envelope_type": "full_approval",
        "payload": {"slate_id": "slate-001", "approved_count": 7},
        "signature": "0x1a44...b304",
        "created_at": "2026-04-28T14:15:30Z",
    },
    {
        "id": "msg-005",
        "from_agent": "publisher",
        "to_agent": "ledger",
        "envelope_type": "publish_result",
        "payload": {"published": 5, "queued": 1, "failed": 0},
        "signature": "0x3b77...c815",
        "created_at": "2026-04-28T14:16:00Z",
    },
]


@router.get("/messages")
async def list_messages(
    org_id: OrgId,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict]:
    """Return agent-to-agent message envelopes for the live feed."""
    return MOCK_MESSAGES[:limit]
