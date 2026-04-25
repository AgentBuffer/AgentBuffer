"""Instagram adapter — publishes via the Instagram Graph API."""

from __future__ import annotations

import logging
import os

import httpx

from services.shared.models import ContentSlot, Platform, PublishResult

from .base import PlatformAdapter

logger = logging.getLogger(__name__)

META_APP_ID = os.environ.get("META_APP_ID", "")
META_APP_SECRET = os.environ.get("META_APP_SECRET", "")
INSTAGRAM_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_ACCOUNT_ID = os.environ.get("INSTAGRAM_ACCOUNT_ID", "")

GRAPH_BASE = "https://graph.instagram.com/v21.0"


class InstagramAdapter(PlatformAdapter):
    """Publish and read analytics via the Instagram Graph API."""

    async def publish(self, slot: ContentSlot, idempotency_key: str) -> PublishResult:
        if not INSTAGRAM_ACCESS_TOKEN or not INSTAGRAM_ACCOUNT_ID:
            logger.warning(
                "No Instagram credentials — simulating publish for slot %s",
                slot.slot_id,
            )
            return PublishResult(
                slot_id=slot.slot_id,
                platform=Platform.INSTAGRAM,
                success=True,
                permalink=f"https://instagram.com/simulated/{slot.slot_id}",
                idempotency_key=idempotency_key,
            )

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                # Step 1: create media container
                container_payload: dict = {
                    "caption": slot.caption,
                    "access_token": INSTAGRAM_ACCESS_TOKEN,
                }
                if slot.image_url:
                    container_payload["image_url"] = slot.image_url

                resp = await client.post(
                    f"{GRAPH_BASE}/{INSTAGRAM_ACCOUNT_ID}/media",
                    data=container_payload,
                )

                if resp.status_code != 200:
                    return PublishResult(
                        slot_id=slot.slot_id,
                        platform=Platform.INSTAGRAM,
                        success=False,
                        error=f"Instagram container error: {resp.status_code} — {resp.text}",
                        idempotency_key=idempotency_key,
                    )

                container_id = resp.json().get("id")

                # Step 2: publish the container
                pub_resp = await client.post(
                    f"{GRAPH_BASE}/{INSTAGRAM_ACCOUNT_ID}/media_publish",
                    data={
                        "creation_id": container_id,
                        "access_token": INSTAGRAM_ACCESS_TOKEN,
                    },
                )

                if pub_resp.status_code == 200:
                    media_id = pub_resp.json().get("id", "")
                    return PublishResult(
                        slot_id=slot.slot_id,
                        platform=Platform.INSTAGRAM,
                        success=True,
                        permalink=f"https://www.instagram.com/p/{media_id}/",
                        idempotency_key=idempotency_key,
                    )
                return PublishResult(
                    slot_id=slot.slot_id,
                    platform=Platform.INSTAGRAM,
                    success=False,
                    error=f"Instagram publish error: {pub_resp.status_code} — {pub_resp.text}",
                    idempotency_key=idempotency_key,
                )
        except Exception as exc:
            return PublishResult(
                slot_id=slot.slot_id,
                platform=Platform.INSTAGRAM,
                success=False,
                error=str(exc),
                idempotency_key=idempotency_key,
            )

    async def get_post_analytics(self, post_id: str) -> dict | None:
        if not INSTAGRAM_ACCESS_TOKEN:
            logger.warning("No INSTAGRAM_ACCESS_TOKEN — skipping analytics for %s", post_id)
            return None

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{GRAPH_BASE}/{post_id}/insights",
                    params={
                        "metric": "impressions,reach,likes,comments,shares,saved",
                        "access_token": INSTAGRAM_ACCESS_TOKEN,
                    },
                )
            if resp.status_code == 200:
                raw = resp.json().get("data", [])
                metrics: dict = {}
                for item in raw:
                    metrics[item["name"]] = item.get("values", [{}])[0].get("value", 0)
                return {
                    "likes": metrics.get("likes", 0),
                    "shares": metrics.get("shares", 0),
                    "comments": metrics.get("comments", 0),
                    "reach": metrics.get("reach", 0),
                }
            logger.error("Instagram analytics error for %s: %s", post_id, resp.text)
        except Exception as exc:
            logger.error("Instagram analytics exception for %s: %s", post_id, exc)
        return None

    async def get_recent_posts(self, days: int = 7) -> list[dict]:
        logger.info("Instagram get_recent_posts not yet implemented — returning empty list")
        return []
