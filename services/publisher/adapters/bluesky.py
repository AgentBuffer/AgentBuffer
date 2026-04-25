"""Bluesky adapter — publishes via the AT Protocol."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import httpx

from services.shared.models import ContentSlot, Platform, PublishResult

from .base import PlatformAdapter

logger = logging.getLogger(__name__)

BLUESKY_HANDLE = os.environ.get("BLUESKY_HANDLE", "")
BLUESKY_APP_PASSWORD = os.environ.get("BLUESKY_APP_PASSWORD", "")

API_BASE = "https://bsky.social/xrpc"


class BlueskyAdapter(PlatformAdapter):
    """Publish and read analytics via the Bluesky AT Protocol.

    Bluesky uses simple app-password auth — no OAuth required.
    """

    async def _create_session(self, client: httpx.AsyncClient) -> str | None:
        """Authenticate and return an access JWT, or *None* on failure."""
        resp = await client.post(
            f"{API_BASE}/com.atproto.server.createSession",
            json={"identifier": BLUESKY_HANDLE, "password": BLUESKY_APP_PASSWORD},
        )
        if resp.status_code == 200:
            return resp.json().get("accessJwt")
        logger.error("Bluesky auth failed: %s — %s", resp.status_code, resp.text)
        return None

    async def publish(self, slot: ContentSlot, idempotency_key: str) -> PublishResult:
        if not BLUESKY_HANDLE or not BLUESKY_APP_PASSWORD:
            logger.warning("No Bluesky credentials — simulating publish for slot %s", slot.slot_id)
            return PublishResult(
                slot_id=slot.slot_id,
                platform=Platform.X,
                success=True,
                permalink=f"https://bsky.app/simulated/{slot.slot_id}",
                idempotency_key=idempotency_key,
            )

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                token = await self._create_session(client)
                if not token:
                    return PublishResult(
                        slot_id=slot.slot_id,
                        platform=Platform.X,
                        success=False,
                        error="Bluesky authentication failed",
                        idempotency_key=idempotency_key,
                    )

                record = {
                    "$type": "app.bsky.feed.post",
                    "text": slot.caption[:300],
                    "createdAt": datetime.now(tz=timezone.utc).isoformat(),
                }

                resp = await client.post(
                    f"{API_BASE}/com.atproto.repo.createRecord",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "repo": BLUESKY_HANDLE,
                        "collection": "app.bsky.feed.post",
                        "record": record,
                    },
                )

            if resp.status_code == 200:
                uri = resp.json().get("uri", "")
                parts = uri.split("/")
                rkey = parts[-1] if parts else ""
                did = parts[2] if len(parts) > 2 else BLUESKY_HANDLE
                return PublishResult(
                    slot_id=slot.slot_id,
                    platform=Platform.X,
                    success=True,
                    permalink=f"https://bsky.app/profile/{did}/post/{rkey}",
                    idempotency_key=idempotency_key,
                )
            return PublishResult(
                slot_id=slot.slot_id,
                platform=Platform.X,
                success=False,
                error=f"Bluesky API error: {resp.status_code} — {resp.text}",
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
        logger.info("Bluesky analytics not yet implemented for post %s", post_id)
        return None

    async def get_recent_posts(self, days: int = 7) -> list[dict]:
        logger.info("Bluesky get_recent_posts not yet implemented — returning empty list")
        return []
