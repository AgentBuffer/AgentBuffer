"""Strategist uAgent — generates weekly content slates using an LLM.

Receives a BrandKit + MarketingAnalysis from the Head Agent and returns
a 7-slot Slate with platform-optimized captions and image/video prompts.

Can operate as:
  1. A standalone Agentverse agent (via Chat Protocol)
  2. An inline function called by the Head Agent (generate_slate)
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone
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
    ContentSlot,
    MarketingAnalysis,
    Platform,
    Slate,
)

logger = logging.getLogger(__name__)

ASI_ONE_API_KEY = os.environ.get("ASI_ONE_API_KEY", "")
ASI_ONE_BASE_URL = os.environ.get("ASI_ONE_BASE_URL", "https://api.asi1.ai/v1")
ASI_ONE_MODEL = os.environ.get("ASI_ONE_MODEL", "asi1")
STRATEGIST_SEED = os.environ.get("STRATEGIST_SEED", "agentbuffer-strategist-seed-v1")
STRATEGIST_PORT = int(os.environ.get("STRATEGIST_PORT", "8002"))

# -- Tone-value-to-descriptor mappings ----------------------------------------

_TONE_DESCRIPTORS: dict[str, list[tuple[int, str]]] = {
    "formality": [
        (33, "casual and conversational"),
        (66, "balanced"),
        (100, "professional and formal"),
    ],
    "humor": [
        (33, "earnest and sincere"),
        (66, "lightly playful"),
        (100, "witty and humorous"),
    ],
    "boldness": [
        (33, "understated"),
        (66, "confident"),
        (100, "bold and direct"),
    ],
    "warmth": [
        (33, "informational"),
        (66, "friendly"),
        (100, "warm and personal"),
    ],
}


def _describe_tone(dimension: str, value: int) -> str:
    for threshold, label in _TONE_DESCRIPTORS.get(dimension, []):
        if value <= threshold:
            return label
    return "balanced"


def _build_tone_block(brand: BrandKit) -> str:
    """Build a natural-language tone description from the BrandKit."""
    tone = brand.tone
    lines = [
        f"- Formality: {_describe_tone('formality', tone.formality)} ({tone.formality}/100)",
        f"- Humor: {_describe_tone('humor', tone.humor)} ({tone.humor}/100)",
        f"- Boldness: {_describe_tone('boldness', tone.boldness)} ({tone.boldness}/100)",
        f"- Warmth: {_describe_tone('warmth', tone.warmth)} ({tone.warmth}/100)",
    ]
    if brand.personality_keywords:
        kw = ", ".join(brand.personality_keywords)
        lines.append(f"- Personality keywords to reflect: {kw}")
    return "\n".join(lines)


def _build_reference_block(brand: BrandKit) -> str:
    """Format reference posts as exemplars for the LLM."""
    if not brand.reference_posts:
        return ""
    header = (
        "The following posts represent ideal on-brand content for this brand. "
        "Match their tone, style, and voice."
    )
    posts = []
    for p in brand.reference_posts:
        posts.append(f"  [{p.platform.value.upper()}] {p.text}")
    return f"{header}\n" + "\n".join(posts)


SLATE_SYSTEM_PROMPT = """\
You are a content strategist AI. Given a brand profile and marketing analysis, generate exactly 7 \
content slots for one week of social media content.

Return valid JSON — an array of 7 objects, each with:
{
  "slot_number": 1,
  "caption": "The full post caption in the brand's voice",
  "image_prompt": "A detailed visual description for AI image/video generation",
  "platform": "one of: linkedin, x, instagram, tiktok, youtube"
}

Rules:
- Spread content across the recommended platforms (don't put all on one platform)
- Captions must be in the brand's voice and tone
- Image prompts should be vivid, detailed, and brand-aligned
- Each slot should cover a different content theme from the analysis
- Slot numbers go from 1 to 7 (Monday to Sunday)
- Make at least one slot intentionally weaker/more generic so the Critic has something to reject
- If a tone profile is provided, strictly follow the tone descriptors in every caption
- If reference posts are provided, use them as exemplars for voice and style

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


def generate_slate(brand: BrandKit, analysis: MarketingAnalysis) -> Slate:
    """Generate a 7-day content slate using the LLM."""
    client = _get_client()

    tone_block = _build_tone_block(brand)
    ref_block = _build_reference_block(brand)

    context = (
        f"Brand: {brand.name}\n"
        f"Industry: {brand.industry}\n"
        f"Tagline: {brand.tagline}\n"
        f"Voice: {brand.voice_description}\n"
        f"Target Audience: {brand.target_audience}\n\n"
        f"Tone Profile:\n{tone_block}\n\n"
        + (f"Reference Posts:\n{ref_block}\n\n" if ref_block else "")
        + f"Marketing Analysis:\n"
        f"Positioning: {analysis.competitive_positioning}\n"
        f"Key Differentiators: {', '.join(analysis.key_differentiators)}\n"
        f"Audience Insights: {analysis.target_audience_insights}\n"
        f"Recommended Platforms: {', '.join(p.value for p in analysis.recommended_platforms)}\n"
        f"Content Themes: {', '.join(analysis.content_themes)}\n"
        f"Tone: {analysis.tone_guidelines}\n"
        f"Cadence: {analysis.weekly_cadence}\n"
    )

    resp = client.chat.completions.create(
        model=ASI_ONE_MODEL,
        messages=[
            {"role": "system", "content": SLATE_SYSTEM_PROMPT},
            {"role": "user", "content": context},
        ],
        max_tokens=4096,
    )

    raw = resp.choices[0].message.content or "[]"
    slots_data = json.loads(_clean_json_response(raw))

    now = datetime.now(tz=timezone.utc)
    next_monday = now + timedelta(days=(7 - now.weekday()) % 7 or 7)

    slots = []
    for i, slot_data in enumerate(slots_data[:7]):
        platform_str = slot_data.get("platform", "instagram")
        try:
            platform = Platform(platform_str)
        except ValueError:
            platform = Platform.INSTAGRAM

        scheduled = next_monday + timedelta(days=i, hours=9)

        slots.append(
            ContentSlot(
                slot_id=f"slot-{uuid4().hex[:8]}",
                slot_number=slot_data.get("slot_number", i + 1),
                caption=slot_data.get("caption", ""),
                image_prompt=slot_data.get("image_prompt", ""),
                platform=platform,
                scheduled_for=scheduled,
                status="proposed",
            )
        )

    slate_id = f"slate-{uuid4().hex[:8]}"
    return Slate(
        slate_id=slate_id,
        brand_id=brand.brand_id,
        org_id=brand.org_id,
        slots=slots,
        generation_context=f"Generated by Strategist for {brand.name}",
    )


# ── Agentverse agent setup ──

agent = Agent(
    name="AgentBuffer-Strategist",
    seed=STRATEGIST_SEED,
    port=STRATEGIST_PORT,
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

    # Check if this is a request from the Head Agent
    if text.startswith("[STRATEGIST_REQUEST:"):
        prefix_end = text.index("]")
        session_id = text[len("[STRATEGIST_REQUEST:") : prefix_end]
        payload_text = text[prefix_end + 1 :].strip()

        try:
            payload = json.loads(payload_text)
            brand = BrandKit(**payload["brand"])
            analysis = MarketingAnalysis(**payload["analysis"])
            slate = generate_slate(brand, analysis)

            reply_text = f"[STRATEGIST_REPLY:{session_id}]\n{slate.json()}"
            await ctx.send(
                sender,
                ChatMessage(
                    timestamp=datetime.now(tz=timezone.utc),
                    msg_id=uuid4(),
                    content=[TextContent(type="text", text=reply_text)],
                ),
            )
        except Exception as exc:
            logger.error("Strategist processing failed: %s", exc)
            await ctx.send(
                sender,
                ChatMessage(
                    timestamp=datetime.now(tz=timezone.utc),
                    msg_id=uuid4(),
                    content=[
                        TextContent(
                            type="text",
                            text=f"[STRATEGIST_REPLY:{session_id}]\n"
                            + json.dumps({"error": str(exc)}),
                        ),
                        EndSessionContent(type="end-session"),
                    ],
                ),
            )
    else:
        # Direct user interaction — generate slate from free-form text
        await ctx.send(
            sender,
            ChatMessage(
                timestamp=datetime.now(tz=timezone.utc),
                msg_id=uuid4(),
                content=[
                    TextContent(
                        type="text",
                        text=(
                            "I'm the AgentBuffer Strategist. I generate content plans "
                            "when dispatched by the Marketing Director. "
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
