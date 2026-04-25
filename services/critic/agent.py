"""Critic uAgent — scores content slates on a 5-axis rubric, rejects weak work.

Receives a Slate + BrandKit from the Head Agent and returns CriticVerdicts.
Must reject at least 1 slot per slate to demonstrate quality standards.

Can operate as:
  1. A standalone Agentverse agent (via Chat Protocol)
  2. An inline function called by the Head Agent (critique_slate)
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from uuid import uuid4

from openai import OpenAI
from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

from services.shared.models import (
    BrandKit,
    CriticScore,
    CriticVerdict,
    Slate,
)

logger = logging.getLogger(__name__)

ASI_ONE_API_KEY = os.environ.get("ASI_ONE_API_KEY", "")
ASI_ONE_BASE_URL = os.environ.get("ASI_ONE_BASE_URL", "https://api.asi1.ai/v1")
ASI_ONE_MODEL = os.environ.get("ASI_ONE_MODEL", "asi1")
CRITIC_SEED = os.environ.get("CRITIC_SEED", "agentbuffer-critic-seed-v1")
CRITIC_PORT = int(os.environ.get("CRITIC_PORT", "8003"))

CRITIC_SYSTEM_PROMPT = """\
You are a ruthless content quality critic for a marketing agency. You evaluate social media \
content on 5 axes, each scored 0.0 to 5.0.

Given a brand profile and a list of content slots, score EACH slot on:
1. Brand Voice Alignment — does the caption match the brand's tone/voice?
2. Visual Coherence — does the image prompt align with the brand aesthetic?
3. Platform Fit — is the content native to the target platform?
4. Audience Relevance — will this resonate with the target audience?
5. Originality — is this fresh and unique, or generic/could-be-any-brand?

IMPORTANT: You MUST reject at least 1 slot (average score < 3.5). A perfect slate is suspicious. \
Find the weakest piece and be honest about why it falls short.

Return valid JSON — an array of objects, one per slot:
[
  {
    "slot_id": "string",
    "scores": [
      {"axis": "Brand Voice Alignment", "score": 4.2, "reasoning": "short explanation"},
      {"axis": "Visual Coherence", "score": 3.8, "reasoning": "short explanation"},
      {"axis": "Platform Fit", "score": 4.0, "reasoning": "short explanation"},
      {"axis": "Audience Relevance", "score": 3.9, "reasoning": "short explanation"},
      {"axis": "Originality", "score": 3.5, "reasoning": "short explanation"}
    ],
    "average": 3.88,
    "approved": true,
    "summary": "One-sentence summary of the verdict"
  }
]

A slot is approved if average >= 3.5, rejected if < 3.5.
Respond ONLY with the JSON array, no markdown fences or extra text.\
"""


def _get_client() -> OpenAI:
    return OpenAI(base_url=ASI_ONE_BASE_URL, api_key=ASI_ONE_API_KEY)


def _clean_json_response(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        text = "\n".join(lines)
    return text.strip()


def critique_slate(slate: Slate, brand: BrandKit) -> list[CriticVerdict]:
    """Score each slot in the slate and return verdicts."""
    client = _get_client()

    slots_description = []
    for s in slate.slots:
        slots_description.append(
            {
                "slot_id": s.slot_id,
                "slot_number": s.slot_number,
                "platform": s.platform.value,
                "caption": s.caption,
                "image_prompt": s.image_prompt,
            }
        )

    context = (
        f"Brand: {brand.name}\n"
        f"Industry: {brand.industry}\n"
        f"Voice: {brand.voice_description}\n"
        f"Target Audience: {brand.target_audience}\n"
        f"Tagline: {brand.tagline}\n\n"
        f"Content Slots to Review:\n{json.dumps(slots_description, indent=2)}"
    )

    resp = client.chat.completions.create(
        model=ASI_ONE_MODEL,
        messages=[
            {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
            {"role": "user", "content": context},
        ],
        max_tokens=4096,
    )

    raw = resp.choices[0].message.content or "[]"
    verdicts_data = json.loads(_clean_json_response(raw))

    verdicts = []
    for v_data in verdicts_data:
        scores = [CriticScore(**s) for s in v_data.get("scores", [])]
        avg = v_data.get("average", 0.0)
        if scores and not avg:
            avg = sum(s.score for s in scores) / len(scores)
        verdicts.append(
            CriticVerdict(
                slot_id=v_data["slot_id"],
                scores=scores,
                average=round(avg, 2),
                approved=v_data.get("approved", avg >= 3.5),
                summary=v_data.get("summary", ""),
            )
        )

    # Ensure at least one rejection
    if all(v.approved for v in verdicts) and verdicts:
        weakest = min(verdicts, key=lambda v: v.average)
        weakest.approved = False
        weakest.summary = (
            f"REJECTED — {weakest.summary} (Weakest in the slate, enforcing quality bar.)"
        )

    return verdicts


# ── Agentverse agent setup ──

agent = Agent(
    name="AgentBuffer-Critic",
    seed=CRITIC_SEED,
    port=CRITIC_PORT,
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

    if text.startswith("[CRITIC_REQUEST:"):
        prefix_end = text.index("]")
        session_id = text[len("[CRITIC_REQUEST:") : prefix_end]
        payload_text = text[prefix_end + 1 :].strip()

        try:
            payload = json.loads(payload_text)
            slate = Slate(**payload["slate"])
            brand = BrandKit(**payload["brand"])
            user_id = payload.get("user_id", "")
            brand_id = payload.get("brand_id", "")
            verdicts = critique_slate(slate, brand)

            reply_text = f"[CRITIC_REPLY:{session_id}]\n{json.dumps([v.dict() for v in verdicts])}"
            await ctx.send(
                sender,
                ChatMessage(
                    timestamp=datetime.now(tz=timezone.utc),
                    msg_id=uuid4(),
                    content=[TextContent(type="text", text=reply_text)],
                ),
            )
            logger.info(
                "Critic completed for user=%s brand=%s session=%s",
                user_id,
                brand_id,
                session_id,
            )
        except Exception as exc:
            logger.error("Critic processing failed: %s", exc)
            await ctx.send(
                sender,
                ChatMessage(
                    timestamp=datetime.now(tz=timezone.utc),
                    msg_id=uuid4(),
                    content=[
                        TextContent(
                            type="text",
                            text=f"[CRITIC_REPLY:{session_id}]\n" + json.dumps({"error": str(exc)}),
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
                        text="I'm the AgentBuffer Critic. I review content quality when dispatched by the Marketing Director. Please chat with the main AgentBuffer agent instead.",
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
