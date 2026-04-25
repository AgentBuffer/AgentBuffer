"""PerformanceHarvester — daily scheduled agent that fetches platform analytics.

Runs once daily via uAgents Bureau scheduling.  For every post published in the
last 7 days it stores a PerformanceRecord in ``ctx.storage`` keyed as:

    perf:{brand_id}:{post_id}

The stored records are later consumed by the BrandPerformanceSummary builder
which the Head Agent queries before dispatching to the Strategist.

Uses per-platform adapters (services.publisher.adapters) to call each social
network's native analytics API directly — no third-party aggregator required.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from uagents import Agent, Context

from services.publisher.adapters.base import get_adapter
from services.shared.models import PerformanceRecord, Platform

logger = logging.getLogger(__name__)

HARVESTER_SEED = os.environ.get("HARVESTER_SEED", "agentbuffer-harvester-seed-v1")
HARVESTER_PORT = int(os.environ.get("HARVESTER_PORT", "8006"))
HARVESTER_BRAND_ID = os.environ.get("HARVESTER_BRAND_ID", "brand-default")

PLATFORM_MAP: dict[str, Platform] = {
    "twitter": Platform.X,
    "x": Platform.X,
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


async def fetch_post_analytics(post_id: str, platform: Platform) -> dict | None:
    """Fetch analytics for a single post via the platform-specific adapter."""
    adapter = get_adapter(platform)
    return await adapter.get_post_analytics(post_id)


async def fetch_recent_posts(platform: Platform) -> list[dict]:
    """Fetch posts published in the last 7 days via the platform-specific adapter."""
    adapter = get_adapter(platform)
    return await adapter.get_recent_posts(days=7)


def _parse_platform(raw: str | list) -> Platform:
    """Normalise platform strings to our Platform enum."""
    name = raw[0] if isinstance(raw, list) else raw
    return PLATFORM_MAP.get(name.lower(), Platform.INSTAGRAM)


def _extract_engagement(analytics: dict) -> dict:
    """Pull engagement numbers from an adapter analytics response."""
    likes = int(analytics.get("likes", 0))
    shares = int(analytics.get("shares", 0))
    comments = int(analytics.get("comments", 0))
    reach = int(analytics.get("reach", 0))
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
    stored = 0

    for platform in Platform:
        posts = await fetch_recent_posts(platform)

        for post in posts:
            post_id = post.get("id", post.get("postId", ""))
            if not post_id:
                continue

            analytics = await fetch_post_analytics(post_id, platform)
            if analytics is None:
                continue

            engagement = _extract_engagement(analytics)

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
