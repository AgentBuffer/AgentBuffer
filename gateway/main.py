"""FastAPI gateway — serves the Next.js dashboard and proxies to agents."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="AgentBuffer Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

USE_APPROVAL_QUEUE = os.environ.get("USE_APPROVAL_QUEUE", "true").lower() == "true"

# ── In-memory stores (replaced by Supabase / agent storage in production) ──

_brands: dict[str, dict] = {}
_slots: dict[str, dict] = {}
_messages: list[dict] = []


# ── Request schemas ──


class ManualPostBody(BaseModel):
    platform: str
    scheduled_for: str
    content_text: str


class RankSlotsBody(BaseModel):
    slot_ids: list[str]


class TriggerPublishBody(BaseModel):
    slot_ids: list[str]


# ── Helpers ──


def _monday_of(dt: datetime) -> datetime:
    """Return midnight UTC of the Monday in the week containing *dt*."""
    return (dt - timedelta(days=dt.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)


# ── Calendar endpoint (existing) ──


@app.get("/brands/{brand_id}/calendar")
async def calendar(
    brand_id: str,
    week_start: str | None = Query(default=None, description="YYYY-MM-DD"),
) -> dict:
    """Return all posts for a 7-day window."""
    if week_start:
        start = datetime.strptime(week_start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        start = _monday_of(datetime.now(tz=timezone.utc))

    end = start + timedelta(days=7)
    posts = (
        [
            s
            for s in _slots.values()
            if start
            <= datetime.fromisoformat(s["scheduled_for"]).replace(tzinfo=timezone.utc)
            < end
        ]
        if _slots
        else []
    )

    return {
        "brand_id": brand_id,
        "week_start": start.strftime("%Y-%m-%d"),
        "posts": posts,
    }


# ── Slot action endpoints ──


@app.post("/api/slots/{slot_id}/approve")
async def approve_slot(slot_id: str) -> dict:
    """Approve a content slot."""
    if slot_id in _slots:
        _slots[slot_id]["status"] = "approved"
    return {"slot_id": slot_id, "status": "approved"}


@app.post("/api/slots/{slot_id}/skip")
async def skip_slot(slot_id: str) -> dict:
    """Skip a content slot."""
    if slot_id in _slots:
        _slots[slot_id]["status"] = "skipped"
    return {"slot_id": slot_id, "status": "skipped"}


@app.post("/api/slots/{slot_id}/regenerate")
async def regenerate_slot(slot_id: str) -> dict:
    """Regenerate a content slot (stub — marks as pending)."""
    if slot_id in _slots:
        _slots[slot_id]["status"] = "pending"
    return {"slot_id": slot_id, "status": "pending"}


@app.post("/api/slots/manual")
async def add_manual_post(body: ManualPostBody) -> dict:
    """Add a manual post."""
    slot_id = f"slot-manual-{uuid4().hex[:8]}"
    slot = {
        "slot_id": slot_id,
        "slot_number": len(_slots) + 1,
        "caption": body.content_text,
        "image_prompt": "",
        "platform": body.platform,
        "scheduled_for": body.scheduled_for,
        "image_url": None,
        "status": "approved",
    }
    _slots[slot_id] = slot
    return slot


# ── Brand & data endpoints ──


@app.get("/api/brands")
async def list_brands() -> list[dict]:
    """Return list of brands."""
    if _brands:
        return list(_brands.values())
    return [
        {
            "brand_id": "brand-default",
            "org_id": "org-default",
            "name": "Default Brand",
            "tagline": "",
            "voice_description": "",
            "target_audience": "",
            "color_palette": [],
            "logo_url": None,
            "sample_captions": [],
            "industry": "",
        }
    ]


@app.get("/api/slots")
async def list_slots() -> list[dict]:
    """Return all content slots."""
    return list(_slots.values())


@app.get("/api/messages")
async def list_messages() -> list[dict]:
    """Return agent message envelopes."""
    return _messages


@app.post("/api/rank-slots")
async def rank_slots(body: RankSlotsBody) -> list[dict]:
    """Rank slots (stub — returns ranked in order given)."""
    return [
        {"slot_id": sid, "rank": i + 1, "reasoning": "Ranked by submission order."}
        for i, sid in enumerate(body.slot_ids)
    ]


@app.post("/api/trigger-publish")
async def trigger_publish(body: TriggerPublishBody) -> list[dict]:
    """Trigger publishing of slots (stub — marks as published)."""
    results = []
    for sid in body.slot_ids:
        slot = _slots.get(sid)
        platform = slot["platform"] if slot else "unknown"
        if slot:
            slot["status"] = "published"
        results.append(
            {
                "slot_id": sid,
                "platform": platform,
                "success": True,
                "permalink": f"https://{platform}.com/simulated/{sid}",
                "error": None,
                "idempotency_key": f"idem-{sid}-{uuid4().hex[:6]}",
            }
        )
    return results
