"""FastAPI gateway — REST API bridging the Next.js frontend to internal agents.

All endpoints are currently stubbed with mock JSON data that matches the
schemas defined in ``docs/backend_gap_analysis.md``. Replace stubs with
real Supabase queries and agent calls as each phase is implemented.

Run:
    uvicorn gateway.main:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

from fastapi import FastAPI
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
