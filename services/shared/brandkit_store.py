"""Versioned BrandKit storage helpers.

Provides read / write / migrate / history operations on top of
``ctx.storage`` using two keys per brand:

- ``brand:{user_id}:{brand_id}:kit:current`` -> active BrandKit dict
- ``brand:{user_id}:{brand_id}:kit:history`` -> append-only list of
  ``BrandKitHistoryEntry`` dicts
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from services.shared.models import (
    BrandKit,
    BrandKitHistoryEntry,
    ContentRules,
    ReferencePost,
    ToneProfile,
)


def _current_key(user_id: str, brand_id: str) -> str:
    return f"brand:{user_id}:{brand_id}:kit:current"


def _history_key(user_id: str, brand_id: str) -> str:
    return f"brand:{user_id}:{brand_id}:kit:history"


def _legacy_key(user_id: str, brand_id: str) -> str:
    return f"brand:{user_id}:{brand_id}:kit"


# -- Reads -------------------------------------------------------------------


def load_brandkit(storage, user_id: str, brand_id: str) -> BrandKit | None:
    """Load the active BrandKit.  Returns *None* when no kit exists."""
    raw = storage.get(_current_key(user_id, brand_id))
    if raw is not None:
        data = json.loads(raw) if isinstance(raw, str) else raw
        return BrandKit(**data)

    # Fall back to legacy flat key (read-only — no migration on read)
    raw = storage.get(_legacy_key(user_id, brand_id))
    if raw is not None:
        data = json.loads(raw) if isinstance(raw, str) else raw
        return BrandKit(**data)

    return None


def load_history(storage, user_id: str, brand_id: str) -> list[BrandKitHistoryEntry]:
    raw = storage.get(_history_key(user_id, brand_id))
    if raw is None:
        return []
    entries = json.loads(raw) if isinstance(raw, str) else raw
    return [BrandKitHistoryEntry(**e) for e in entries]


# -- Writes ------------------------------------------------------------------


def _save_current(storage, user_id: str, brand_id: str, kit: BrandKit) -> None:
    storage.set(_current_key(user_id, brand_id), kit.model_dump_json())


def _append_history(
    storage,
    user_id: str,
    brand_id: str,
    entry: BrandKitHistoryEntry,
) -> None:
    history = load_history(storage, user_id, brand_id)
    history.append(entry)
    storage.set(
        _history_key(user_id, brand_id),
        json.dumps([e.model_dump(mode="json") for e in history]),
    )


def _make_history_entry(
    old_kit: BrandKit,
    changed_fields: list[str],
) -> BrandKitHistoryEntry:
    return BrandKitHistoryEntry(
        version=old_kit.version,
        timestamp=datetime.now(tz=timezone.utc),
        changed_fields=changed_fields,
        snapshot=json.loads(old_kit.model_dump_json()),
    )


# -- Migration ----------------------------------------------------------------


def migrate_if_needed(storage, user_id: str, brand_id: str) -> BrandKit:
    """Ensure the BrandKit lives in the versioned schema.

    Called lazily on first *edit*.  Reads the kit, backfills new fields with
    neutral defaults, bumps to version 2, and writes both ``kit:current`` and
    the initial ``kit:history`` entry.
    """
    kit = load_brandkit(storage, user_id, brand_id)
    if kit is None:
        raise ValueError(f"No BrandKit found for user={user_id} brand={brand_id}")

    # Already migrated?
    current_raw = storage.get(_current_key(user_id, brand_id))
    if current_raw is not None:
        return kit

    # Snapshot v1 before migration
    v1_snapshot = json.loads(kit.model_dump_json())

    kit.tone = ToneProfile()
    kit.personality_keywords = kit.personality_keywords or []
    kit.content_rules = kit.content_rules or ContentRules()
    kit.reference_posts = kit.reference_posts or []
    kit.version = 2
    kit.last_updated = datetime.now(tz=timezone.utc)

    _save_current(storage, user_id, brand_id, kit)

    # Seed history with the v1 snapshot
    entry = BrandKitHistoryEntry(
        version=1,
        timestamp=kit.last_updated,
        changed_fields=["migration_to_v2"],
        snapshot=v1_snapshot,
    )
    _append_history(storage, user_id, brand_id, entry)

    return kit


# -- Edit helpers (return updated kit + message) -----------------------------


def _commit_edit(
    storage,
    user_id: str,
    brand_id: str,
    kit: BrandKit,
    changed_fields: list[str],
) -> BrandKit:
    """Snapshot pre-edit state, bump version, persist, and return new kit."""
    old_kit_snapshot = _make_history_entry(kit, changed_fields)
    kit.version += 1
    kit.last_updated = datetime.now(tz=timezone.utc)
    _save_current(storage, user_id, brand_id, kit)
    _append_history(storage, user_id, brand_id, old_kit_snapshot)
    return kit


def set_tone(
    storage, user_id: str, brand_id: str, dimension: str, value: int
) -> tuple[BrandKit, str]:
    kit = migrate_if_needed(storage, user_id, brand_id)
    dimension = dimension.lower()
    valid = {"formality", "humor", "boldness", "warmth"}
    if dimension not in valid:
        return (
            kit,
            f"Unknown tone dimension '{dimension}'. Choose from: {', '.join(sorted(valid))}.",
        )
    if not 0 <= value <= 100:
        return kit, f"Value must be 0-100. You provided {value}."
    setattr(kit.tone, dimension, value)
    kit = _commit_edit(storage, user_id, brand_id, kit, [f"tone.{dimension}"])
    return kit, f"Tone `{dimension}` set to {value}."


def add_keyword(storage, user_id: str, brand_id: str, word: str) -> tuple[BrandKit, str]:
    kit = migrate_if_needed(storage, user_id, brand_id)
    word_lower = word.strip().lower()
    existing = [k.lower() for k in kit.personality_keywords]
    if word_lower in existing:
        return kit, f"Keyword '{word}' is already in the list."
    if len(kit.personality_keywords) >= 20:
        return kit, "Maximum of 20 personality keywords reached. Remove one before adding another."
    kit.personality_keywords.append(word.strip())
    kit = _commit_edit(storage, user_id, brand_id, kit, ["personality_keywords"])
    return kit, f"Keyword '{word.strip()}' added."


def remove_keyword(storage, user_id: str, brand_id: str, word: str) -> tuple[BrandKit, str]:
    kit = migrate_if_needed(storage, user_id, brand_id)
    word_lower = word.strip().lower()
    original_len = len(kit.personality_keywords)
    kit.personality_keywords = [k for k in kit.personality_keywords if k.lower() != word_lower]
    if len(kit.personality_keywords) == original_len:
        return kit, f"Keyword '{word}' not found."
    kit = _commit_edit(storage, user_id, brand_id, kit, ["personality_keywords"])
    return kit, f"Keyword '{word.strip()}' removed."


def add_rule(
    storage, user_id: str, brand_id: str, rule_type: str, text: str
) -> tuple[BrandKit, str]:
    kit = migrate_if_needed(storage, user_id, brand_id)
    if rule_type == "do":
        if len(kit.content_rules.always_do) >= 15:
            return kit, "Maximum of 15 'always do' rules reached."
        kit.content_rules.always_do.append(text.strip())
        field = "content_rules.always_do"
    elif rule_type == "dont":
        if len(kit.content_rules.never_do) >= 15:
            return kit, "Maximum of 15 'never do' rules reached."
        kit.content_rules.never_do.append(text.strip())
        field = "content_rules.never_do"
    else:
        return kit, f"Unknown rule type '{rule_type}'. Use 'do' or 'dont'."
    kit = _commit_edit(storage, user_id, brand_id, kit, [field])
    return kit, f"Rule added to {'always do' if rule_type == 'do' else 'never do'} list."


def remove_rule(
    storage, user_id: str, brand_id: str, rule_type: str, index: int
) -> tuple[BrandKit, str]:
    kit = migrate_if_needed(storage, user_id, brand_id)
    if rule_type == "do":
        rules = kit.content_rules.always_do
        field = "content_rules.always_do"
        label = "always do"
    elif rule_type == "dont":
        rules = kit.content_rules.never_do
        field = "content_rules.never_do"
        label = "never do"
    else:
        return kit, f"Unknown rule type '{rule_type}'. Use 'do' or 'dont'."
    if index < 1 or index > len(rules):
        return kit, f"Invalid index {index}. The '{label}' list has {len(rules)} rule(s)."
    removed = rules.pop(index - 1)
    kit = _commit_edit(storage, user_id, brand_id, kit, [field])
    return kit, f"Removed '{label}' rule #{index}: \"{removed}\""


def add_reference_post(
    storage,
    user_id: str,
    brand_id: str,
    post: ReferencePost,
) -> tuple[BrandKit, str]:
    kit = migrate_if_needed(storage, user_id, brand_id)
    if len(kit.reference_posts) >= 20:
        return kit, "Maximum of 20 reference posts reached. Remove one before adding another."
    kit.reference_posts.append(post)
    kit = _commit_edit(storage, user_id, brand_id, kit, ["reference_posts"])
    return kit, f"Reference post added (ID: {post.post_id})."


def remove_reference_post(
    storage, user_id: str, brand_id: str, post_id: str
) -> tuple[BrandKit, str]:
    kit = migrate_if_needed(storage, user_id, brand_id)
    original_len = len(kit.reference_posts)
    kit.reference_posts = [p for p in kit.reference_posts if p.post_id != post_id]
    if len(kit.reference_posts) == original_len:
        return kit, f"Reference post '{post_id}' not found."
    kit = _commit_edit(storage, user_id, brand_id, kit, ["reference_posts"])
    return kit, f"Reference post '{post_id}' removed."


def reset_brandkit(storage, user_id: str, brand_id: str) -> tuple[BrandKit, str]:
    """Restore BrandKit to version 1 snapshot from history."""
    history = load_history(storage, user_id, brand_id)
    if not history:
        return (
            load_brandkit(storage, user_id, brand_id),  # type: ignore[return-value]
            "No history found — cannot reset.",
        )
    v1 = history[0]
    kit = BrandKit(**v1.snapshot)
    # Re-apply versioned fields for consistency
    kit.version = 1
    kit = _commit_edit(storage, user_id, brand_id, kit, ["reset_to_v1"])
    return kit, "BrandKit reset to version 1."


def get_brandkit_summary(kit: BrandKit) -> str:
    """Human-readable summary of the current BrandKit state."""
    tone = kit.tone
    rules_do = len(kit.content_rules.always_do)
    rules_dont = len(kit.content_rules.never_do)
    ref_count = len(kit.reference_posts)
    keywords = ", ".join(kit.personality_keywords) if kit.personality_keywords else "(none)"
    return (
        f"BRANDKIT — {kit.name} (v{kit.version})\n"
        f"{'=' * 40}\n"
        f"Tone:\n"
        f"  Formality: {tone.formality}/100\n"
        f"  Humor:     {tone.humor}/100\n"
        f"  Boldness:  {tone.boldness}/100\n"
        f"  Warmth:    {tone.warmth}/100\n\n"
        f"Personality keywords: {keywords}\n"
        f"Content rules: {rules_do} always-do, {rules_dont} never-do\n"
        f"Reference posts: {ref_count}\n\n"
        "Available commands:\n"
        "  set tone [formality|humor|boldness|warmth] [0-100]\n"
        "  add keyword [word]\n"
        "  remove keyword [word]\n"
        "  add rule do [text]\n"
        "  add rule dont [text]\n"
        "  remove rule do [index]\n"
        "  remove rule dont [index]\n"
        "  add reference post\n"
        "  remove reference post [post_id]\n"
        "  show brandkit history\n"
        "  reset brandkit"
    )


def format_history(history: list[BrandKitHistoryEntry], limit: int = 5) -> str:
    """Format the last *limit* history entries as a readable string."""
    if not history:
        return "No BrandKit history available."
    recent = history[-limit:]
    lines = [f"BRANDKIT HISTORY (last {len(recent)} entries)\n{'=' * 40}"]
    for entry in reversed(recent):
        ts = entry.timestamp.strftime("%Y-%m-%d %H:%M UTC")
        fields = ", ".join(entry.changed_fields)
        lines.append(f"  v{entry.version} | {ts} | changed: {fields}")
    return "\n".join(lines)
