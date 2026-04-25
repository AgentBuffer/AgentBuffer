"""Unit tests for the Publisher agent — direct platform API publishing."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from services.shared.models import ContentSlot, Platform, PublishResult

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _slot(**overrides) -> ContentSlot:
    defaults = dict(
        slot_id="slot-pub-1",
        slot_number=1,
        caption="Test caption",
        image_prompt="image desc",
        platform=Platform.INSTAGRAM,
        scheduled_for=datetime(2025, 7, 1, 12, 0, tzinfo=timezone.utc),
    )
    defaults.update(overrides)
    return ContentSlot(**defaults)


# ---------------------------------------------------------------------------
# publish_slots — simulated mode
# ---------------------------------------------------------------------------


class TestPublishSlotsSimulated:
    def test_simulated_returns_success(self):
        from services.publisher.agent import publish_slots

        slots = [_slot(), _slot(slot_id="slot-pub-2", platform=Platform.LINKEDIN)]
        results = asyncio.get_event_loop().run_until_complete(publish_slots(slots))

        assert len(results) == 2
        for r in results:
            assert isinstance(r, PublishResult)
            assert r.success is True
            assert r.permalink is not None
            assert r.idempotency_key.startswith("pub-")

    def test_empty_slots_returns_empty(self):
        from services.publisher.agent import publish_slots

        assert asyncio.get_event_loop().run_until_complete(publish_slots([])) == []

    def test_idempotency_keys_unique(self):
        from services.publisher.agent import publish_slots

        slots = [_slot(slot_id=f"slot-{i}") for i in range(5)]
        results = asyncio.get_event_loop().run_until_complete(publish_slots(slots))
        keys = [r.idempotency_key for r in results]
        assert len(set(keys)) == 5

    def test_platform_in_permalink(self):
        from services.publisher.agent import publish_slots

        slots = [_slot(platform=Platform.X)]
        results = asyncio.get_event_loop().run_until_complete(publish_slots(slots))
        assert "x.com" in results[0].permalink

    def test_correct_platform_returned(self):
        from services.publisher.agent import publish_slots

        slots = [_slot(platform=Platform.LINKEDIN)]
        results = asyncio.get_event_loop().run_until_complete(publish_slots(slots))
        assert results[0].platform == Platform.LINKEDIN

    def test_multiple_platforms(self):
        from services.publisher.agent import publish_slots

        slots = [
            _slot(slot_id="s1", platform=Platform.X),
            _slot(slot_id="s2", platform=Platform.INSTAGRAM),
            _slot(slot_id="s3", platform=Platform.TIKTOK),
        ]
        results = asyncio.get_event_loop().run_until_complete(publish_slots(slots))
        assert len(results) == 3
        platforms = [r.platform for r in results]
        assert Platform.X in platforms
        assert Platform.INSTAGRAM in platforms
        assert Platform.TIKTOK in platforms
