"""YouTube adapter — publishes via the YouTube Data API v3."""

from __future__ import annotations

import logging
import os

import httpx

from services.shared.models import ContentSlot, Platform, PublishResult

from .base import PlatformAdapter

logger = logging.getLogger(__name__)

YOUTUBE_ACCESS_TOKEN = os.environ.get("YOUTUBE_ACCESS_TOKEN", "")

API_BASE = "https://www.googleapis.com/youtube/v3"
UPLOAD_BASE = "https://www.googleapis.com/upload/youtube/v3"


class YouTubeAdapter(PlatformAdapter):
    """Publish and read analytics via the YouTube Data API v3."""

    async def publish(self, slot: ContentSlot, idempotency_key: str) -> PublishResult:
        if not YOUTUBE_ACCESS_TOKEN:
            logger.warning("No YOUTUBE_ACCESS_TOKEN — simulating publish for slot %s", slot.slot_id)
            return PublishResult(
                slot_id=slot.slot_id,
                platform=Platform.YOUTUBE,
                success=True,
                permalink=f"https://youtube.com/simulated/{slot.slot_id}",
                idempotency_key=idempotency_key,
            )

        try:
            metadata = {
                "snippet": {
                    "title": slot.caption[:100],
                    "description": slot.caption,
                    "categoryId": "22",
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False,
                },
            }

            if slot.scheduled_for:
                metadata["status"]["privacyStatus"] = "private"
                metadata["status"]["publishAt"] = slot.scheduled_for.isoformat()

            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{API_BASE}/videos",
                    headers={
                        "Authorization": f"Bearer {YOUTUBE_ACCESS_TOKEN}",
                        "Content-Type": "application/json",
                    },
                    params={"part": "snippet,status"},
                    json=metadata,
                )

            if resp.status_code in (200, 201):
                video_id = resp.json().get("id", "")
                return PublishResult(
                    slot_id=slot.slot_id,
                    platform=Platform.YOUTUBE,
                    success=True,
                    permalink=f"https://www.youtube.com/watch?v={video_id}",
                    idempotency_key=idempotency_key,
                )
            return PublishResult(
                slot_id=slot.slot_id,
                platform=Platform.YOUTUBE,
                success=False,
                error=f"YouTube API error: {resp.status_code} — {resp.text}",
                idempotency_key=idempotency_key,
            )
        except Exception as exc:
            return PublishResult(
                slot_id=slot.slot_id,
                platform=Platform.YOUTUBE,
                success=False,
                error=str(exc),
                idempotency_key=idempotency_key,
            )

    async def get_post_analytics(self, post_id: str) -> dict | None:
        if not YOUTUBE_ACCESS_TOKEN:
            logger.warning("No YOUTUBE_ACCESS_TOKEN — skipping analytics for %s", post_id)
            return None

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{API_BASE}/videos",
                    headers={"Authorization": f"Bearer {YOUTUBE_ACCESS_TOKEN}"},
                    params={"part": "statistics", "id": post_id},
                )
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                if items:
                    stats = items[0].get("statistics", {})
                    return {
                        "likes": int(stats.get("likeCount", 0)),
                        "shares": 0,
                        "comments": int(stats.get("commentCount", 0)),
                        "reach": int(stats.get("viewCount", 0)),
                    }
            logger.error("YouTube analytics error for %s: %s", post_id, resp.text)
        except Exception as exc:
            logger.error("YouTube analytics exception for %s: %s", post_id, exc)
        return None

    async def get_recent_posts(self, days: int = 7) -> list[dict]:
        logger.info("YouTube get_recent_posts not yet implemented — returning empty list")
        return []
