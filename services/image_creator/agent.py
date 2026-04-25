"""Image Creator sub-agent — receives ApprovedSlates and generates platform images.

This agent sits between the Critic and Publisher in the pipeline. It:
1. Receives an ApprovedSlate with critic-approved ContentSlots
2. Adapts each slot into a platform-optimized image prompt
3. Calls the Imagen API to generate PNG files
4. Returns ImageResults for the Publisher to upload

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

from services.image_creator.imagen_client import ImagenClient
from services.image_creator.prompt_adapter import adapt_prompt
from services.shared.models import (
    AgentEnvelope,
    ApprovedSlate,
    BrandKit,
    ImageResult,
)

logger = logging.getLogger(__name__)

IMAGE_CREATOR_SEED = os.environ.get("IMAGE_CREATOR_SEED", "agentbuffer-image-creator-seed-v1")
IMAGE_CREATOR_PORT = int(os.environ.get("IMAGE_CREATOR_PORT", "8006"))


async def process_approved_slate(
    slate: ApprovedSlate,
    brand: BrandKit,
    imagen_client: ImagenClient | None = None,
) -> list[ImageResult]:
    """Generate images for all approved slots in a slate.

    Args:
        slate: The critic-approved slate containing content slots.
        brand: The brand kit for contextual prompt generation.
        imagen_client: Optional ImagenClient instance (created if not provided).

    Returns:
        A list of ImageResult objects — one per approved slot.
    """
    client = imagen_client or ImagenClient()
    approved_slot_ids = {v.slot_id for v in slate.verdicts if v.approved}

    results: list[ImageResult] = []
    for slot in slate.slate.slots:
        if slot.slot_id not in approved_slot_ids:
            logger.info("Skipping unapproved slot %s", slot.slot_id)
            continue

        try:
            image_request = adapt_prompt(slot, brand)
            result = await client.generate_image(image_request)
            results.append(result)

            if result.status == "success":
                logger.info(
                    "Generated image for slot %s → %s",
                    slot.slot_id,
                    result.local_path,
                )
            else:
                logger.warning(
                    "Image generation issue for slot %s: %s — %s",
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
                ImageResult(
                    slot_id=slot.slot_id,
                    platform=slot.platform,
                    status="error",
                    error=f"Unexpected error: {exc}",
                )
            )

    return results


def wrap_results_as_envelope(results: list[ImageResult]) -> AgentEnvelope:
    """Package image results into an AgentEnvelope for the Publisher."""
    return AgentEnvelope(
        from_agent="image_creator",
        to_agent="publisher",
        envelope_type="image_results",
        payload={"images": [r.dict() for r in results]},
        signature="placeholder",
        timestamp=datetime.now(tz=timezone.utc),
    )


# ── Agentverse agent setup ──

agent = Agent(
    name="AgentBuffer-Image-Creator",
    seed=IMAGE_CREATOR_SEED,
    port=IMAGE_CREATOR_PORT,
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

    if text.startswith("[IMAGE_REQUEST:"):
        prefix_end = text.index("]")
        session_id = text[len("[IMAGE_REQUEST:") : prefix_end]
        payload_text = text[prefix_end + 1 :].strip()

        try:
            payload = json.loads(payload_text)
            approved_slate = ApprovedSlate(**payload["approved_slate"])
            brand = BrandKit(**payload["brand"])

            results = await process_approved_slate(approved_slate, brand)

            result_data = json.dumps(
                [r.dict() for r in results],
                default=str,
            )
            reply_text = f"[IMAGE_REPLY:{session_id}]\n{result_data}"
            await ctx.send(
                sender,
                ChatMessage(
                    timestamp=datetime.now(tz=timezone.utc),
                    msg_id=uuid4(),
                    content=[TextContent(type="text", text=reply_text)],
                ),
            )
        except Exception as exc:
            logger.error("Image Creator processing failed: %s", exc)
            await ctx.send(
                sender,
                ChatMessage(
                    timestamp=datetime.now(tz=timezone.utc),
                    msg_id=uuid4(),
                    content=[
                        TextContent(
                            type="text",
                            text=f"[IMAGE_REPLY:{session_id}]\n" + json.dumps({"error": str(exc)}),
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
                            "I'm the AgentBuffer Image Creator. I generate platform-optimized "
                            "images via Google Imagen when dispatched by the Marketing Director. "
                            "Please chat with the main AgentBuffer agent instead."
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
