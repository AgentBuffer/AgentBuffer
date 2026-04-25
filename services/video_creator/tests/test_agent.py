"""Unit tests for video_creator/agent.py — process_approved_slate & envelope wrapping."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.shared.models import (
    ApprovedSlate,
    BrandKit,
    ContentSlot,
    CriticScore,
    CriticVerdict,
    Platform,
    Slate,
    VideoResult,
)
from services.video_creator.agent import process_approved_slate, wrap_results_as_envelope

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def brand() -> BrandKit:
    return BrandKit(
        brand_id="brand-va",
        org_id="org-va",
        name="TestBrand",
        tagline="Test",
        voice_description="Friendly",
        target_audience="Devs",
        color_palette=["#FF0000"],
        sample_captions=["Hi"],
        industry="Tech",
    )


def _make_approved_slate(platforms_and_ids: list[tuple[str, Platform, bool]]) -> ApprovedSlate:
    slots = []
    verdicts = []
    for slot_id, platform, approved in platforms_and_ids:
        slots.append(
            ContentSlot(
                slot_id=slot_id,
                slot_number=len(slots) + 1,
                caption="Caption",
                image_prompt="prompt",
                platform=platform,
                scheduled_for=datetime(2025, 7, 1, tzinfo=timezone.utc),
            )
        )
        verdicts.append(
            CriticVerdict(
                slot_id=slot_id,
                scores=[CriticScore(axis="rel", score=4.0, reasoning="ok")],
                average=4.0 if approved else 2.0,
                approved=approved,
                summary="verdict",
            )
        )
    slate = Slate(
        slate_id="slate-va",
        brand_id="brand-va",
        org_id="org-va",
        slots=slots,
        generation_context="test",
    )
    return ApprovedSlate(slate=slate, verdicts=verdicts)


def _mock_veo_client(results: dict[str, VideoResult]) -> MagicMock:
    client = MagicMock()

    async def gen(request):
        return results.get(
            request.slot_id,
            VideoResult(
                slot_id=request.slot_id,
                platform=request.platform,
                status="error",
                error="Unexpected slot",
            ),
        )

    client.generate_video = AsyncMock(side_effect=gen)
    return client


# ---------------------------------------------------------------------------
# process_approved_slate
# ---------------------------------------------------------------------------


class TestProcessApprovedSlate:
    @pytest.mark.asyncio
    async def test_only_approved_slots_processed(self, brand: BrandKit):
        slate = _make_approved_slate(
            [
                ("slot-a", Platform.TIKTOK, True),
                ("slot-b", Platform.YOUTUBE, False),
            ]
        )
        veo = _mock_veo_client(
            {
                "slot-a": VideoResult(
                    slot_id="slot-a",
                    platform=Platform.TIKTOK,
                    status="success",
                    video_url="gs://bucket/a.mp4",
                ),
            }
        )

        results = await process_approved_slate(slate, brand, veo_client=veo)
        assert len(results) == 1
        assert results[0].slot_id == "slot-a"
        assert results[0].status == "success"

    @pytest.mark.asyncio
    async def test_error_propagated_gracefully(self, brand: BrandKit):
        slate = _make_approved_slate([("slot-e", Platform.INSTAGRAM, True)])
        veo = MagicMock()
        veo.generate_video = AsyncMock(side_effect=RuntimeError("API down"))

        results = await process_approved_slate(slate, brand, veo_client=veo)
        assert len(results) == 1
        assert results[0].status == "error"
        assert "API down" in results[0].error

    @pytest.mark.asyncio
    async def test_empty_approved_returns_empty(self, brand: BrandKit):
        slate = _make_approved_slate([("slot-x", Platform.TIKTOK, False)])
        veo = _mock_veo_client({})

        results = await process_approved_slate(slate, brand, veo_client=veo)
        assert results == []


# ---------------------------------------------------------------------------
# wrap_results_as_envelope
# ---------------------------------------------------------------------------


class TestWrapResultsAsEnvelope:
    def test_envelope_structure(self):
        results = [
            VideoResult(
                slot_id="s-1",
                platform=Platform.TIKTOK,
                status="success",
                video_url="gs://bucket/v.mp4",
            ),
        ]
        env = wrap_results_as_envelope(results)
        assert env.from_agent == "video_creator"
        assert env.to_agent == "publisher"
        assert env.envelope_type == "video_results"
        assert len(env.payload["videos"]) == 1

    def test_empty_results(self):
        env = wrap_results_as_envelope([])
        assert env.payload["videos"] == []
