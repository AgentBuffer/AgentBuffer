"""FastAPI gateway — placeholder. Read-only API that forwards user JWT."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Query

app = FastAPI(title="AgentBuffer Gateway")

USE_APPROVAL_QUEUE = os.environ.get("USE_APPROVAL_QUEUE", "true").lower() == "true"


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
