"""PerformanceHarvester — daily scheduled agent that fetches Ayrshare analytics.

Runs once daily via uAgents Bureau scheduling.  For every post published in the
last 7 days it stores a PerformanceRecord in ``ctx.storage`` keyed as:

    perf:{brand_id}:{post_id}

The stored records are later consumed by the BrandPerformanceSummary builder
which the Head Agent queries before dispatching to the Strategist.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import httpx
from uagents import Agent, Context

from services.shared.models import PerformanceRecord, Platform

logger = logging.getLogger(__name__)

AYRSHARE_API_KEY = os.environ.get("AYRSHARE_API_KEY", "")
HARVESTER_SEED = os.environ.get("HARVESTER_SEED", "agentbuffer-harvester-seed-v1")
HARVESTER_PORT = int(os.environ.get("HARVESTER_PORT", "8006"))
HARVESTER_BRAND_ID = os.environ.get("HARVESTER_BRAND_ID", "brand-default")
AYRSHARE_BASE_URL = "https://app.ayrshare.com/api"

PLATFORM_MAP: dict[str, Platform] = {
    "twitter": Platform.X,
    "linkedin": Platform.LINKEDIN,
    "instagram": Platform.INSTAGRAM,
    "tiktok": Platform.TIKTOK,
    "youtube": Platform.YOUTUBE,
}

agent = Agent(
    name="AgentBuffer-PerformanceHarvester",
    seed=HARVESTER_SEED,
    port=HARVESTER_PORT,
)


async def fetch_post_analytics(post_id: str) -> dict | None:
    """Call Ayrshare ``/analytics/post`` for a single post."""
    if not AYRSHARE_API_KEY:
        logger.warning("No AYRSHARE_API_KEY set — skipping analytics fetch")
        return None

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{AYRSHARE_BASE_URL}/analytics/post",
            headers={
                "Authorization": f"Bearer {AYRSHARE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"id": post_id},
        )
        if resp.status_code == 200:
            return resp.json()
        logger.error(
            "Ayrshare analytics error for post %s: %s — %s",
            post_id,
            resp.status_code,
            resp.text,
        )
        return None


async def fetch_recent_posts() -> list[dict]:
    """Fetch posts published in the last 7 days from the Ayrshare history endpoint."""
    if not AYRSHARE_API_KEY:
        logger.warning("No AYRSHARE_API_KEY set — skipping history fetch")
        return []

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{AYRSHARE_BASE_URL}/history",
            headers={
                "Authorization": f"Bearer {AYRSHARE_API_KEY}",
                "Content-Type": "application/json",
            },
            params={"lastDays": 7},
        )
        if resp.status_code == 200:
            return resp.json() if isinstance(resp.json(), list) else []
        logger.error("Ayrshare history error: %s — %s", resp.status_code, resp.text)
        return []


def _parse_platform(raw: str | list) -> Platform:
    """Normalise Ayrshare platform strings to our Platform enum."""
    name = raw[0] if isinstance(raw, list) else raw
    return PLATFORM_MAP.get(name.lower(), Platform.INSTAGRAM)


def _extract_engagement(analytics: dict, platform_key: str) -> dict:
    """Pull engagement numbers from an Ayrshare analytics response."""
    data = analytics.get(platform_key, analytics)
    likes = int(data.get("likes", data.get("likeCount", 0)))
    shares = int(data.get("shares", data.get("shareCount", data.get("retweetCount", 0))))
    comments = int(data.get("comments", data.get("commentCount", data.get("replyCount", 0))))
    reach = int(data.get("reach", data.get("impressions", data.get("impressionCount", 0))))
    total_engagement = likes + shares + comments
    engagement_rate = (total_engagement / reach * 100) if reach > 0 else 0.0
    return {
        "likes": likes,
        "shares": shares,
        "comments": comments,
        "reach": reach,
        "engagement_rate": round(engagement_rate, 4),
    }


async def harvest(ctx: Context, brand_id: str) -> int:
    """Fetch analytics for recent posts and persist PerformanceRecords.

    Returns the number of records stored.
    """
    posts = await fetch_recent_posts()
    stored = 0

    for post in posts:
        post_id = post.get("id", post.get("postId", ""))
        if not post_id:
            continue

        analytics = await fetch_post_analytics(post_id)
        if analytics is None:
            continue

        platform = _parse_platform(post.get("platforms", post.get("platform", "instagram")))
        platform_key = platform.value

        engagement = _extract_engagement(analytics, platform_key)

        published_raw = post.get("created", post.get("scheduledDate", ""))
        try:
            published_at = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            published_at = datetime.now(tz=timezone.utc)

        content_type = post.get("mediaType", post.get("type", "text"))

        record = PerformanceRecord(
            post_id=post_id,
            platform=platform,
            published_at=published_at,
            content_type=content_type,
            **engagement,
        )

        ctx.storage.set(f"perf:{brand_id}:{post_id}", record.model_dump_json())
        stored += 1

    return stored


@agent.on_interval(period=86400)
async def daily_harvest(ctx: Context) -> None:
    """Scheduled task — runs once every 24 h."""
    brand_id = HARVESTER_BRAND_ID
    logger.info("PerformanceHarvester running daily harvest for brand %s", brand_id)
    try:
        count = await harvest(ctx, brand_id)
        logger.info("Harvested %d performance records for brand %s", count, brand_id)
    except Exception as exc:
        logger.error("Harvest failed for brand %s: %s", brand_id, exc)


if __name__ == "__main__":
    agent.run()
