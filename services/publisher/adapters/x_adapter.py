"""X / Twitter adapter — publishes via the X API v2 (tweepy)."""

from __future__ import annotations

import logging
import os

import httpx

from services.shared.models import ContentSlot, Platform, PublishResult

from .base import PlatformAdapter

logger = logging.getLogger(__name__)

X_CLIENT_ID = os.environ.get("X_CLIENT_ID", "")
X_CLIENT_SECRET = os.environ.get("X_CLIENT_SECRET", "")
X_ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN", "")
X_ACCESS_TOKEN_SECRET = os.environ.get("X_ACCESS_TOKEN_SECRET", "")
X_BEARER_TOKEN = os.environ.get("X_BEARER_TOKEN", "")

API_BASE = "https://api.x.com/2"


class XAdapter(PlatformAdapter):
    """Publish and read analytics via the X API v2."""

    async def publish(self, slot: ContentSlot, idempotency_key: str) -> PublishResult:
        if not X_BEARER_TOKEN:
            logger.warning("No X_BEARER_TOKEN set — simulating publish for slot %s", slot.slot_id)
            return PublishResult(
                slot_id=slot.slot_id,
                platform=Platform.X,
                success=True,
                permalink=f"https://x.com/simulated/{slot.slot_id}",
                idempotency_key=idempotency_key,
            )

        try:
            payload: dict = {"text": slot.caption}
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{API_BASE}/tweets",
                    headers={
                        "Authorization": f"Bearer {X_BEARER_TOKEN}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )

            if resp.status_code in (200, 201):
                data = resp.json().get("data", {})
                tweet_id = data.get("id", "")
                return PublishResult(
                    slot_id=slot.slot_id,
                    platform=Platform.X,
                    success=True,
                    permalink=f"https://x.com/i/status/{tweet_id}",
                    idempotency_key=idempotency_key,
                )
            return PublishResult(
                slot_id=slot.slot_id,
                platform=Platform.X,
                success=False,
                error=f"X API error: {resp.status_code} — {resp.text}",
                idempotency_key=idempotency_key,
            )
        except Exception as exc:
            return PublishResult(
                slot_id=slot.slot_id,
                platform=Platform.X,
                success=False,
                error=str(exc),
                idempotency_key=idempotency_key,
            )

    async def get_post_analytics(self, post_id: str) -> dict | None:
        if not X_BEARER_TOKEN:
            logger.warning("No X_BEARER_TOKEN — skipping analytics for post %s", post_id)
            return None

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{API_BASE}/tweets/{post_id}",
                    headers={"Authorization": f"Bearer {X_BEARER_TOKEN}"},
                    params={"tweet.fields": "public_metrics,created_at"},
                )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                metrics = data.get("public_metrics", {})
                return {
                    "likes": metrics.get("like_count", 0),
                    "shares": metrics.get("retweet_count", 0),
                    "comments": metrics.get("reply_count", 0),
                    "reach": metrics.get("impression_count", 0),
                }
            logger.error("X analytics error for %s: %s", post_id, resp.text)
        except Exception as exc:
            logger.error("X analytics exception for %s: %s", post_id, exc)
        return None

    async def get_recent_posts(self, days: int = 7) -> list[dict]:
        logger.info("X get_recent_posts not yet implemented — returning empty list")
        return []
