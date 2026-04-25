"""Unit tests for carousel_creator/agent.py — process_approved_slate & envelope."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from PIL import Image

from services.carousel_creator.agent import (
    CAROUSEL_PLATFORMS,
    process_approved_slate,
    wrap_results_as_envelope,
)
from services.shared.models import (
    ApprovedSlate,
    BrandKit,
    CarouselResult,
    ContentSlot,
    CriticScore,
    CriticVerdict,
    Platform,
    Slate,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _brand(**overrides) -> BrandKit:
    defaults = dict(
        brand_id="brand-ca",
        org_id="org-ca",
        name="CarouselBrand",
        tagline="Slide into success",
        voice_description="Energetic",
        target_audience="Marketers",
        color_palette=["#1a1a2e", "#16213e", "#0f3460"],
        logo_url=None,
        sample_captions=["Follow us!", "Stay tuned!", "Join now!"],
        industry="Marketing",
    )
    defaults.update(overrides)
    return BrandKit(**defaults)


def _approved_slate(
    platforms_and_ids: list[tuple[str, Platform, bool]],
) -> ApprovedSlate:
    slots = []
    verdicts = []
    for slot_id, platform, approved in platforms_and_ids:
        slots.append(
            ContentSlot(
                slot_id=slot_id,
                slot_number=len(slots) + 1,
                caption="Great content here. Another sentence follows. And one more for depth.",
                image_prompt="colorful visual",
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
        slate_id="slate-ca",
        brand_id="brand-ca",
        org_id="org-ca",
        slots=slots,
        generation_context="test",
    )
    return ApprovedSlate(slate=slate, verdicts=verdicts)


# ---------------------------------------------------------------------------
# process_approved_slate
# ---------------------------------------------------------------------------


class TestCarouselProcessApprovedSlate:
    def test_generates_slides_for_instagram(self, tmp_path: Path):
        slate = _approved_slate([("slot-ig", Platform.INSTAGRAM, True)])
        results = process_approved_slate(slate, _brand(), output_root=tmp_path)

        assert len(results) == 1
        r = results[0]
        assert r.status == "success"
        assert r.slot_id == "slot-ig"
        assert len(r.slide_paths) >= 5
        # Verify actual images were created
        for p in r.slide_paths:
            img = Image.open(p)
            assert img.size == (1080, 1350)

    def test_skips_unapproved_slots(self, tmp_path: Path):
        slate = _approved_slate([
            ("slot-ok", Platform.INSTAGRAM, True),
            ("slot-no", Platform.INSTAGRAM, False),
        ])
        results = process_approved_slate(slate, _brand(), output_root=tmp_path)
        assert len(results) == 1
        assert results[0].slot_id == "slot-ok"

    def test_skips_non_carousel_platforms(self, tmp_path: Path):
        slate = _approved_slate([
            ("slot-tt", Platform.TIKTOK, True),
            ("slot-yt", Platform.YOUTUBE, True),
        ])
        results = process_approved_slate(slate, _brand(), output_root=tmp_path)
        assert results == []

    def test_linkedin_is_carousel_platform(self, tmp_path: Path):
        slate = _approved_slate([("slot-li", Platform.LINKEDIN, True)])
        results = process_approved_slate(slate, _brand(), output_root=tmp_path)
        assert len(results) == 1
        assert results[0].status == "success"


# ---------------------------------------------------------------------------
# wrap_results_as_envelope
# ---------------------------------------------------------------------------


class TestCarouselWrapResultsAsEnvelope:
    def test_envelope_structure(self):
        results = [
            CarouselResult(
                slot_id="s-1",
                platform=Platform.INSTAGRAM,
                slide_paths=["/tmp/s1.png"],
                output_dir="/tmp",
                status="success",
            ),
        ]
        env = wrap_results_as_envelope(results)
        assert env.from_agent == "carousel_creator"
        assert env.to_agent == "publisher"
        assert env.envelope_type == "carousel_results"
        assert len(env.payload["carousels"]) == 1

    def test_empty_results(self):
        env = wrap_results_as_envelope([])
        assert env.payload["carousels"] == []
