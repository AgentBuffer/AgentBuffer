"""Unit tests for shared Pydantic models — serialization, validation, edge cases."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from services.shared.models import (
    AgentEnvelope,
    ApprovedSlate,
    BrandKit,
    ContentSlot,
    CriticScore,
    CriticVerdict,
    DesignRequest,
    DesignTaskType,
    MarketingAnalysis,
    PlanStep,
    Platform,
    Slate,
    SpecialistResult,
    VideoRequest,
    VideoResult,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_NOW = datetime(2025, 7, 1, 12, 0, tzinfo=timezone.utc)


def _brand_kit(**overrides) -> BrandKit:
    defaults = dict(
        brand_id="b-1",
        org_id="o-1",
        name="Acme",
        tagline="We build things",
        voice_description="Friendly",
        target_audience="Developers",
        color_palette=["#000000"],
        sample_captions=["Hello"],
        industry="Tech",
    )
    defaults.update(overrides)
    return BrandKit(**defaults)


def _content_slot(**overrides) -> ContentSlot:
    defaults = dict(
        slot_id="slot-1",
        slot_number=1,
        caption="Caption",
        image_prompt="Prompt",
        platform=Platform.INSTAGRAM,
        scheduled_for=_NOW,
    )
    defaults.update(overrides)
    return ContentSlot(**defaults)


# ---------------------------------------------------------------------------
# Platform enum
# ---------------------------------------------------------------------------


class TestPlatform:
    def test_all_values(self):
        assert set(Platform) == {
            Platform.LINKEDIN,
            Platform.X,
            Platform.INSTAGRAM,
            Platform.TIKTOK,
            Platform.YOUTUBE,
        }

    def test_string_coercion(self):
        assert Platform("instagram") == Platform.INSTAGRAM


# ---------------------------------------------------------------------------
# BrandKit
# ---------------------------------------------------------------------------


class TestBrandKit:
    def test_round_trip(self):
        kit = _brand_kit()
        data = kit.model_dump()
        restored = BrandKit(**data)
        assert restored == kit

    def test_optional_logo_url(self):
        kit = _brand_kit(logo_url=None)
        assert kit.logo_url is None

    def test_empty_color_palette(self):
        kit = _brand_kit(color_palette=[])
        assert kit.color_palette == []

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            BrandKit(brand_id="b-1", org_id="o-1")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# ContentSlot
# ---------------------------------------------------------------------------


class TestContentSlot:
    def test_defaults(self):
        slot = _content_slot()
        assert slot.status == "draft"
        assert slot.image_url is None

    def test_round_trip(self):
        slot = _content_slot(image_url="https://img.example.com/1.png")
        assert ContentSlot(**slot.model_dump()) == slot


# ---------------------------------------------------------------------------
# Slate / CriticVerdict / ApprovedSlate
# ---------------------------------------------------------------------------


class TestSlateModels:
    def test_slate_round_trip(self):
        slate = Slate(
            slate_id="sl-1",
            brand_id="b-1",
            org_id="o-1",
            slots=[_content_slot()],
            generation_context="test",
        )
        assert Slate(**slate.model_dump()) == slate

    def test_critic_verdict_approved_threshold(self):
        v = CriticVerdict(
            slot_id="s-1",
            scores=[CriticScore(axis="voice", score=4.0, reasoning="ok")],
            average=4.0,
            approved=True,
            summary="good",
        )
        assert v.approved is True

    def test_approved_slate_contains_verdicts(self):
        slate = Slate(
            slate_id="sl-1",
            brand_id="b-1",
            org_id="o-1",
            slots=[_content_slot()],
            generation_context="test",
        )
        verdict = CriticVerdict(
            slot_id="slot-1",
            scores=[],
            average=4.0,
            approved=True,
            summary="ok",
        )
        approved = ApprovedSlate(slate=slate, verdicts=[verdict])
        assert len(approved.verdicts) == 1


# ---------------------------------------------------------------------------
# VideoRequest / VideoResult
# ---------------------------------------------------------------------------


class TestVideoModels:
    def test_video_request_defaults(self):
        vr = VideoRequest(
            slot_id="s-1",
            prompt="test",
            aspect_ratio="9:16",
            platform=Platform.TIKTOK,
            brand_context="ctx",
        )
        assert vr.duration_seconds == 8
        assert vr.audio_cue is None

    def test_video_result_success(self):
        r = VideoResult(
            slot_id="s-1",
            video_url="gs://bucket/v.mp4",
            platform=Platform.YOUTUBE,
            status="success",
        )
        assert r.error is None

    def test_video_result_error(self):
        r = VideoResult(
            slot_id="s-1",
            platform=Platform.X,
            status="error",
            error="timeout",
        )
        assert r.video_url is None


# ---------------------------------------------------------------------------
# Design models
# ---------------------------------------------------------------------------


class TestDesignModels:
    def test_design_task_type_enum(self):
        assert DesignTaskType("logo_variation") == DesignTaskType.LOGO_VARIATION

    def test_design_request_defaults(self):
        req = DesignRequest(
            task_description="Make a header",
            task_type=DesignTaskType.MARKETING_HEADER,
            brand_kit=_brand_kit(),
        )
        assert req.inputs == {}
        assert req.platform is None

    def test_plan_step_round_trip(self):
        step = PlanStep(
            step_id="s-0",
            agent="layout",
            action="render",
            params={"key": "value"},
        )
        assert PlanStep(**step.model_dump()) == step

    def test_specialist_result_defaults(self):
        sr = SpecialistResult(
            task_id="t-1",
            step_id="s-0",
            agent="layout",
            success=True,
        )
        assert sr.output_paths == []
        assert sr.error is None


# ---------------------------------------------------------------------------
# AgentEnvelope
# ---------------------------------------------------------------------------


class TestAgentEnvelope:
    def test_round_trip(self):
        env = AgentEnvelope(
            from_agent="a",
            to_agent="b",
            envelope_type="test",
            payload={"key": "value"},
            signature="sig",
            timestamp=_NOW,
        )
        assert AgentEnvelope(**env.model_dump()) == env


# ---------------------------------------------------------------------------
# MarketingAnalysis
# ---------------------------------------------------------------------------


class TestMarketingAnalysis:
    def test_round_trip(self):
        ma = MarketingAnalysis(
            brand_name="Acme",
            industry="Tech",
            competitive_positioning="Leader",
            key_differentiators=["speed"],
            target_audience_insights="devs",
            recommended_platforms=[Platform.LINKEDIN],
            content_themes=["innovation"],
            tone_guidelines="professional",
            weekly_cadence="7/week",
        )
        assert MarketingAnalysis(**ma.model_dump()) == ma
