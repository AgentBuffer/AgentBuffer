"""Head Agent — the orchestrator that users interact with via ASI:One.

Implements a state machine using ctx.storage for async sub-agent handoffs.
Sends intermediate ChatMessage updates so the user sees progress in real-time.

Supports multi-brand workspaces: each user (identified by their ASI:One wallet
address) can own multiple brands, switch between them, and run the full
pipeline scoped to the active brand.

Pipeline stages:
  1. INTAKE       — parse business description, extract BrandKit
  2. ANALYSIS     — generate marketing analysis via LLM
  3. STRATEGIZE   — dispatch to Strategist, await Slate
  4. CRITIQUE     — dispatch to Critic, await verdicts
  5. VIDEO        — dispatch to Video Creator (if video slots exist)
  6. PUBLISH      — dispatch to Publisher
  7. REPORT       — compile final report, send to user

Storage key conventions:
  brands:{user_id}                           — JSON list of BrandRegistryEntry
  brand:{user_id}:{brand_id}:kit             — serialized BrandKit
  brand:{user_id}:{brand_id}:analysis        — serialized MarketingAnalysis
  perf:{user_id}:{brand_id}:{post_id}        — serialized PerformanceRecord
  session:{session_id}:active_brand          — active brand_id for session
  session:{session_id}:stage                 — current pipeline stage
  session:{session_id}:sender                — original user address
  session:{session_id}:user_id               — derived user_id
  session:{session_id}:brand                 — serialized BrandKit (pipeline)
  session:{session_id}:analysis              — serialized MarketingAnalysis
  session:{session_id}:slate                 — serialized Slate from Strategist
  session:{session_id}:verdicts              — serialized CriticVerdicts
  session:{session_id}:pending_delete        — brand_id awaiting delete confirm
  sender_session:{sender}                    — maps sender address to session_id
"""

from __future__ import annotations

import json
import logging
import re
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
from services.shared.models import (
    BrandKit,
    BrandRegistryEntry,
    CriticVerdict,
    MarketingAnalysis,
    Slate,
)

logger = logging.getLogger(__name__)

agent = Agent(
    name="AgentBuffer-Marketing-Director",
    seed=HEAD_AGENT_SEED,
    port=HEAD_AGENT_PORT,
    mailbox=True,
    publish_agent_details=True,
)

protocol = Protocol(spec=chat_protocol_spec)

# ---------------------------------------------------------------------------
# Helpers — messaging
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Helpers — session storage (unchanged key scheme for session-transient data)
# ---------------------------------------------------------------------------


def _store(ctx: Context, session_id: str, key: str, value: str) -> None:
    ctx.storage.set(f"session:{session_id}:{key}", value)


def _load(ctx: Context, session_id: str, key: str) -> str | None:
    return ctx.storage.get(f"session:{session_id}:{key}")


def _cleanup_session(ctx: Context, session_id: str) -> None:
    """Remove all session keys from storage."""
    for key in (
        "stage",
        "sender",
        "user_id",
        "brand",
        "analysis",
        "slate",
        "verdicts",
        "user_text",
        "active_brand",
        "pending_delete",
    ):
        ctx.storage.remove(f"session:{session_id}:{key}")


# ---------------------------------------------------------------------------
# Helpers — user_id derivation
# ---------------------------------------------------------------------------


def _derive_user_id(sender: str) -> str:
    """Derive a stable user_id from the sender's wallet / agent address."""
    return sender


# ---------------------------------------------------------------------------
# Helpers — brand registry (persistent, user-scoped)
# ---------------------------------------------------------------------------


def _get_brand_registry(ctx: Context, user_id: str) -> list[BrandRegistryEntry]:
    raw = ctx.storage.get(f"brands:{user_id}")
    if not raw:
        return []
    return [BrandRegistryEntry(**entry) for entry in json.loads(raw)]


def _save_brand_registry(ctx: Context, user_id: str, entries: list[BrandRegistryEntry]) -> None:
    ctx.storage.set(
        f"brands:{user_id}",
        json.dumps([e.dict() for e in entries], default=str),
    )


def _register_brand(
    ctx: Context, user_id: str, brand_id: str, brand_name: str
) -> BrandRegistryEntry:
    """Add a new brand to the user's registry and return the entry."""
    now = datetime.now(tz=timezone.utc)
    entry = BrandRegistryEntry(
        brand_id=brand_id,
        brand_name=brand_name,
        created_at=now,
        last_active=now,
    )
    registry = _get_brand_registry(ctx, user_id)
    registry.append(entry)
    _save_brand_registry(ctx, user_id, registry)
    return entry


def _touch_brand(ctx: Context, user_id: str, brand_id: str) -> None:
    """Update last_active timestamp for a brand."""
    registry = _get_brand_registry(ctx, user_id)
    for entry in registry:
        if entry.brand_id == brand_id:
            entry.last_active = datetime.now(tz=timezone.utc)
            break
    _save_brand_registry(ctx, user_id, registry)


def _find_most_recent_brand(ctx: Context, user_id: str) -> BrandRegistryEntry | None:
    registry = _get_brand_registry(ctx, user_id)
    if not registry:
        return None
    return max(registry, key=lambda e: e.last_active)


# ---------------------------------------------------------------------------
# Helpers — brand-scoped persistent storage
# ---------------------------------------------------------------------------


def _store_brand_data(ctx: Context, user_id: str, brand_id: str, key: str, value: str) -> None:
    ctx.storage.set(f"brand:{user_id}:{brand_id}:{key}", value)


def _load_brand_data(ctx: Context, user_id: str, brand_id: str, key: str) -> str | None:
    return ctx.storage.get(f"brand:{user_id}:{brand_id}:{key}")


def _delete_brand_storage(ctx: Context, user_id: str, brand_id: str) -> None:
    """Remove all persistent storage keys for a brand."""
    for key in ("kit", "analysis"):
        ctx.storage.remove(f"brand:{user_id}:{brand_id}:{key}")
    # Remove performance records — iterate known keys by prefix convention.
    # ctx.storage does not expose iteration, so we track perf keys in a list.
    perf_index_raw = ctx.storage.get(f"brand:{user_id}:{brand_id}:perf_index")
    if perf_index_raw:
        for post_id in json.loads(perf_index_raw):
            ctx.storage.remove(f"perf:{user_id}:{brand_id}:{post_id}")
        ctx.storage.remove(f"brand:{user_id}:{brand_id}:perf_index")


# ---------------------------------------------------------------------------
# Helpers — resolve active brand for a session
# ---------------------------------------------------------------------------


def _get_active_brand_id(ctx: Context, session_id: str) -> str | None:
    return _load(ctx, session_id, "active_brand")


def _set_active_brand_id(ctx: Context, session_id: str, brand_id: str) -> None:
    _store(ctx, session_id, "active_brand", brand_id)


# ---------------------------------------------------------------------------
# Brand command routing
# ---------------------------------------------------------------------------

_CMD_LIST_BRANDS = re.compile(r"^\s*list\s+brands?\s*$", re.IGNORECASE)
_CMD_SWITCH_BRAND = re.compile(r"^\s*switch\s+brand\s+(\S+)\s*$", re.IGNORECASE)
_CMD_CREATE_BRAND = re.compile(r"^\s*create\s+brand\s*$", re.IGNORECASE)
_CMD_DELETE_BRAND = re.compile(r"^\s*delete\s+brand\s+(\S+)\s*$", re.IGNORECASE)
_CMD_CONFIRM_YES = re.compile(r"^\s*(yes|confirm)\s*$", re.IGNORECASE)
_CMD_CONFIRM_NO = re.compile(r"^\s*(no|cancel)\s*$", re.IGNORECASE)


async def _handle_list_brands(ctx: Context, sender: str, user_id: str, session_id: str) -> None:
    registry = _get_brand_registry(ctx, user_id)
    if not registry:
        await _send_status(
            ctx,
            sender,
            "You have no brands yet. Send a business description to create your first brand.",
        )
        return

    active_id = _get_active_brand_id(ctx, session_id)
    lines = ["YOUR BRANDS\n" + "=" * 40]
    for e in registry:
        marker = " (active)" if e.brand_id == active_id else ""
        lines.append(
            f"  {e.brand_name} — id: {e.brand_id}{marker}\n"
            f"    created: {e.created_at:%Y-%m-%d}  last active: {e.last_active:%Y-%m-%d}"
        )
    await _send_status(ctx, sender, "\n".join(lines))


async def _handle_switch_brand(
    ctx: Context,
    sender: str,
    user_id: str,
    session_id: str,
    brand_id: str,
) -> None:
    registry = _get_brand_registry(ctx, user_id)
    entry = next((e for e in registry if e.brand_id == brand_id), None)
    if entry is None:
        await _send_status(
            ctx,
            sender,
            f"Brand '{brand_id}' not found. Use 'list brands' to see your brands.",
        )
        return

    _set_active_brand_id(ctx, session_id, brand_id)
    _touch_brand(ctx, user_id, brand_id)
    await _send_status(ctx, sender, f"Switched to brand **{entry.brand_name}** ({brand_id}).")


async def _handle_delete_brand_request(
    ctx: Context,
    sender: str,
    user_id: str,
    session_id: str,
    brand_id: str,
) -> None:
    registry = _get_brand_registry(ctx, user_id)
    entry = next((e for e in registry if e.brand_id == brand_id), None)
    if entry is None:
        await _send_status(
            ctx,
            sender,
            f"Brand '{brand_id}' not found. Use 'list brands' to see your brands.",
        )
        return

    _store(ctx, session_id, "pending_delete", brand_id)
    await _send_status(
        ctx,
        sender,
        f"Are you sure you want to delete brand **{entry.brand_name}** ({brand_id})? "
        "This will permanently remove the BrandKit, marketing analysis, and all "
        "performance records for this brand.\n\nReply **yes** to confirm or **no** to cancel.",
    )


async def _handle_delete_confirm(ctx: Context, sender: str, user_id: str, session_id: str) -> None:
    brand_id = _load(ctx, session_id, "pending_delete")
    if not brand_id:
        return

    ctx.storage.remove(f"session:{session_id}:pending_delete")

    registry = _get_brand_registry(ctx, user_id)
    entry = next((e for e in registry if e.brand_id == brand_id), None)
    if entry is None:
        await _send_status(ctx, sender, "Brand already removed.")
        return

    brand_name = entry.brand_name
    registry = [e for e in registry if e.brand_id != brand_id]
    _save_brand_registry(ctx, user_id, registry)
    _delete_brand_storage(ctx, user_id, brand_id)

    active = _get_active_brand_id(ctx, session_id)
    if active == brand_id:
        if registry:
            new_active = max(registry, key=lambda e: e.last_active)
            _set_active_brand_id(ctx, session_id, new_active.brand_id)
            await _send_status(
                ctx,
                sender,
                f"Brand **{brand_name}** deleted. Switched to **{new_active.brand_name}**.",
            )
        else:
            ctx.storage.remove(f"session:{session_id}:active_brand")
            await _send_status(
                ctx,
                sender,
                f"Brand **{brand_name}** deleted. You have no remaining brands.",
            )
    else:
        await _send_status(ctx, sender, f"Brand **{brand_name}** deleted successfully.")


async def _handle_delete_cancel(ctx: Context, sender: str, session_id: str) -> None:
    brand_id = _load(ctx, session_id, "pending_delete")
    if not brand_id:
        return
    ctx.storage.remove(f"session:{session_id}:pending_delete")
    await _send_status(ctx, sender, "Brand deletion cancelled.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    """Entry point: user sends a command / business description, or a sub-agent replies."""
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

    if not text.strip():
        await _send_final(
            ctx,
            sender,
            "Please describe your business and product so I can create a marketing plan.",
        )
        return

    # ── Sub-agent replies ──
    if text.startswith("[STRATEGIST_REPLY:"):
        await _handle_strategist_reply(ctx, sender, text)
        return
    if text.startswith("[CRITIC_REPLY:"):
        await _handle_critic_reply(ctx, sender, text)
        return

    # ── Derive user_id and resolve / create session ──
    user_id = _derive_user_id(sender)

    existing_session_id = ctx.storage.get(f"sender_session:{sender}")
    if existing_session_id:
        session_id = existing_session_id
    else:
        session_id = str(uuid4())
        ctx.storage.set(f"sender_session:{sender}", session_id)

    _store(ctx, session_id, "sender", sender)
    _store(ctx, session_id, "user_id", user_id)

    # If no active brand yet, try to restore from most-recently-active brand
    if not _get_active_brand_id(ctx, session_id):
        recent = _find_most_recent_brand(ctx, user_id)
        if recent:
            _set_active_brand_id(ctx, session_id, recent.brand_id)

    # ── Pending delete confirmation? ──
    pending_delete = _load(ctx, session_id, "pending_delete")
    if pending_delete:
        if _CMD_CONFIRM_YES.match(text):
            await _handle_delete_confirm(ctx, sender, user_id, session_id)
            return
        if _CMD_CONFIRM_NO.match(text):
            await _handle_delete_cancel(ctx, sender, session_id)
            return
        # Any other input cancels the pending delete implicitly
        ctx.storage.remove(f"session:{session_id}:pending_delete")

    # ── Brand management commands ──
    if _CMD_LIST_BRANDS.match(text):
        await _handle_list_brands(ctx, sender, user_id, session_id)
        return

    m = _CMD_SWITCH_BRAND.match(text)
    if m:
        await _handle_switch_brand(ctx, sender, user_id, session_id, m.group(1))
        return

    if _CMD_CREATE_BRAND.match(text):
        await _send_status(
            ctx,
            sender,
            "Starting brand onboarding. Please describe your business "
            "and product so I can build your BrandKit.",
        )
        return

    m = _CMD_DELETE_BRAND.match(text)
    if m:
        await _handle_delete_brand_request(ctx, sender, user_id, session_id, m.group(1))
        return

    # ── Pipeline: new brand creation / onboarding ──
    await _run_intake(ctx, sender, user_id, session_id, text)


# ---------------------------------------------------------------------------
# Pipeline stage 1 — Intake (brand extraction + registration)
# ---------------------------------------------------------------------------


async def _run_intake(
    ctx: Context,
    sender: str,
    user_id: str,
    session_id: str,
    text: str,
) -> None:
    _store(ctx, session_id, "user_text", text)
    _store(ctx, session_id, "stage", "intake")

    await _send_status(
        ctx,
        sender,
        "Analyzing your business... extracting brand identity and positioning.",
    )

    try:
        brand = extract_brand_kit(text)
    except Exception as exc:
        logger.error("Brand extraction failed: %s", exc)
        await _send_final(
            ctx,
            sender,
            f"I had trouble understanding your business description. Could you provide "
            f"more detail about your brand name, industry, target audience, and brand voice?\n\n"
            f"Error: {exc}",
        )
        return

    # Assign a fresh UUID as brand_id
    brand_id = str(uuid4())
    brand.brand_id = brand_id
    brand.org_id = user_id

    # Register the brand under this user
    _register_brand(ctx, user_id, brand_id, brand.name)
    _set_active_brand_id(ctx, session_id, brand_id)

    # Persist BrandKit under the new key scheme
    _store_brand_data(ctx, user_id, brand_id, "kit", brand.json())
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
        await _send_final(
            ctx,
            sender,
            f"Marketing analysis generation encountered an error: {exc}",
        )
        return

    _store_brand_data(ctx, user_id, brand_id, "analysis", analysis.json())
    _store(ctx, session_id, "analysis", analysis.json())
    _store(ctx, session_id, "stage", "strategize")

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
            "user_id": user_id,
            "brand_id": brand_id,
            "brand": json.loads(brand.json()),
            "analysis": json.loads(analysis.json()),
        }
    )

    if not STRATEGIST_ADDRESS:
        await _run_strategist_inline(ctx, session_id, sender, brand, analysis)
        return

    await ctx.send(
        STRATEGIST_ADDRESS,
        ChatMessage(
            timestamp=datetime.now(tz=timezone.utc),
            msg_id=uuid4(),
            content=[
                TextContent(
                    type="text",
                    text=f"[STRATEGIST_REQUEST:{session_id}]\n{strategist_payload}",
                )
            ],
        ),
    )


# ---------------------------------------------------------------------------
# Inline sub-agent runners (for local / single-process testing)
# ---------------------------------------------------------------------------


async def _run_strategist_inline(
    ctx: Context,
    session_id: str,
    sender: str,
    brand: BrandKit,
    analysis: MarketingAnalysis,
) -> None:
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

    user_id = _load(ctx, session_id, "user_id") or ""
    brand_id = _get_active_brand_id(ctx, session_id) or brand.brand_id

    if not CRITIC_ADDRESS:
        await _run_critic_inline(ctx, session_id, sender, slate)
        return

    critic_payload = json.dumps(
        {
            "session_id": session_id,
            "user_id": user_id,
            "brand_id": brand_id,
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
                TextContent(
                    type="text",
                    text=f"[CRITIC_REQUEST:{session_id}]\n{critic_payload}",
                )
            ],
        ),
    )


async def _run_critic_inline(
    ctx: Context,
    session_id: str,
    sender: str,
    slate: Slate,
) -> None:
    from services.critic.agent import critique_slate

    brand_json = _load(ctx, session_id, "brand")
    brand = BrandKit.parse_raw(brand_json)

    await _send_status(
        ctx,
        sender,
        "Critic is reviewing each content piece on 5 quality axes...",
    )

    try:
        verdicts = critique_slate(slate, brand)
    except Exception as exc:
        logger.error("Inline critic failed: %s", exc)
        await _send_final(ctx, sender, f"Critic review failed: {exc}")
        return

    _store(
        ctx,
        session_id,
        "verdicts",
        json.dumps([v.dict() for v in verdicts]),
    )

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
    await _compile_final_report(ctx, session_id, sender)


# ---------------------------------------------------------------------------
# Sub-agent reply handlers
# ---------------------------------------------------------------------------


async def _handle_strategist_reply(ctx: Context, sender: str, text: str) -> None:
    prefix_end = text.index("]")
    session_id = text[len("[STRATEGIST_REPLY:") : prefix_end]
    payload_text = text[prefix_end + 1 :].strip()

    user_sender = _load(ctx, session_id, "sender")
    if not user_sender:
        logger.error("No sender found for session %s", session_id)
        return

    try:
        slate_data = json.loads(payload_text)
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

    user_id = _load(ctx, session_id, "user_id") or ""
    brand_id = _get_active_brand_id(ctx, session_id) or ""
    brand_json = _load(ctx, session_id, "brand")

    critic_payload = json.dumps(
        {
            "session_id": session_id,
            "user_id": user_id,
            "brand_id": brand_id,
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
                TextContent(
                    type="text",
                    text=f"[CRITIC_REQUEST:{session_id}]\n{critic_payload}",
                )
            ],
        ),
    )


async def _handle_critic_reply(ctx: Context, sender: str, text: str) -> None:
    prefix_end = text.index("]")
    session_id = text[len("[CRITIC_REPLY:") : prefix_end]
    payload_text = text[prefix_end + 1 :].strip()

    user_sender = _load(ctx, session_id, "sender")
    if not user_sender:
        logger.error("No sender found for session %s", session_id)
        return

    try:
        verdicts_data = json.loads(payload_text)
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


# ---------------------------------------------------------------------------
# Final report
# ---------------------------------------------------------------------------


async def _compile_final_report(ctx: Context, session_id: str, recipient: str) -> None:
    brand_json = _load(ctx, session_id, "brand")
    analysis_json = _load(ctx, session_id, "analysis")
    slate_json = _load(ctx, session_id, "slate")
    verdicts_json = _load(ctx, session_id, "verdicts")

    _brand = BrandKit.parse_raw(brand_json) if brand_json else None  # noqa: F841
    analysis = MarketingAnalysis.parse_raw(analysis_json) if analysis_json else None
    slate = Slate.parse_raw(slate_json) if slate_json else None
    verdicts = [CriticVerdict(**v) for v in json.loads(verdicts_json)] if verdicts_json else []

    report_parts: list[str] = []

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

    if verdicts:
        approved_count = sum(1 for v in verdicts if v.approved)
        rejected_count = sum(1 for v in verdicts if not v.approved)
        report_parts.append(
            f"\nCRITIC SUMMARY\n{'=' * 50}\n"
            f"{approved_count} approved / {rejected_count} rejected out of {len(verdicts)} total"
        )

    report_parts.append(
        "\n\nThis marketing plan was generated by AgentBuffer's multi-agent system:\n"
        "  Head Agent (orchestration) -> Strategist (content planning) -> "
        "Critic (quality control)\n"
        "All agents are registered on Fetch.ai Agentverse and communicate "
        "via the Chat Protocol."
    )

    await _send_final(ctx, recipient, "\n\n".join(report_parts))
    _cleanup_session(ctx, session_id)


@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


agent.include(protocol, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
