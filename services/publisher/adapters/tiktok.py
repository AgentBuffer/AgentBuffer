"""TikTok adapter — publishes via the TikTok Content Posting API."""

from __future__ import annotations

import logging
import os

import httpx

from services.shared.models import ContentSlot, Platform, PublishResult

from .base import PlatformAdapter

logger = logging.getLogger(__name__)

TIKTOK_ACCESS_TOKEN = os.environ.get("TIKTOK_ACCESS_TOKEN", "")

API_BASE = "https://open.tiktokapis.com/v2"


class TikTokAdapter(PlatformAdapter):
    """Publish and read analytics via the TikTok Content Posting API."""

    async def publish(self, slot: ContentSlot, idempotency_key: str) -> PublishResult:
        if not TIKTOK_ACCESS_TOKEN:
            logger.warning("No TIKTOK_ACCESS_TOKEN — simulating publish for slot %s", slot.slot_id)
            return PublishResult(
                slot_id=slot.slot_id,
                platform=Platform.TIKTOK,
                success=True,
                permalink=f"https://tiktok.com/simulated/{slot.slot_id}",
                idempotency_key=idempotency_key,
            )

        try:
            payload = {
                "post_info": {
                    "title": slot.caption[:150],
                    "privacy_level": "PUBLIC_TO_EVERYONE",
                    "disable_duet": False,
                    "disable_comment": False,
                    "disable_stitch": False,
                },
                "source_info": {
                    "source": "PULL_FROM_URL",
                    "video_url": slot.image_url or "",
                },
            }

            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{API_BASE}/post/publish/video/init/",
                    headers={
                        "Authorization": f"Bearer {TIKTOK_ACCESS_TOKEN}",
                        "Content-Type": "application/json; charset=UTF-8",
                    },
                    json=payload,
                )

            if resp.status_code == 200:
                data = resp.json().get("data", {})
                publish_id = data.get("publish_id", "")
                return PublishResult(
                    slot_id=slot.slot_id,
                    platform=Platform.TIKTOK,
                    success=True,
                    permalink=f"https://www.tiktok.com/publish/{publish_id}",
                    idempotency_key=idempotency_key,
                )
            return PublishResult(
                slot_id=slot.slot_id,
                platform=Platform.TIKTOK,
                success=False,
                error=f"TikTok API error: {resp.status_code} — {resp.text}",
                idempotency_key=idempotency_key,
            )
        except Exception as exc:
            return PublishResult(
                slot_id=slot.slot_id,
                platform=Platform.TIKTOK,
                success=False,
                error=str(exc),
                idempotency_key=idempotency_key,
            )

    async def get_post_analytics(self, post_id: str) -> dict | None:
        if not TIKTOK_ACCESS_TOKEN:
            logger.warning("No TIKTOK_ACCESS_TOKEN — skipping analytics for %s", post_id)
            return None

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{API_BASE}/video/query/",
                    headers={
                        "Authorization": f"Bearer {TIKTOK_ACCESS_TOKEN}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "filters": {"video_ids": [post_id]},
                        "fields": ["like_count", "comment_count", "share_count", "view_count"],
                    },
                )
            if resp.status_code == 200:
                videos = resp.json().get("data", {}).get("videos", [])
                if videos:
                    v = videos[0]
                    return {
                        "likes": v.get("like_count", 0),
                        "shares": v.get("share_count", 0),
                        "comments": v.get("comment_count", 0),
                        "reach": v.get("view_count", 0),
                    }
            logger.error("TikTok analytics error for %s: %s", post_id, resp.text)
        except Exception as exc:
            logger.error("TikTok analytics exception for %s: %s", post_id, exc)
        return None

    async def get_recent_posts(self, days: int = 7) -> list[dict]:
        logger.info("TikTok get_recent_posts not yet implemented — returning empty list")
        return []
