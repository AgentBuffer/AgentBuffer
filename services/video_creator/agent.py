"""Video Creator sub-agent — receives ApprovedSlates and generates platform videos.

This agent sits between the Critic and Publisher in the pipeline. It:
1. Receives an ApprovedSlate with critic-approved ContentSlots
2. Fetches current trends for each slot's target platform
3. Adapts each slot into a platform-optimized video prompt
4. Calls the Veo API to generate .mp4 files
5. Returns VideoResults for the Publisher to upload

Also registered on Agentverse with Chat Protocol for ASI:One discoverability.
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
    AgentEnvelope,
    ApprovedSlate,
    BrandKit,
    VideoResult,
)
from services.video_creator.trends import adapt_prompt_for_platform, get_trends
from services.video_creator.veo_client import VeoClient

logger = logging.getLogger(__name__)

VIDEO_CREATOR_SEED = os.environ.get("VIDEO_CREATOR_SEED", "agentbuffer-video-creator-seed-v1")
VIDEO_CREATOR_PORT = int(os.environ.get("VIDEO_CREATOR_PORT", "8004"))


async def process_approved_slate(
    slate: ApprovedSlate,
    brand: BrandKit,
    veo_client: VeoClient | None = None,
) -> list[VideoResult]:
    """Generate videos for all approved slots in a slate.

    Args:
        slate: The critic-approved slate containing content slots.
        brand: The brand kit for contextual prompt generation.
        veo_client: Optional VeoClient instance (created if not provided).

    Returns:
        A list of VideoResult objects — one per approved slot.
    """
    client = veo_client or VeoClient()
    approved_slot_ids = {v.slot_id for v in slate.verdicts if v.approved}

    results: list[VideoResult] = []
    for slot in slate.slate.slots:
        if slot.slot_id not in approved_slot_ids:
            logger.info("Skipping unapproved slot %s", slot.slot_id)
            continue

        try:
            trends = get_trends(slot.platform)
            video_request = adapt_prompt_for_platform(slot, brand, trends)
            result = await client.generate_video(video_request)
            results.append(result)

            if result.status == "success":
                logger.info(
                    "Generated video for slot %s → %s",
                    slot.slot_id,
                    result.local_path,
                )
            else:
                logger.warning(
                    "Video generation issue for slot %s: %s — %s",
                    slot.slot_id,
                    result.status,
                    result.error,
                )
        except Exception as exc:
            logger.error(
                "Unexpected error processing slot %s: %s",
                slot.slot_id,
                exc,
            )
            results.append(
                VideoResult(
                    slot_id=slot.slot_id,
                    platform=slot.platform,
                    status="error",
                    error=f"Unexpected error: {exc}",
                )
            )

    return results


def wrap_results_as_envelope(results: list[VideoResult]) -> AgentEnvelope:
    """Package video results into an AgentEnvelope for the Publisher."""
    return AgentEnvelope(
        from_agent="video_creator",
        to_agent="publisher",
        envelope_type="video_results",
        payload={"videos": [r.model_dump() for r in results]},
        signature="placeholder",
        timestamp=datetime.now(tz=timezone.utc),
    )


# ── Agentverse agent setup ──

agent = Agent(
    name="AgentBuffer-Video-Creator",
    seed=VIDEO_CREATOR_SEED,
    port=VIDEO_CREATOR_PORT,
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

    if text.startswith("[VIDEO_REQUEST:"):
        prefix_end = text.index("]")
        session_id = text[len("[VIDEO_REQUEST:") : prefix_end]
        payload_text = text[prefix_end + 1 :].strip()

        try:
            payload = json.loads(payload_text)
            approved_slate = ApprovedSlate(**payload["approved_slate"])
            brand = BrandKit(**payload["brand"])
            user_id = payload.get("user_id", "")
            brand_id = payload.get("brand_id", "")

            results = await process_approved_slate(approved_slate, brand)

            serialized = json.dumps(
                [r.model_dump() for r in results],
                default=str,
            )
            reply_text = f"[VIDEO_REPLY:{session_id}]\n{serialized}"
            logger.info(
                "Video Creator completed for user=%s brand=%s session=%s",
                user_id,
                brand_id,
                session_id,
            )
            await ctx.send(
                sender,
                ChatMessage(
                    timestamp=datetime.now(tz=timezone.utc),
                    msg_id=uuid4(),
                    content=[TextContent(type="text", text=reply_text)],
                ),
            )
        except Exception as exc:
            logger.error("Video Creator processing failed: %s", exc)
            await ctx.send(
                sender,
                ChatMessage(
                    timestamp=datetime.now(tz=timezone.utc),
                    msg_id=uuid4(),
                    content=[
                        TextContent(
                            type="text",
                            text=f"[VIDEO_REPLY:{session_id}]\n" + json.dumps({"error": str(exc)}),
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
                            "I'm the AgentBuffer Video Creator. I generate"
                            " platform-optimized videos via Google Veo when"
                            " dispatched by the Marketing Director. Please chat"
                            " with the main AgentBuffer agent instead."
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
