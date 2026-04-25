"""LinkedIn adapter — publishes via the LinkedIn Posts API."""

from __future__ import annotations

import logging
import os

import httpx

from services.shared.models import ContentSlot, Platform, PublishResult

from .base import PlatformAdapter

logger = logging.getLogger(__name__)

LINKEDIN_ACCESS_TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_PERSON_URN = os.environ.get("LINKEDIN_PERSON_URN", "")

API_BASE = "https://api.linkedin.com/rest"
API_VERSION = "202504"


class LinkedInAdapter(PlatformAdapter):
    """Publish and read analytics via the LinkedIn Marketing API."""

    async def publish(self, slot: ContentSlot, idempotency_key: str) -> PublishResult:
        if not LINKEDIN_ACCESS_TOKEN or not LINKEDIN_PERSON_URN:
            logger.warning("No LinkedIn credentials — simulating publish for slot %s", slot.slot_id)
            return PublishResult(
                slot_id=slot.slot_id,
                platform=Platform.LINKEDIN,
                success=True,
                permalink=f"https://linkedin.com/simulated/{slot.slot_id}",
                idempotency_key=idempotency_key,
            )

        try:
            payload = {
                "author": LINKEDIN_PERSON_URN,
                "commentary": slot.caption,
                "visibility": "PUBLIC",
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": [],
                },
                "lifecycleState": "PUBLISHED",
                "isReshareDisabledByAuthor": False,
            }

            headers = {
                "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
                "Content-Type": "application/json",
                "LinkedIn-Version": API_VERSION,
                "X-Restli-Protocol-Version": "2.0.0",
            }

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{API_BASE}/posts",
                    headers=headers,
                    json=payload,
                )

            if resp.status_code in (200, 201):
                post_urn = resp.headers.get("x-restli-id", "")
                return PublishResult(
                    slot_id=slot.slot_id,
                    platform=Platform.LINKEDIN,
                    success=True,
                    permalink=f"https://www.linkedin.com/feed/update/{post_urn}/",
                    idempotency_key=idempotency_key,
                )
            return PublishResult(
                slot_id=slot.slot_id,
                platform=Platform.LINKEDIN,
                success=False,
                error=f"LinkedIn API error: {resp.status_code} — {resp.text}",
                idempotency_key=idempotency_key,
            )
        except Exception as exc:
            return PublishResult(
                slot_id=slot.slot_id,
                platform=Platform.LINKEDIN,
                success=False,
                error=str(exc),
                idempotency_key=idempotency_key,
            )

    async def get_post_analytics(self, post_id: str) -> dict | None:
        if not LINKEDIN_ACCESS_TOKEN:
            logger.warning("No LINKEDIN_ACCESS_TOKEN — skipping analytics for %s", post_id)
            return None

        try:
            headers = {
                "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
                "LinkedIn-Version": API_VERSION,
                "X-Restli-Protocol-Version": "2.0.0",
            }
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{API_BASE}/organizationalEntityShareStatistics",
                    headers=headers,
                    params={"q": "organizationalEntity", "shares": f"List({post_id})"},
                )
            if resp.status_code == 200:
                elements = resp.json().get("elements", [])
                if elements:
                    stats = elements[0].get("totalShareStatistics", {})
                    return {
                        "likes": stats.get("likeCount", 0),
                        "shares": stats.get("shareCount", 0),
                        "comments": stats.get("commentCount", 0),
                        "reach": stats.get("impressionCount", 0),
                    }
            logger.error("LinkedIn analytics error for %s: %s", post_id, resp.text)
        except Exception as exc:
            logger.error("LinkedIn analytics exception for %s: %s", post_id, exc)
        return None

    async def get_recent_posts(self, days: int = 7) -> list[dict]:
        logger.info("LinkedIn get_recent_posts not yet implemented — returning empty list")
        return []
