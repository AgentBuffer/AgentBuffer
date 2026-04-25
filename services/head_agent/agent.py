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
from services.head_agent.brandkit_commands import dispatch_brandkit_command
from services.head_agent.config import (
    CRITIC_ADDRESS,
    HEAD_AGENT_PORT,
    HEAD_AGENT_SEED,
    IMAGE_CREATOR_ADDRESS,
    STRATEGIST_ADDRESS,
)
from services.shared.brandkit_store import load_brandkit

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
    for key in ("stage", "sender", "brand", "analysis", "slate", "verdicts", "user_text"):
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
        await _send_final(
            ctx,
            sender,
            "Please describe your business and product so I can create a marketing plan.",
        )
        return

    # Check if this is a sub-agent reply (Strategist or Critic).
    # Sub-agents prefix replies with [STRATEGIST_REPLY:…] or [CRITIC_REPLY:…]
    if text.startswith("[STRATEGIST_REPLY:"):
        await _handle_strategist_reply(ctx, sender, text)
        return
    if text.startswith("[CRITIC_REPLY:"):
        await _handle_critic_reply(ctx, sender, text)
        return
    if text.startswith("[IMAGE_REPLY:"):
        await _handle_image_reply(ctx, sender, text)
        return

    # ── BrandKit edit commands ──
    bk_result = _try_brandkit_command(ctx, sender, text)
    if bk_result is not None:
        response_text, kit_modified = bk_result
        await _send_status(ctx, sender, response_text)
        if kit_modified:
            await _handle_brandkit_updated(ctx, sender)
        return

    # ── Calendar and manual post commands ──
    normalized_cmd = text.strip().lower()
    if normalized_cmd.startswith("show calendar"):
        await _handle_show_calendar(ctx, sender, text)
        return
    if normalized_cmd.startswith("add post"):
        await _handle_add_post(ctx, sender, text)
        return

    # ── Regenerate slate command ──
    if text.strip().lower() == "regenerate slate":
        await _handle_regenerate_slate(ctx, sender)
        return

    # Check if this is an approval reply from a user with an active session
    existing_session_id = ctx.storage.get(f"sender_session:{sender}")
    if existing_session_id:
        stage = _load(ctx, existing_session_id, "stage")
        if stage == "awaiting_approval":
            await _handle_approval_reply(ctx, existing_session_id, sender, text)
            return

    # Otherwise, this is a new user request
    session_id = str(uuid4())
    _store(ctx, session_id, "sender", sender)
    _store(ctx, session_id, "user_text", text)
    ctx.storage.set(f"sender_session:{sender}", session_id)

    # Stage 1: Brand extraction
    await _send_status(
        ctx, sender, "Analyzing your business... extracting brand identity and positioning."
    )

    try:
        brand = extract_brand_kit(text)
    except Exception as exc:
        logger.error("Brand extraction failed: %s", exc)
        await _send_final(
            ctx,
            sender,
            "I had trouble understanding your business description. "
            "Could you provide more detail about your brand name, "
            f"industry, target audience, and brand voice?\n\nError: {exc}",
        )
        return

    _store(ctx, session_id, "brand", brand.json())
    _store(ctx, session_id, "stage", "analysis")

    # Stage 2: Marketing analysis
    await _send_status(
        ctx,
        sender,
        f"Brand identified: **{brand.name}** in {brand.industry}.\n"
        f"Target audience: {brand.target_audience}\n\n"
        "Now generating your marketing analysis — competitive positioning, "
        "content themes, platform strategy...",
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

    # Stage 3: Dispatch to Strategist
    strategist_payload = json.dumps(
        {
            "session_id": session_id,
            "brand": json.loads(brand.json()),
            "analysis": json.loads(analysis.json()),
        }
    )

    if not STRATEGIST_ADDRESS:
        # If no strategist address, run strategist inline (for local testing)
        await _run_strategist_inline(ctx, session_id, sender, brand, analysis)
        return

    await ctx.send(
        STRATEGIST_ADDRESS,
        ChatMessage(
            timestamp=datetime.now(tz=timezone.utc),
            msg_id=uuid4(),
            content=[
                TextContent(
                    type="text", text=f"[STRATEGIST_REQUEST:{session_id}]\n{strategist_payload}"
                )
            ],
        ),
    )


async def _run_strategist_inline(ctx, session_id, sender, brand, analysis):
    """Run the strategist logic inline when no external strategist agent is configured."""
    from services.strategist.agent import generate_slate

    await _send_status(ctx, sender, "Strategist is crafting your 7-day content slate...")

    try:
        slate = generate_slate(brand, analysis)
    except Exception as exc:
        logger.error("Inline strategist failed: %s", exc)
        await _send_final(ctx, sender, f"Content slate generation failed: {exc}")
        return

    _store(ctx, session_id, "slate", slate.json())
    _store(ctx, session_id, "stage", "critique")

    slot_summary = "\n".join(
        f"  {s.slot_number}. [{s.platform.value.upper()}] {s.caption[:80]}..." for s in slate.slots
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

    critic_payload = json.dumps(
        {
            "session_id": session_id,
            "slate": json.loads(slate.json()),
            "brand": json.loads(brand.json()),
        }
    )
    await ctx.send(
        CRITIC_ADDRESS,
        ChatMessage(
            timestamp=datetime.now(tz=timezone.utc),
            msg_id=uuid4(),
            content=[
                TextContent(type="text", text=f"[CRITIC_REQUEST:{session_id}]\n{critic_payload}")
            ],
        ),
    )


async def _run_critic_inline(ctx, session_id, sender, slate):
    """Run the critic logic inline when no external critic agent is configured."""
    from services.critic.agent import critique_slate

    brand_json = _load(ctx, session_id, "brand")
    from services.shared.models import BrandKit as BrandKitModel

    brand = BrandKitModel.model_validate_json(brand_json)

    await _send_status(ctx, sender, "Critic is reviewing each content piece on 6 quality axes...")

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

    # Dispatch to Image Creator before final report
    await _dispatch_image_generation(ctx, session_id, sender)


async def _handle_strategist_reply(ctx: Context, sender: str, text: str) -> None:
    """Handle the Strategist sub-agent's reply with the generated Slate."""
    # Parse session_id from prefix
    prefix_end = text.index("]")
    session_id = text[len("[STRATEGIST_REPLY:") : prefix_end]
    payload_text = text[prefix_end + 1 :].strip()

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
        f"  {s.slot_number}. [{s.platform.value.upper()}] {s.caption[:80]}..." for s in slate.slots
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
    critic_payload = json.dumps(
        {
            "session_id": session_id,
            "slate": json.loads(slate.json()),
            "brand": json.loads(brand_json) if brand_json else {},
        }
    )

    if not CRITIC_ADDRESS:
        await _run_critic_inline(ctx, session_id, user_sender, slate)
        return

    await ctx.send(
        CRITIC_ADDRESS,
        ChatMessage(
            timestamp=datetime.now(tz=timezone.utc),
            msg_id=uuid4(),
            content=[
                TextContent(type="text", text=f"[CRITIC_REQUEST:{session_id}]\n{critic_payload}")
            ],
        ),
    )


async def _handle_critic_reply(ctx: Context, sender: str, text: str) -> None:
    """Handle the Critic sub-agent's reply with verdicts."""
    prefix_end = text.index("]")
    session_id = text[len("[CRITIC_REPLY:") : prefix_end]
    payload_text = text[prefix_end + 1 :].strip()

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
    await _dispatch_image_generation(ctx, session_id, user_sender)


async def _dispatch_image_generation(ctx: Context, session_id: str, recipient: str) -> None:
    """Dispatch image generation after critic approval, before publishing."""
    from services.shared.models import ApprovedSlate, BrandKit, CriticVerdict, Slate

    slate_json = _load(ctx, session_id, "slate")
    brand_json = _load(ctx, session_id, "brand")
    verdicts_json = _load(ctx, session_id, "verdicts")

    if not slate_json or not brand_json or not verdicts_json:
        await _compile_final_report(ctx, session_id, recipient)
        return

    slate = Slate.parse_raw(slate_json)
    brand = BrandKit.parse_raw(brand_json)
    verdicts = [CriticVerdict(**v) for v in json.loads(verdicts_json)]
    approved_slate = ApprovedSlate(slate=slate, verdicts=verdicts)

    approved_count = sum(1 for v in verdicts if v.approved)
    if approved_count == 0:
        await _compile_final_report(ctx, session_id, recipient)
        return

    await _send_status(ctx, recipient, "Generating AI images for your content...")
    _store(ctx, session_id, "stage", "image_generation")

    if not IMAGE_CREATOR_ADDRESS:
        await _run_image_creator_inline(ctx, session_id, recipient, approved_slate, brand)
        return

    image_payload = json.dumps({
        "approved_slate": json.loads(approved_slate.json()),
        "brand": json.loads(brand.json()),
    })
    await ctx.send(
        IMAGE_CREATOR_ADDRESS,
        ChatMessage(
            timestamp=datetime.now(tz=timezone.utc),
            msg_id=uuid4(),
            content=[
                TextContent(
                    type="text",
                    text=f"[IMAGE_REQUEST:{session_id}]\n{image_payload}",
                )
            ],
        ),
    )


async def _run_image_creator_inline(ctx, session_id, sender, approved_slate, brand):
    """Run the image creator logic inline when no external agent is configured."""
    from services.image_creator.agent import process_approved_slate

    try:
        results = await process_approved_slate(approved_slate, brand)
    except Exception as exc:
        logger.error("Inline image creator failed: %s", exc)
        await _send_status(ctx, sender, f"Image generation encountered an error: {exc}")
        await _compile_final_report(ctx, session_id, sender)
        return

    _apply_image_results(ctx, session_id, results)
    success_count = sum(1 for r in results if r.status == "success")
    await _send_status(
        ctx,
        sender,
        f"Image generation complete: {success_count}/{len(results)} images created successfully.",
    )
    await _compile_final_report(ctx, session_id, sender)


def _apply_image_results(ctx: Context, session_id: str, results: list) -> None:
    """Update stored slate with generated image URLs/paths."""
    from services.shared.models import Slate

    slate_json = _load(ctx, session_id, "slate")
    if not slate_json:
        return

    slate = Slate.parse_raw(slate_json)
    result_map = {r.slot_id: r for r in results if r.status == "success"}

    for slot in slate.slots:
        if slot.slot_id in result_map:
            result = result_map[slot.slot_id]
            slot.image_url = result.image_url or result.local_path

    _store(ctx, session_id, "slate", slate.json())


async def _handle_image_reply(ctx: Context, sender: str, text: str) -> None:
    """Handle the Image Creator sub-agent's reply with generated images."""
    from services.shared.models import ImageResult

    prefix_end = text.index("]")
    session_id = text[len("[IMAGE_REPLY:"):prefix_end]
    payload_text = text[prefix_end + 1:].strip()

    user_sender = _load(ctx, session_id, "sender")
    if not user_sender:
        logger.error("No sender found for session %s", session_id)
        return

    try:
        results_data = json.loads(payload_text)
        if isinstance(results_data, dict) and "error" in results_data:
            logger.error("Image Creator returned error: %s", results_data["error"])
            await _send_status(ctx, user_sender, f"Image generation error: {results_data['error']}")
        else:
            results = [ImageResult(**r) for r in results_data]
            _apply_image_results(ctx, session_id, results)
            success_count = sum(1 for r in results if r.status == "success")
            await _send_status(
                ctx,
                user_sender,
                f"Image generation complete: {success_count}/{len(results)}"
                " images created successfully.",
            )
    except Exception as exc:
        logger.error("Failed to parse image reply: %s", exc)
        await _send_status(ctx, user_sender, f"Image generation returned invalid data: {exc}")

    await _compile_final_report(ctx, session_id, user_sender)


async def _compile_final_report(ctx: Context, session_id: str, recipient: str) -> None:
    """Compile all pipeline results into a final report and send to user."""
    from services.shared.models import (
        CriticVerdict,
        MarketingAnalysis,
        Slate,
    )

    analysis_json = _load(ctx, session_id, "analysis")
    slate_json = _load(ctx, session_id, "slate")
    verdicts_json = _load(ctx, session_id, "verdicts")

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
            f"{'=' * 50}\n" + "\n\n".join(slot_lines)
        )

    # Critic Summary
    if verdicts:
        approved = sum(1 for v in verdicts if v.approved)
        rejected = sum(1 for v in verdicts if not v.approved)
        report_parts.append(
            f"\nCRITIC SUMMARY\n{'=' * 50}\n"
            f"{approved} approved / {rejected} rejected out of {len(verdicts)} total"
        )

        # Surface rule compliance failures
        rule_failures = []
        for v in verdicts:
            for s in v.scores:
                if s.axis == "Rule Compliance" and s.score < 6:
                    rule_failures.append(
                        f"  Slot {v.slot_id}: Rule Compliance {s.score}/10 — {s.reasoning}"
                    )
        if rule_failures:
            report_parts.append(
                f"\nRULE COMPLIANCE ALERTS\n{'=' * 50}\n" + "\n".join(rule_failures)
            )

    report_parts.append(
        "\n\nThis marketing plan was generated by AgentBuffer's "
        "multi-agent system:\n"
        "  Head Agent (orchestration) -> Strategist (content planning)"
        " -> Critic (quality control)\n"
        "All agents are registered on Fetch.ai Agentverse and "
        "communicate via the Chat Protocol."
    )

    await _send_final(ctx, recipient, "\n\n".join(report_parts))
    _cleanup_session(ctx, session_id)


# ── BrandKit command routing ──


def _try_brandkit_command(ctx: Context, sender: str, text: str) -> tuple[str, bool] | None:
    """Attempt to match *text* as a BrandKit command.

    Returns ``(response, kit_modified)`` or ``None`` if not a BrandKit command.
    """
    # Derive user/brand ids from the active session
    session_id = ctx.storage.get(f"sender_session:{sender}")
    user_id, brand_id = "default", "default"
    if session_id:
        brand_raw = _load(ctx, session_id, "brand")
        if brand_raw:
            data = json.loads(brand_raw) if isinstance(brand_raw, str) else brand_raw
            user_id = data.get("org_id", "default")
            brand_id = data.get("brand_id", "default")

    return dispatch_brandkit_command(ctx, user_id, brand_id, text)


async def _handle_brandkit_updated(ctx: Context, sender: str) -> None:
    """Set the propagation flag and notify the user."""
    session_id = ctx.storage.get(f"sender_session:{sender}")
    if session_id:
        # Only set flag if a slate has already been generated in this session
        slate_json = _load(ctx, session_id, "slate")
        if slate_json:
            ctx.storage.set(f"session:{session_id}:brandkit_updated", "true")
            await _send_status(
                ctx,
                sender,
                "BrandKit updated. Changes will apply to your next content slate. "
                "Reply 'regenerate slate' to apply them to the current queue.",
            )


async def _handle_regenerate_slate(ctx: Context, sender: str) -> None:
    """Re-run the Strategist -> Critic pipeline with the updated BrandKit."""
    session_id = ctx.storage.get(f"sender_session:{sender}")
    if not session_id:
        await _send_status(ctx, sender, "No active session found.")
        return

    brand_raw = _load(ctx, session_id, "brand")
    analysis_raw = _load(ctx, session_id, "analysis")
    if not brand_raw or not analysis_raw:
        await _send_status(
            ctx, sender, "Cannot regenerate — brand data or analysis missing from this session."
        )
        return

    from services.shared.models import BrandKit as BrandKitModel
    from services.shared.models import MarketingAnalysis

    brand = BrandKitModel.model_validate_json(brand_raw)
    user_id = brand.org_id
    brand_id_val = brand.brand_id

    # Load the updated BrandKit from versioned storage
    updated_kit = load_brandkit(ctx.storage, user_id, brand_id_val)
    if updated_kit:
        brand = updated_kit
        _store(ctx, session_id, "brand", brand.model_dump_json())

    analysis = MarketingAnalysis.model_validate_json(analysis_raw)

    # Clear old verdicts
    ctx.storage.remove(f"session:{session_id}:verdicts")
    ctx.storage.remove(f"session:{session_id}:brandkit_updated")
    _store(ctx, session_id, "stage", "strategize")

    await _send_status(ctx, sender, "Regenerating content slate with your updated BrandKit...")

    if not STRATEGIST_ADDRESS:
        await _run_strategist_inline(ctx, session_id, sender, brand, analysis)
        return

    strategist_payload = json.dumps(
        {
            "session_id": session_id,
            "brand": json.loads(brand.model_dump_json()),
            "analysis": json.loads(analysis.model_dump_json()),
        }
    )
    await ctx.send(
        STRATEGIST_ADDRESS,
        ChatMessage(
            timestamp=datetime.now(tz=timezone.utc),
            msg_id=uuid4(),
            content=[
                TextContent(
                    type="text", text=f"[STRATEGIST_REQUEST:{session_id}]\n{strategist_payload}"
                )
            ],
        ),
    )


# ── Calendar & Manual Post Commands ──


async def _handle_show_calendar(
    ctx: Context,
    sender: str,
    text: str,
) -> None:
    """Handle 'show calendar [week of YYYY-MM-DD]' command."""
    from datetime import timedelta

    from services.shared.models import Slate

    # Parse optional week date
    match = re.search(r"week of (\d{4}-\d{2}-\d{2})", text.strip().lower())
    if match:
        try:
            target = datetime.strptime(match.group(1), "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            await _send_status(
                ctx, sender, "Invalid date format. Use: show calendar week of YYYY-MM-DD"
            )
            return
    else:
        target = datetime.now(tz=timezone.utc)

    # Find Monday of that week
    monday = target - timedelta(days=target.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)

    # Find the active session for this sender
    session_id = ctx.storage.get(f"sender_session:{sender}")
    if not session_id:
        await _send_status(
            ctx,
            sender,
            "No active session found. Please onboard a brand first to generate content.",
        )
        return

    # Read from approval queue first, fall back to slate
    queue_json = ctx.storage.get(f"approval_queue:{session_id}")
    slate_json = _load(ctx, session_id, "slate")

    posts: list[dict] = []
    if queue_json:
        posts = json.loads(queue_json)
    elif slate_json:
        slate = Slate.parse_raw(slate_json)
        for slot in slate.slots:
            posts.append(
                {
                    "slot_id": slot.slot_id,
                    "platform": slot.platform.value,
                    "scheduled_time": slot.scheduled_for.isoformat(),
                    "content_text": slot.caption,
                    "status": slot.status,
                }
            )

    # Filter to the requested week
    week_posts: list[dict] = []
    for p in posts:
        try:
            st = datetime.fromisoformat(p.get("scheduled_time", "").replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue
        if monday <= st < monday + timedelta(days=7):
            week_posts.append(p)

    week_posts.sort(key=lambda x: x.get("scheduled_time", ""))

    # Build plain-text digest
    brand_json = _load(ctx, session_id, "brand")
    brand_name = "Your brand"
    if brand_json:
        from services.shared.models import BrandKit

        brand = BrandKit.parse_raw(brand_json)
        brand_name = brand.name

    lines = [
        f"{brand_name} — week of {monday.strftime('%b %d')}",
        "",
    ]

    current_day = ""
    counts = {"approved": 0, "pending": 0, "skipped": 0}
    for p in week_posts:
        try:
            st = datetime.fromisoformat(p["scheduled_time"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue
        day_label = st.strftime("%a %b %d")
        if day_label != current_day:
            current_day = day_label
            lines.append(day_label)
        time_str = st.strftime("%-I:%M %p")
        platform = p.get("platform", "?").capitalize()
        status = p.get("status", "pending")
        status_label = f"[{status.capitalize()}]"
        preview = p.get("content_text", "")[:60]
        if len(p.get("content_text", "")) > 60:
            preview += "..."
        lines.append(f'  {time_str}  {platform:10s} {status_label:12s} "{preview}"')
        counts[status] = counts.get(status, 0) + 1

    lines.append("")
    lines.append(
        f"{counts.get('approved', 0)} posts approved · "
        f"{counts.get('pending', 0)} pending review · "
        f"{counts.get('skipped', 0)} skipped"
    )
    lines.append('Reply "approve all" to approve all pending posts.')

    await _send_status(ctx, sender, "\n".join(lines))


async def _handle_add_post(
    ctx: Context,
    sender: str,
    text: str,
) -> None:
    """Handle 'add post [platform] [date YYYY-MM-DD] [time HH:MM] [content]' command."""
    from datetime import timedelta

    session_id = ctx.storage.get(f"sender_session:{sender}")
    if not session_id:
        await _send_status(
            ctx,
            sender,
            "No active session found. Please onboard a brand first.",
        )
        return

    # Parse command: add post <platform> <date> <time> <content>
    parts = text.strip().split(None, 5)  # ['add', 'post', platform, date, time, content]
    if len(parts) < 6:
        await _send_status(
            ctx,
            sender,
            "Usage: add post <platform> <YYYY-MM-DD> <HH:MM> <content text>\n"
            "Platforms: instagram, twitter, linkedin, tiktok",
        )
        return

    platform_raw = parts[2].lower()
    date_str = parts[3]
    time_str = parts[4]
    content_text = parts[5]

    # Validate platform
    valid_platforms = {"instagram", "twitter", "linkedin", "tiktok"}
    if platform_raw not in valid_platforms:
        await _send_status(
            ctx,
            sender,
            f"Invalid platform '{platform_raw}'. Choose from: instagram, twitter, linkedin, tiktok",
        )
        return

    # Map twitter -> x for internal use
    platform_internal = "x" if platform_raw == "twitter" else platform_raw

    # Validate date
    try:
        post_date = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        await _send_status(
            ctx,
            sender,
            "Invalid date/time format. Use: YYYY-MM-DD HH:MM (e.g. 2026-05-01 09:00)",
        )
        return

    now = datetime.now(tz=timezone.utc)
    if post_date < now:
        await _send_status(ctx, sender, "Cannot schedule a post in the past.")
        return
    if post_date > now + timedelta(days=30):
        await _send_status(
            ctx,
            sender,
            "Cannot schedule more than 30 days in advance.",
        )
        return

    # Create new slot in approval queue
    new_slot_id = f"slot-manual-{uuid4().hex[:8]}"
    new_item = {
        "slot_id": new_slot_id,
        "platform": platform_internal,
        "scheduled_time": post_date.isoformat(),
        "content_text": content_text,
        "video_url": None,
        "critic_score": 0.0,
        "status": "approved",
        "note": "manually added",
    }

    queue_json = ctx.storage.get(f"approval_queue:{session_id}")
    queue_items = json.loads(queue_json) if queue_json else []
    queue_items.append(new_item)
    ctx.storage.set(f"approval_queue:{session_id}", json.dumps(queue_items))

    await _send_status(
        ctx,
        sender,
        f"Manual post added and auto-approved:\n"
        f"  Platform: {platform_raw}\n"
        f"  Scheduled: {post_date.strftime('%a %b %d at %-I:%M %p')} UTC\n"
        f"  Content: {content_text[:120]}\n\n"
        "Note: Manual posts bypass the Critic by default.",
    )


@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
