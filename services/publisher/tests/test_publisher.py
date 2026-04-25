"""Unit tests for the Publisher agent — mocked platform adapter calls."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

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


def _ok_result(slot: ContentSlot, key: str) -> PublishResult:
    return PublishResult(
        slot_id=slot.slot_id,
        platform=slot.platform,
        success=True,
        permalink=f"https://{slot.platform.value}.com/simulated/{slot.slot_id}",
        idempotency_key=key,
    )


# ---------------------------------------------------------------------------
# publish_slots — simulated mode (no credentials set)
# ---------------------------------------------------------------------------


class TestPublishSlotsSimulated:
    def test_simulated_returns_success(self):
        from services.publisher.agent import publish_slots

        slots = [_slot(), _slot(slot_id="slot-pub-2", platform=Platform.LINKEDIN)]
        results = publish_slots(slots)

        assert len(results) == 2
        for r in results:
            assert isinstance(r, PublishResult)
            assert r.success is True
            assert r.permalink is not None
            assert r.idempotency_key.startswith("pub-")

    def test_empty_slots_returns_empty(self):
        from services.publisher.agent import publish_slots

        assert publish_slots([]) == []

    def test_idempotency_keys_unique(self):
        from services.publisher.agent import publish_slots

        slots = [_slot(slot_id=f"slot-{i}") for i in range(5)]
        results = publish_slots(slots)
        keys = [r.idempotency_key for r in results]
        assert len(set(keys)) == 5


# ---------------------------------------------------------------------------
# Adapter dispatch — mocked adapters
# ---------------------------------------------------------------------------


class TestAdapterDispatch:
    @pytest.mark.asyncio
    async def test_publish_dispatches_to_correct_adapter(self):
        """Verify _publish_slot delegates to the right adapter."""
        from services.publisher.agent import _publish_slot

        slot = _slot(platform=Platform.INSTAGRAM)
        expected = _ok_result(slot, "idem-test")

        mock_adapter = AsyncMock()
        mock_adapter.publish.return_value = expected

        with patch(
            "services.publisher.agent.get_adapter",
            return_value=mock_adapter,
        ):
            result = await _publish_slot(slot, "idem-test")

        mock_adapter.publish.assert_awaited_once_with(slot, "idem-test")
        assert result.success is True
        assert result.slot_id == "slot-pub-1"

    @pytest.mark.asyncio
    async def test_publish_handles_adapter_error(self):
        """Verify adapter exceptions propagate as failed PublishResults."""
        from services.publisher.agent import _publish_slot

        slot = _slot(platform=Platform.X)
        fail_result = PublishResult(
            slot_id=slot.slot_id,
            platform=Platform.X,
            success=False,
            error="API error: 500",
            idempotency_key="idem-err",
        )

        mock_adapter = AsyncMock()
        mock_adapter.publish.return_value = fail_result

        with patch(
            "services.publisher.agent.get_adapter",
            return_value=mock_adapter,
        ):
            result = await _publish_slot(slot, "idem-err")

        assert result.success is False
        assert "500" in result.error

    @pytest.mark.asyncio
    async def test_each_platform_gets_its_own_adapter(self):
        """Verify get_adapter is called with the slot's platform."""
        from services.publisher.agent import _publish_slot

        for plat in [
            Platform.X,
            Platform.INSTAGRAM,
            Platform.LINKEDIN,
            Platform.TIKTOK,
            Platform.YOUTUBE,
        ]:
            slot = _slot(platform=plat)
            mock_adapter = AsyncMock()
            mock_adapter.publish.return_value = _ok_result(slot, "k")

            with patch(
                "services.publisher.agent.get_adapter",
                return_value=mock_adapter,
            ) as mock_get:
                await _publish_slot(slot, "k")
                mock_get.assert_called_once_with(plat)
