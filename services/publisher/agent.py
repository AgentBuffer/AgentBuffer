"""Publisher uAgent — publishes approved content to social platforms.

Receives approved ContentSlots + optional VideoResults from the Head Agent
and schedules posts for publication.

Uses per-platform adapters (services.publisher.adapters) to call each
social network's native API directly — no third-party aggregator required.

Can operate as:
  1. A standalone Agentverse agent (via Chat Protocol)
  2. An inline function called by the Head Agent (publish_slots)
"""

from __future__ import annotations

import asyncio
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

from services.publisher.adapters.base import get_adapter
from services.shared.models import (
    ContentSlot,
    PublishResult,
)

logger = logging.getLogger(__name__)

PUBLISHER_SEED = os.environ.get("PUBLISHER_SEED", "agentbuffer-publisher-seed-v1")
PUBLISHER_PORT = int(os.environ.get("PUBLISHER_PORT", "8005"))
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
STORAGE_BUCKET = os.environ.get("STORAGE_BUCKET", "agent-media")


async def _publish_slot(slot: ContentSlot, idempotency_key: str) -> PublishResult:
    """Publish a single slot via the platform-specific adapter."""
    adapter = get_adapter(slot.platform)
    return await adapter.publish(slot, idempotency_key)


def publish_slots(slots: list[ContentSlot]) -> list[PublishResult]:
    """Publish content slots to their target platforms.

    Delegates to the appropriate platform adapter for each slot.
    Falls back to simulated results when no credentials are configured
    (each adapter handles this internally).
    """
    results = []
    for slot in slots:
        idempotency_key = f"pub-{slot.slot_id}-{uuid4().hex[:6]}"
        result = asyncio.get_event_loop().run_until_complete(_publish_slot(slot, idempotency_key))
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
            user_id = payload.get("user_id", "")
            brand_id = payload.get("brand_id", "")
            results = publish_slots(slots)
            logger.info(
                "Publisher completed for user=%s brand=%s session=%s",
                user_id,
                brand_id,
                session_id,
            )

            serialized = json.dumps(
                [r.dict() for r in results],
                default=str,
            )
            reply_text = f"[PUBLISH_REPLY:{session_id}]\n{serialized}"
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
                        text=(
                            "I'm the AgentBuffer Publisher. I publish approved"
                            " content to social media platforms when dispatched"
                            " by the Marketing Director. Please chat with the"
                            " main AgentBuffer agent instead."
                        ),
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
