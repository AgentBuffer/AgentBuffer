"""Unit tests for the Publisher agent — mocked Ayrshare calls."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

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
# publish_slots — simulated mode (no API key)
# ---------------------------------------------------------------------------


class TestPublishSlotsSimulated:
    @patch("services.publisher.agent.AYRSHARE_API_KEY", "")
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

    @patch("services.publisher.agent.AYRSHARE_API_KEY", "")
    def test_empty_slots_returns_empty(self):
        from services.publisher.agent import publish_slots

        assert publish_slots([]) == []

    @patch("services.publisher.agent.AYRSHARE_API_KEY", "")
    def test_idempotency_keys_unique(self):
        from services.publisher.agent import publish_slots

        slots = [_slot(slot_id=f"slot-{i}") for i in range(5)]
        results = publish_slots(slots)
        keys = [r.idempotency_key for r in results]
        assert len(set(keys)) == 5


# ---------------------------------------------------------------------------
# _publish_via_ayrshare — mocked HTTP
# ---------------------------------------------------------------------------


class TestPublishViaAyrshare:
    def test_success(self):
        mock_requests = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"postUrl": "https://instagram.com/p/abc"}
        mock_requests.post.return_value = mock_resp

        with patch.dict(sys.modules, {"requests": mock_requests}):
            from services.publisher.agent import _publish_via_ayrshare

            result = _publish_via_ayrshare(_slot(), "idem-001")
        assert result.success is True
        assert result.permalink == "https://instagram.com/p/abc"

    def test_api_error(self):
        mock_requests = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_requests.post.return_value = mock_resp

        with patch.dict(sys.modules, {"requests": mock_requests}):
            from services.publisher.agent import _publish_via_ayrshare

            result = _publish_via_ayrshare(_slot(), "idem-002")
        assert result.success is False
        assert "500" in result.error

    def test_network_exception(self):
        mock_requests = MagicMock()
        mock_requests.post.side_effect = ConnectionError("Network down")

        with patch.dict(sys.modules, {"requests": mock_requests}):
            from services.publisher.agent import _publish_via_ayrshare

            result = _publish_via_ayrshare(_slot(), "idem-003")
        assert result.success is False
        assert "Network down" in result.error

    def test_includes_media_url(self):
        mock_requests = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"postUrl": "https://example.com/p/1"}
        mock_requests.post.return_value = mock_resp

        with patch.dict(sys.modules, {"requests": mock_requests}):
            from services.publisher.agent import _publish_via_ayrshare

            slot = _slot(image_url="https://cdn.example.com/img.png")
            _publish_via_ayrshare(slot, "idem-004")

        call_kwargs = mock_requests.post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert "mediaUrls" in payload
        assert payload["mediaUrls"] == ["https://cdn.example.com/img.png"]
