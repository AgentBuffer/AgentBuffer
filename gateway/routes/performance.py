"""Performance analytics endpoint — stubbed with mock data."""

from __future__ import annotations

from fastapi import APIRouter

from gateway.auth import OrgId

router = APIRouter(prefix="/api", tags=["performance"])


@router.get("/performance/{brand_id}")
async def get_performance(brand_id: str, org_id: OrgId) -> dict:
    """Return performance analytics for a brand.

    Stub: returns mock summary data.
    Real implementation: query performance_records table,
    call build_performance_summary().
    """
    return {
        "brand_id": brand_id,
        "top_formats": [
            {"format": "video", "avg_engagement": 4.2},
            {"format": "carousel", "avg_engagement": 3.8},
            {"format": "image", "avg_engagement": 2.9},
        ],
        "best_times": {
            "linkedin": "09:00",
            "x": "12:00",
            "instagram": "18:00",
        },
        "avoid_patterns": [
            "Generic discount CTAs",
            "Stock photography",
            "Hashtag-heavy captions",
        ],
        "records": [
            {
                "post_id": "post-001",
                "platform": "linkedin",
                "published_at": "2026-04-21T09:00:00Z",
                "content_type": "carousel",
                "likes": 142,
                "shares": 28,
                "comments": 15,
                "reach": 3200,
                "engagement_rate": 5.78,
            },
            {
                "post_id": "post-002",
                "platform": "x",
                "published_at": "2026-04-22T12:00:00Z",
                "content_type": "video",
                "likes": 89,
                "shares": 34,
                "comments": 7,
                "reach": 1800,
                "engagement_rate": 7.22,
            },
        ],
    }
