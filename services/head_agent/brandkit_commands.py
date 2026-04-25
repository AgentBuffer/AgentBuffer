"""BrandKit chat-command router for the Head Agent.

Parses incoming user text against the supported ``edit brandkit`` vocabulary
and delegates to :mod:`services.shared.brandkit_store`.  Every public function
returns ``(response_text, kit_was_modified)`` so the caller can decide whether
to set the propagation flag.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from uuid import uuid4

from services.shared.brandkit_store import (
    add_keyword,
    add_reference_post,
    add_rule,
    format_history,
    get_brandkit_summary,
    load_brandkit,
    load_history,
    remove_keyword,
    remove_reference_post,
    remove_rule,
    reset_brandkit,
    set_tone,
)
from services.shared.models import Platform, ReferencePost


def _user_brand_ids(ctx) -> tuple[str, str]:
    """Derive user_id and brand_id from the current session.

    The Head Agent stores the serialised BrandKit under
    ``session:<sid>:brand``.  We re-use the kit's own ``brand_id`` and
    ``org_id`` as the storage-key identifiers.
    """
    # Walk active sessions to find brand info
    sender_session_keys = [k for k in _iter_storage_keys(ctx) if k.startswith("sender_session:")]
    for key in sender_session_keys:
        session_id = ctx.storage.get(key)
        if session_id:
            brand_json = ctx.storage.get(f"session:{session_id}:brand")
            if brand_json:
                import json

                data = json.loads(brand_json) if isinstance(brand_json, str) else brand_json
                return data.get("org_id", "default"), data.get("brand_id", "default")
    return "default", "default"


def _iter_storage_keys(ctx):
    """Best-effort iteration over ctx.storage keys."""
    try:
        return ctx.storage.keys()
    except AttributeError:
        return []


# ---------------------------------------------------------------------------
# Command matching
# ---------------------------------------------------------------------------

_COMMANDS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^edit\s+brandkit$", re.I), "show"),
    (re.compile(r"^set\s+tone\s+(\w+)\s+(\d+)$", re.I), "set_tone"),
    (re.compile(r"^add\s+keyword\s+(.+)$", re.I), "add_keyword"),
    (re.compile(r"^remove\s+keyword\s+(.+)$", re.I), "remove_keyword"),
    (re.compile(r"^add\s+rule\s+do\s+(.+)$", re.I), "add_rule_do"),
    (re.compile(r"^add\s+rule\s+dont\s+(.+)$", re.I), "add_rule_dont"),
    (re.compile(r"^remove\s+rule\s+do\s+(\d+)$", re.I), "remove_rule_do"),
    (re.compile(r"^remove\s+rule\s+dont\s+(\d+)$", re.I), "remove_rule_dont"),
    (re.compile(r"^add\s+reference\s+post$", re.I), "add_ref_post_start"),
    (re.compile(r"^remove\s+reference\s+post\s+(.+)$", re.I), "remove_ref_post"),
    (re.compile(r"^show\s+brandkit\s+history$", re.I), "show_history"),
    (re.compile(r"^reset\s+brandkit$", re.I), "reset"),
    (re.compile(r"^regenerate\s+slate$", re.I), "regenerate_slate"),
]


def match_brandkit_command(text: str) -> tuple[str | None, re.Match | None]:
    """Return ``(command_name, match)`` or ``(None, None)``."""
    text = text.strip()
    for pattern, name in _COMMANDS:
        m = pattern.match(text)
        if m:
            return name, m
    return None, None


# ---------------------------------------------------------------------------
# Handlers — each returns (response_text, was_modified)
# ---------------------------------------------------------------------------


def handle_show(ctx, user_id: str, brand_id: str) -> tuple[str, bool]:
    kit = load_brandkit(ctx.storage, user_id, brand_id)
    if kit is None:
        return "No BrandKit found. Complete onboarding first.", False
    return get_brandkit_summary(kit), False


def handle_set_tone(
    ctx, user_id: str, brand_id: str, dimension: str, value: int
) -> tuple[str, bool]:
    kit, msg = set_tone(ctx.storage, user_id, brand_id, dimension, value)
    modified = "set to" in msg
    return msg, modified


def handle_add_keyword(ctx, user_id: str, brand_id: str, word: str) -> tuple[str, bool]:
    kit, msg = add_keyword(ctx.storage, user_id, brand_id, word)
    modified = "added" in msg.lower()
    return msg, modified


def handle_remove_keyword(ctx, user_id: str, brand_id: str, word: str) -> tuple[str, bool]:
    kit, msg = remove_keyword(ctx.storage, user_id, brand_id, word)
    modified = "removed" in msg.lower()
    return msg, modified


def handle_add_rule(
    ctx, user_id: str, brand_id: str, rule_type: str, text: str
) -> tuple[str, bool]:
    kit, msg = add_rule(ctx.storage, user_id, brand_id, rule_type, text)
    modified = "added" in msg.lower()
    return msg, modified


def handle_remove_rule(
    ctx, user_id: str, brand_id: str, rule_type: str, index: int
) -> tuple[str, bool]:
    kit, msg = remove_rule(ctx.storage, user_id, brand_id, rule_type, index)
    modified = "removed" in msg.lower()
    return msg, modified


def handle_add_ref_post_start(ctx, user_id: str, brand_id: str) -> tuple[str, bool]:
    """Begin the interactive reference-post flow."""
    return (
        "Let's add a reference post. Please reply with:\n"
        "  Platform: [instagram|linkedin|twitter|tiktok]\n"
        "  Text: [the post text]\n"
        "  Source (optional): [where this post came from]"
    ), False


def handle_add_ref_post_complete(
    ctx,
    user_id: str,
    brand_id: str,
    platform_str: str,
    text: str,
    source_meta: str = "",
) -> tuple[str, bool]:
    """Complete the reference-post sub-flow with user-supplied data."""
    platform_map = {
        "instagram": Platform.INSTAGRAM,
        "linkedin": Platform.LINKEDIN,
        "twitter": Platform.X,
        "x": Platform.X,
        "tiktok": Platform.TIKTOK,
    }
    platform = platform_map.get(platform_str.lower())
    if platform is None:
        return (
            f"Unknown platform '{platform_str}'. Choose from: {', '.join(platform_map.keys())}."
        ), False

    post = ReferencePost(
        post_id=str(uuid4()),
        platform=platform,
        text=text.strip(),
        source="manual",
        source_meta=source_meta.strip(),
        added_at=datetime.now(tz=timezone.utc),
    )
    kit, msg = add_reference_post(ctx.storage, user_id, brand_id, post)
    modified = "added" in msg.lower()
    return msg, modified


def handle_remove_ref_post(ctx, user_id: str, brand_id: str, post_id: str) -> tuple[str, bool]:
    kit, msg = remove_reference_post(ctx.storage, user_id, brand_id, post_id)
    modified = "removed" in msg.lower()
    return msg, modified


def handle_show_history(ctx, user_id: str, brand_id: str) -> tuple[str, bool]:
    history = load_history(ctx.storage, user_id, brand_id)
    return format_history(history), False


def handle_reset(ctx, user_id: str, brand_id: str, confirmed: bool = False) -> tuple[str, bool]:
    if not confirmed:
        return (
            "Are you sure you want to reset your BrandKit to its original "
            "version? Reply 'confirm reset brandkit' to proceed."
        ), False
    kit, msg = reset_brandkit(ctx.storage, user_id, brand_id)
    modified = "reset" in msg.lower()
    return msg, modified


# ---------------------------------------------------------------------------
# Top-level dispatcher
# ---------------------------------------------------------------------------


def dispatch_brandkit_command(
    ctx,
    user_id: str,
    brand_id: str,
    text: str,
) -> tuple[str, bool] | None:
    """Try to handle *text* as a BrandKit command.

    Returns ``(response_text, kit_was_modified)`` if the text matched a
    command, or ``None`` if no command matched.
    """
    # Special case: confirm reset
    if re.match(r"^confirm\s+reset\s+brandkit$", text.strip(), re.I):
        return handle_reset(ctx, user_id, brand_id, confirmed=True)

    cmd, m = match_brandkit_command(text)
    if cmd is None or m is None:
        return None

    if cmd == "show":
        return handle_show(ctx, user_id, brand_id)
    if cmd == "set_tone":
        return handle_set_tone(ctx, user_id, brand_id, m.group(1), int(m.group(2)))
    if cmd == "add_keyword":
        return handle_add_keyword(ctx, user_id, brand_id, m.group(1))
    if cmd == "remove_keyword":
        return handle_remove_keyword(ctx, user_id, brand_id, m.group(1))
    if cmd == "add_rule_do":
        return handle_add_rule(ctx, user_id, brand_id, "do", m.group(1))
    if cmd == "add_rule_dont":
        return handle_add_rule(ctx, user_id, brand_id, "dont", m.group(1))
    if cmd == "remove_rule_do":
        return handle_remove_rule(ctx, user_id, brand_id, "do", int(m.group(1)))
    if cmd == "remove_rule_dont":
        return handle_remove_rule(ctx, user_id, brand_id, "dont", int(m.group(1)))
    if cmd == "add_ref_post_start":
        return handle_add_ref_post_start(ctx, user_id, brand_id)
    if cmd == "remove_ref_post":
        return handle_remove_ref_post(ctx, user_id, brand_id, m.group(1))
    if cmd == "show_history":
        return handle_show_history(ctx, user_id, brand_id)
    if cmd == "reset":
        return handle_reset(ctx, user_id, brand_id)
    if cmd == "regenerate_slate":
        # Handled separately by the caller (Head Agent) for propagation logic
        return None

    return None
