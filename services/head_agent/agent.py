"""Head Agent — the orchestrator that users interact with via ASI:One.

Implements a state machine using ctx.storage for async sub-agent handoffs.
Sends intermediate ChatMessage updates so the user sees progress in real-time.

Pipeline stages:
  1. INTAKE       — parse business description, extract BrandKit
  2. ANALYSIS     — generate marketing analysis via LLM
  3. STRATEGIZE   — dispatch to Strategist, await Slate
  4. CRITIQUE     — dispatch to Critic, await verdicts
  5. VIDEO        — dispatch to Video Creator (if video slots exist)
  6. PUBLISH      — dispatch to Publisher
  7. REPORT       — compile final report, send to user
"""

from __future__ import annotations

import json
import logging
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

from services.head_agent.analysis import (
    extract_brand_kit,
    generate_marketing_analysis,
)
from services.head_agent.config import (
    CRITIC_ADDRESS,
    HEAD_AGENT_PORT,
    HEAD_AGENT_SEED,
    STRATEGIST_ADDRESS,
)
from services.performance_harvester.summary import build_performance_summary

logger = logging.getLogger(__name__)

agent = Agent(
    name="AgentBuffer-Marketing-Director",
    seed=HEAD_AGENT_SEED,
    port=HEAD_AGENT_PORT,
    mailbox=True,
    publish_agent_details=True,
)

protocol = Protocol(spec=chat_protocol_spec)

# ── State keys in ctx.storage ──
# session:{session_id}:stage    — current pipeline stage
# session:{session_id}:sender   — original user address
# session:{session_id}:brand    — serialized BrandKit
# session:{session_id}:analysis — serialized MarketingAnalysis
# session:{session_id}:slate    — serialized Slate from Strategist
# session:{session_id}:verdicts — serialized CriticVerdicts
# session:{session_id}:perf_context_used — "true" or "false"
# sender_session:{sender}       — maps sender address to session_id


async def _send_status(ctx: Context, recipient: str, text: str) -> None:
    """Send an intermediate status update to the user (no EndSession)."""
    await ctx.send(
        recipient,
        ChatMessage(
            timestamp=datetime.now(tz=timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=text)],
        ),
    )


async def _send_final(ctx: Context, recipient: str, text: str) -> None:
    """Send the final report and close the session."""
    await ctx.send(
        recipient,
        ChatMessage(
            timestamp=datetime.now(tz=timezone.utc),
            msg_id=uuid4(),
            content=[
                TextContent(type="text", text=text),
                EndSessionContent(type="end-session"),
            ],
        ),
    )


def _store(ctx: Context, session_id: str, key: str, value: str) -> None:
    ctx.storage.set(f"session:{session_id}:{key}", value)


def _load(ctx: Context, session_id: str, key: str) -> str | None:
    return ctx.storage.get(f"session:{session_id}:{key}")


def _cleanup_session(ctx: Context, session_id: str) -> None:
    """Remove all session keys from storage."""
    for key in (
        "stage", "sender", "brand", "analysis", "slate",
        "verdicts", "user_text", "perf_context_used",
    ):
        ctx.storage.remove(f"session:{session_id}:{key}")


# ── Incoming chat from user (via ASI:One) ──


@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    """Entry point: user sends a business description, or a sub-agent replies."""
    # Acknowledge receipt immediately
    await ctx.send(
        sender,
        ChatAcknowledgement(
            timestamp=datetime.now(tz=timezone.utc),
            acknowledged_msg_id=msg.msg_id,
        ),
    )

    # Extract text
    text = ""
    for item in msg.content:
        if isinstance(item, TextContent):
            text += item.text

    if not text.strip():
        await _send_final(ctx, sender, "Please describe your business and product so I can create a marketing plan.")
        return

    # Check if this is a sub-agent reply (Strategist or Critic)
    # Sub-agents prefix their replies with [STRATEGIST_REPLY:session_id] or [CRITIC_REPLY:session_id]
    if text.startswith("[STRATEGIST_REPLY:"):
        await _handle_strategist_reply(ctx, sender, text)
        return
    if text.startswith("[CRITIC_REPLY:"):
        await _handle_critic_reply(ctx, sender, text)
        return

    # Otherwise, this is a new user request
    session_id = str(uuid4())
    _store(ctx, session_id, "sender", sender)
    _store(ctx, session_id, "user_text", text)
    ctx.storage.set(f"sender_session:{sender}", session_id)

    # Stage 1: Brand extraction
    await _send_status(ctx, sender, "Analyzing your business... extracting brand identity and positioning.")

    try:
        brand = extract_brand_kit(text)
    except Exception as exc:
        logger.error("Brand extraction failed: %s", exc)
        await _send_final(ctx, sender, f"I had trouble understanding your business description. Could you provide more detail about your brand name, industry, target audience, and brand voice?\n\nError: {exc}")
        return

    _store(ctx, session_id, "brand", brand.json())
    _store(ctx, session_id, "stage", "analysis")

    # Stage 2: Marketing analysis
    await _send_status(
        ctx,
        sender,
        f"Brand identified: **{brand.name}** in {brand.industry}.\n"
        f"Target audience: {brand.target_audience}\n\n"
        "Now generating your marketing analysis — competitive positioning, content themes, platform strategy...",
    )

    try:
        analysis = generate_marketing_analysis(brand, text)
    except Exception as exc:
        logger.error("Marketing analysis failed: %s", exc)
        await _send_final(ctx, sender, f"Marketing analysis generation encountered an error: {exc}")
        return

    _store(ctx, session_id, "analysis", analysis.json())
    _store(ctx, session_id, "stage", "strategize")

    # Send analysis summary to user
    analysis_summary = (
        f"MARKETING ANALYSIS — {analysis.brand_name}\n"
        f"{'=' * 40}\n"
        f"Positioning: {analysis.competitive_positioning}\n\n"
        f"Key Differentiators:\n"
        + "\n".join(f"  - {d}" for d in analysis.key_differentiators)
        + f"\n\nTarget Audience: {analysis.target_audience_insights}\n"
        f"Recommended Platforms: {', '.join(p.value for p in analysis.recommended_platforms)}\n"
        f"Content Themes: {', '.join(analysis.content_themes)}\n"
        f"Tone: {analysis.tone_guidelines}\n"
        f"Cadence: {analysis.weekly_cadence}\n\n"
        "Dispatching to Strategist agent to generate your weekly content plan..."
    )
    await _send_status(ctx, sender, analysis_summary)

    # Stage 3: Fetch performance context (if available) and dispatch to Strategist
    perf_summary = build_performance_summary(ctx, brand.brand_id)
    perf_context_used = perf_summary is not None
    _store(ctx, session_id, "perf_context_used", str(perf_context_used).lower())

    perf_payload: dict | None = None
    if perf_summary:
        perf_payload = perf_summary.model_dump()
        await _send_status(
            ctx,
            sender,
            "Found historical performance data — the Strategist will use it to "
            "optimise content types and scheduling.",
        )

    strategist_payload = json.dumps({
        "session_id": session_id,
        "brand": json.loads(brand.json()),
        "analysis": json.loads(analysis.json()),
        "performance_context": perf_payload,
    })

    if not STRATEGIST_ADDRESS:
        # If no strategist address, run strategist inline (for local testing)
        await _run_strategist_inline(ctx, session_id, sender, brand, analysis, perf_summary)
        return

    await ctx.send(
        STRATEGIST_ADDRESS,
        ChatMessage(
            timestamp=datetime.now(tz=timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=f"[STRATEGIST_REQUEST:{session_id}]\n{strategist_payload}")],
        ),
    )


async def _run_strategist_inline(ctx, session_id, sender, brand, analysis, perf_summary=None):
    """Run the strategist logic inline when no external strategist agent is configured."""
    from services.strategist.agent import generate_slate

    await _send_status(ctx, sender, "Strategist is crafting your 7-day content slate...")

    try:
        slate = generate_slate(brand, analysis, performance_context=perf_summary)
    except Exception as exc:
        logger.error("Inline strategist failed: %s", exc)
        await _send_final(ctx, sender, f"Content slate generation failed: {exc}")
        return

    _store(ctx, session_id, "slate", slate.json())
    _store(ctx, session_id, "stage", "critique")

    slot_summary = "\n".join(
        f"  {s.slot_number}. [{s.platform.value.upper()}] {s.caption[:80]}..."
        for s in slate.slots
    )
    await _send_status(
        ctx,
        sender,
        f"WEEKLY CONTENT PLAN — {len(slate.slots)} slots generated\n"
        f"{'=' * 40}\n{slot_summary}\n\n"
        "Sending to Critic agent for quality review...",
    )

    # Dispatch to critic
    if not CRITIC_ADDRESS:
        await _run_critic_inline(ctx, session_id, sender, slate)
        return

    critic_payload = json.dumps({
        "session_id": session_id,
        "slate": json.loads(slate.json()),
        "brand": json.loads(brand.json()),
    })
    await ctx.send(
        CRITIC_ADDRESS,
        ChatMessage(
            timestamp=datetime.now(tz=timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=f"[CRITIC_REQUEST:{session_id}]\n{critic_payload}")],
        ),
    )


async def _run_critic_inline(ctx, session_id, sender, slate):
    """Run the critic logic inline when no external critic agent is configured."""
    from services.critic.agent import critique_slate

    brand_json = _load(ctx, session_id, "brand")
    from services.shared.models import BrandKit
    brand = BrandKit.parse_raw(brand_json)

    await _send_status(ctx, sender, "Critic is reviewing each content piece on 5 quality axes...")

    try:
        verdicts = critique_slate(slate, brand)
    except Exception as exc:
        logger.error("Inline critic failed: %s", exc)
        await _send_final(ctx, sender, f"Critic review failed: {exc}")
        return

    _store(ctx, session_id, "verdicts", json.dumps([v.dict() for v in verdicts]))

    approved = [v for v in verdicts if v.approved]
    rejected = [v for v in verdicts if not v.approved]

    critic_summary = (
        f"CRITIC REVIEW\n{'=' * 40}\n"
        f"{len(approved)}/{len(verdicts)} slots approved\n"
        f"{len(rejected)}/{len(verdicts)} slots rejected\n\n"
    )
    for v in verdicts:
        status = "APPROVED" if v.approved else "REJECTED"
        critic_summary += f"  Slot {v.slot_id}: [{status}] avg={v.average:.1f}/5.0 — {v.summary}\n"

    await _send_status(ctx, sender, critic_summary)

    # Compile final report
    await _compile_final_report(ctx, session_id, sender)


async def _handle_strategist_reply(ctx: Context, sender: str, text: str) -> None:
    """Handle the Strategist sub-agent's reply with the generated Slate."""
    # Parse session_id from prefix
    prefix_end = text.index("]")
    session_id = text[len("[STRATEGIST_REPLY:"):prefix_end]
    payload_text = text[prefix_end + 1:].strip()

    user_sender = _load(ctx, session_id, "sender")
    if not user_sender:
        logger.error("No sender found for session %s", session_id)
        return

    try:
        slate_data = json.loads(payload_text)
        from services.shared.models import Slate
        slate = Slate(**slate_data)
    except Exception as exc:
        logger.error("Failed to parse strategist reply: %s", exc)
        await _send_final(ctx, user_sender, f"Strategist returned invalid data: {exc}")
        return

    _store(ctx, session_id, "slate", slate.json())
    _store(ctx, session_id, "stage", "critique")

    slot_summary = "\n".join(
        f"  {s.slot_number}. [{s.platform.value.upper()}] {s.caption[:80]}..."
        for s in slate.slots
    )
    await _send_status(
        ctx,
        user_sender,
        f"WEEKLY CONTENT PLAN — {len(slate.slots)} slots generated\n"
        f"{'=' * 40}\n{slot_summary}\n\n"
        "Sending to Critic agent for quality review...",
    )

    # Dispatch to Critic
    brand_json = _load(ctx, session_id, "brand")
    critic_payload = json.dumps({
        "session_id": session_id,
        "slate": json.loads(slate.json()),
        "brand": json.loads(brand_json) if brand_json else {},
    })

    if not CRITIC_ADDRESS:
        await _run_critic_inline(ctx, session_id, user_sender, slate)
        return

    await ctx.send(
        CRITIC_ADDRESS,
        ChatMessage(
            timestamp=datetime.now(tz=timezone.utc),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=f"[CRITIC_REQUEST:{session_id}]\n{critic_payload}")],
        ),
    )


async def _handle_critic_reply(ctx: Context, sender: str, text: str) -> None:
    """Handle the Critic sub-agent's reply with verdicts."""
    prefix_end = text.index("]")
    session_id = text[len("[CRITIC_REPLY:"):prefix_end]
    payload_text = text[prefix_end + 1:].strip()

    user_sender = _load(ctx, session_id, "sender")
    if not user_sender:
        logger.error("No sender found for session %s", session_id)
        return

    try:
        verdicts_data = json.loads(payload_text)
        from services.shared.models import CriticVerdict
        verdicts = [CriticVerdict(**v) for v in verdicts_data]
    except Exception as exc:
        logger.error("Failed to parse critic reply: %s", exc)
        await _send_final(ctx, user_sender, f"Critic returned invalid data: {exc}")
        return

    _store(ctx, session_id, "verdicts", json.dumps(verdicts_data))

    approved = [v for v in verdicts if v.approved]
    rejected = [v for v in verdicts if not v.approved]

    critic_summary = (
        f"CRITIC REVIEW\n{'=' * 40}\n"
        f"{len(approved)}/{len(verdicts)} slots approved\n"
        f"{len(rejected)}/{len(verdicts)} slots rejected\n\n"
    )
    for v in verdicts:
        status = "APPROVED" if v.approved else "REJECTED"
        critic_summary += f"  Slot {v.slot_id}: [{status}] avg={v.average:.1f}/5.0 — {v.summary}\n"

    await _send_status(ctx, user_sender, critic_summary)
    await _compile_final_report(ctx, session_id, user_sender)


async def _compile_final_report(ctx: Context, session_id: str, recipient: str) -> None:
    """Compile all pipeline results into a final report and send to user."""
    from services.shared.models import BrandKit, MarketingAnalysis, Slate, CriticVerdict

    brand_json = _load(ctx, session_id, "brand")
    analysis_json = _load(ctx, session_id, "analysis")
    slate_json = _load(ctx, session_id, "slate")
    verdicts_json = _load(ctx, session_id, "verdicts")

    brand = BrandKit.parse_raw(brand_json) if brand_json else None
    analysis = MarketingAnalysis.parse_raw(analysis_json) if analysis_json else None
    slate = Slate.parse_raw(slate_json) if slate_json else None
    verdicts = [CriticVerdict(**v) for v in json.loads(verdicts_json)] if verdicts_json else []

    report_parts = []

    # Marketing Analysis section
    if analysis:
        report_parts.append(
            f"MARKETING ANALYSIS — {analysis.brand_name}\n"
            f"{'=' * 50}\n"
            f"Positioning: {analysis.competitive_positioning}\n\n"
            f"Key Differentiators:\n"
            + "\n".join(f"  - {d}" for d in analysis.key_differentiators)
            + f"\n\nAudience Insights: {analysis.target_audience_insights}\n"
            f"Platforms: {', '.join(p.value for p in analysis.recommended_platforms)}\n"
            f"Themes: {', '.join(analysis.content_themes)}\n"
            f"Tone: {analysis.tone_guidelines}\n"
            f"Cadence: {analysis.weekly_cadence}"
        )

    # Content Plan section
    if slate:
        slot_lines = []
        for s in slate.slots:
            verdict = next((v for v in verdicts if v.slot_id == s.slot_id), None)
            status = ""
            if verdict:
                status = " APPROVED" if verdict.approved else " REJECTED"
                status += f" ({verdict.average:.1f}/5.0)"
            slot_lines.append(
                f"  {s.slot_number}. [{s.platform.value.upper()}]{status}\n"
                f"     Caption: {s.caption}\n"
                f"     Visual: {s.image_prompt}"
            )
        report_parts.append(
            f"\nWEEKLY CONTENT PLAN — {len(slate.slots)} slots\n"
            f"{'=' * 50}\n"
            + "\n\n".join(slot_lines)
        )

    # Critic Summary
    if verdicts:
        approved = sum(1 for v in verdicts if v.approved)
        rejected = sum(1 for v in verdicts if not v.approved)
        report_parts.append(
            f"\nCRITIC SUMMARY\n{'=' * 50}\n"
            f"{approved} approved / {rejected} rejected out of {len(verdicts)} total"
        )

    # Performance context flag
    perf_flag_raw = _load(ctx, session_id, "perf_context_used")
    perf_context_used = perf_flag_raw == "true"
    report_parts.append(
        f"\nPERFORMANCE DATA\n{'=' * 50}\n"
        f"perf_context_used: {perf_context_used}"
    )

    report_parts.append(
        "\n\nThis marketing plan was generated by AgentBuffer's multi-agent system:\n"
        "  Head Agent (orchestration) -> Strategist (content planning) -> Critic (quality control)\n"
        "All agents are registered on Fetch.ai Agentverse and communicate via the Chat Protocol."
    )

    await _send_final(ctx, recipient, "\n\n".join(report_parts))
    _cleanup_session(ctx, session_id)


@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
