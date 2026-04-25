"""FastAPI gateway — REST API bridging the Next.js frontend to internal agents.

All endpoints are currently stubbed with mock JSON data that matches the
schemas defined in ``docs/backend_gap_analysis.md``. Replace stubs with
real Supabase queries and agent calls as each phase is implemented.

Run:
    uvicorn gateway.main:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from gateway.routes import (
    assets,
    brands,
    campaigns,
    dead_letters,
    designs,
    messages,
    performance,
    publish,
    ranking,
    slots,
)

app = FastAPI(
    title="AgentBuffer Gateway",
    description="REST API for the AgentBuffer multi-agent marketing platform.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

USE_APPROVAL_QUEUE = os.environ.get("USE_APPROVAL_QUEUE", "true").lower() == "true"

# Mount all route routers
app.include_router(brands.router)
app.include_router(slots.router)
app.include_router(messages.router)
app.include_router(ranking.router)
app.include_router(publish.router)
app.include_router(campaigns.router)
app.include_router(performance.router)
app.include_router(assets.router)
app.include_router(designs.router)
app.include_router(dead_letters.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "gateway", "version": "0.1.0"}


def _monday_of(dt: datetime) -> datetime:
    """Return midnight UTC of the Monday in the week containing *dt*."""
    return (dt - timedelta(days=dt.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)


@app.get("/brands/{brand_id}/calendar")
async def calendar(
    brand_id: str,
    week_start: str | None = Query(default=None, description="YYYY-MM-DD"),
) -> dict:
    """Return all posts for a 7-day window.

    Reads from approval_queue first; falls back to the Strategist slate
    if the approval queue feature is not present.

    Currently returns an empty stub — real implementation will read from
    ctx.storage or Supabase once the gateway is wired to the agent
    storage layer.
    """
    if week_start:
        start = datetime.strptime(week_start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        start = _monday_of(datetime.now(tz=timezone.utc))

    return {
        "brand_id": brand_id,
        "week_start": start.strftime("%Y-%m-%d"),
        "posts": [],
    }
