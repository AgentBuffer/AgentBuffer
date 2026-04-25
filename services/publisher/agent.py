"""Publisher uAgent — publishes approved content to social platforms via Ayrshare.

Receives approved ContentSlots + optional VideoResults from the Head Agent
and schedules posts for publication.

Can operate as:
  1. A standalone Agentverse agent (via Chat Protocol)
  2. An inline function called by the Head Agent (publish_slots)
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from uuid import uuid4

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

from services.shared.models import (
    ContentSlot,
    Platform,
    PublishResult,
)

logger = logging.getLogger(__name__)

PUBLISHER_SEED = os.environ.get("PUBLISHER_SEED", "agentbuffer-publisher-seed-v1")
PUBLISHER_PORT = int(os.environ.get("PUBLISHER_PORT", "8005"))
AYRSHARE_API_KEY = os.environ.get("AYRSHARE_API_KEY", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
STORAGE_BUCKET = os.environ.get("STORAGE_BUCKET", "agent-media")


def publish_slots(slots: list[ContentSlot]) -> list[PublishResult]:
    """Publish content slots to their target platforms.

    Currently returns simulated results. Replace with Ayrshare API calls
    when the API key is configured.
    """
    results = []
    for slot in slots:
        idempotency_key = f"pub-{slot.slot_id}-{uuid4().hex[:6]}"

        if AYRSHARE_API_KEY:
            result = _publish_via_ayrshare(slot, idempotency_key)
        else:
            result = PublishResult(
                slot_id=slot.slot_id,
                platform=slot.platform,
                success=True,
                permalink=f"https://{slot.platform.value}.com/simulated/{slot.slot_id}",
                error=None,
                idempotency_key=idempotency_key,
            )
            logger.info(
                "Simulated publish for slot %s to %s (no AYRSHARE_API_KEY)",
                slot.slot_id,
                slot.platform.value,
            )

        results.append(result)

    return results


def _upload_to_storage(local_path: str) -> str:
    """Upload a local file to Supabase Storage and return a public URL.

    Falls back to the local path if Supabase credentials are not configured
    or the upload fails.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.info("Supabase Storage not configured, using local path: %s", local_path)
        return local_path

    try:
        from pathlib import Path

        import requests as _requests

        file_path = Path(local_path)
        if not file_path.exists():
            logger.warning("Local file not found for upload: %s", local_path)
            return local_path

        storage_path = f"images/{file_path.name}"
        upload_url = f"{SUPABASE_URL}/storage/v1/object/{STORAGE_BUCKET}/{storage_path}"

        with open(file_path, "rb") as f:
            resp = _requests.post(
                upload_url,
                headers={
                    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                    "Content-Type": "image/png",
                },
                data=f.read(),
                timeout=30,
            )

        if resp.status_code in (200, 201):
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/{STORAGE_BUCKET}/{storage_path}"
            logger.info("Uploaded %s → %s", local_path, public_url)
            return public_url
        else:
            logger.warning(
                "Supabase upload failed (%d): %s — using local path",
                resp.status_code,
                resp.text,
            )
            return local_path
    except Exception as exc:
        logger.warning("Failed to upload to Supabase Storage: %s — using local path", exc)
        return local_path


def _publish_via_ayrshare(slot: ContentSlot, idempotency_key: str) -> PublishResult:
    """Publish a single slot via the Ayrshare API."""
    try:
        import requests

        platform_map = {
            Platform.LINKEDIN: "linkedin",
            Platform.X: "twitter",
            Platform.INSTAGRAM: "instagram",
            Platform.TIKTOK: "tiktok",
            Platform.YOUTUBE: "youtube",
        }

        payload = {
            "post": slot.caption,
            "platforms": [platform_map.get(slot.platform, "instagram")],
            "scheduledDate": slot.scheduled_for.isoformat(),
        }

        if slot.image_url:
            media_url = slot.image_url
            if not media_url.startswith("http"):
                media_url = _upload_to_storage(media_url)
            if media_url.startswith("http"):
                payload["mediaUrls"] = [media_url]

        resp = requests.post(
            "https://app.ayrshare.com/api/post",
            headers={
                "Authorization": f"Bearer {AYRSHARE_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )

        if resp.status_code == 200:
            data = resp.json()
            return PublishResult(
                slot_id=slot.slot_id,
                platform=slot.platform,
                success=True,
                permalink=data.get("postUrl", ""),
                error=None,
                idempotency_key=idempotency_key,
            )
        else:
            return PublishResult(
                slot_id=slot.slot_id,
                platform=slot.platform,
                success=False,
                error=f"Ayrshare API error: {resp.status_code} — {resp.text}",
                idempotency_key=idempotency_key,
            )
    except Exception as exc:
        return PublishResult(
            slot_id=slot.slot_id,
            platform=slot.platform,
            success=False,
            error=str(exc),
            idempotency_key=idempotency_key,
        )


# ── Agentverse agent setup ──

agent = Agent(
    name="AgentBuffer-Publisher",
    seed=PUBLISHER_SEED,
    port=PUBLISHER_PORT,
    mailbox=True,
    publish_agent_details=True,
)

protocol = Protocol(spec=chat_protocol_spec)


@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=datetime.now(tz=timezone.utc),
            acknowledged_msg_id=msg.msg_id,
        ),
    )

    text = ""
    for item in msg.content:
        if isinstance(item, TextContent):
            text += item.text

    if text.startswith("[PUBLISH_REQUEST:"):
        prefix_end = text.index("]")
        session_id = text[len("[PUBLISH_REQUEST:") : prefix_end]
        payload_text = text[prefix_end + 1 :].strip()

        try:
            payload = json.loads(payload_text)
            slots = [ContentSlot(**s) for s in payload["slots"]]
            results = publish_slots(slots)

            reply_text = f"[PUBLISH_REPLY:{session_id}]\n{json.dumps([r.dict() for r in results], default=str)}"
            await ctx.send(
                sender,
                ChatMessage(
                    timestamp=datetime.now(tz=timezone.utc),
                    msg_id=uuid4(),
                    content=[TextContent(type="text", text=reply_text)],
                ),
            )
        except Exception as exc:
            logger.error("Publisher processing failed: %s", exc)
            await ctx.send(
                sender,
                ChatMessage(
                    timestamp=datetime.now(tz=timezone.utc),
                    msg_id=uuid4(),
                    content=[
                        TextContent(
                            type="text",
                            text=f"[PUBLISH_REPLY:{session_id}]\n"
                            + json.dumps({"error": str(exc)}),
                        ),
                        EndSessionContent(type="end-session"),
                    ],
                ),
            )
    else:
        await ctx.send(
            sender,
            ChatMessage(
                timestamp=datetime.now(tz=timezone.utc),
                msg_id=uuid4(),
                content=[
                    TextContent(
                        type="text",
                        text="I'm the AgentBuffer Publisher. I publish approved content to social media platforms when dispatched by the Marketing Director. Please chat with the main AgentBuffer agent instead.",
                    ),
                    EndSessionContent(type="end-session"),
                ],
            ),
        )


@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
