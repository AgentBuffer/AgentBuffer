"""Unit tests for the trend adaptation engine."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from services.shared.models import (
    BrandKit,
    ContentSlot,
    Platform,
    TrendContext,
    VideoRequest,
)
from services.video_creator.config import ASPECT_RATIOS
from services.video_creator.trends import adapt_prompt_for_platform, get_trends

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def brand() -> BrandKit:
    return BrandKit(
        brand_id="brand-001",
        org_id="org-001",
        name="TestBrand",
        tagline="Innovation for everyone",
        voice_description="Friendly and authoritative",
        target_audience="Tech-savvy millennials aged 25-35",
        color_palette=["#FF5733", "#33FF57"],
        logo_url="https://example.com/logo.png",
        sample_captions=["Discover the future today."],
        industry="Technology",
    )


@pytest.fixture()
def slot_tiktok() -> ContentSlot:
    return ContentSlot(
        slot_id="slot-tt-001",
        slot_number=1,
        caption="Check out our latest gadget!",
        image_prompt="A sleek smartphone on a minimalist desk with warm lighting",
        platform=Platform.TIKTOK,
        scheduled_for=datetime(2025, 7, 1, 12, 0, tzinfo=timezone.utc),
    )


@pytest.fixture()
def slot_youtube() -> ContentSlot:
    return ContentSlot(
        slot_id="slot-yt-001",
        slot_number=2,
        caption="The full story behind our new product line",
        image_prompt="Cinematic shot of a product being assembled in a modern factory",
        platform=Platform.YOUTUBE,
        scheduled_for=datetime(2025, 7, 2, 14, 0, tzinfo=timezone.utc),
    )


@pytest.fixture()
def slot_instagram() -> ContentSlot:
    return ContentSlot(
        slot_id="slot-ig-001",
        slot_number=3,
        caption="Transform your workflow",
        image_prompt="Aesthetic flat-lay of productivity tools with soft pastels",
        platform=Platform.INSTAGRAM,
        scheduled_for=datetime(2025, 7, 3, 10, 0, tzinfo=timezone.utc),
    )


@pytest.fixture()
def slot_linkedin() -> ContentSlot:
    return ContentSlot(
        slot_id="slot-li-001",
        slot_number=4,
        caption="Industry insights from our CEO",
        image_prompt="Professional headshot with data visualization background",
        platform=Platform.LINKEDIN,
        scheduled_for=datetime(2025, 7, 4, 9, 0, tzinfo=timezone.utc),
    )


@pytest.fixture()
def slot_x() -> ContentSlot:
    return ContentSlot(
        slot_id="slot-x-001",
        slot_number=5,
        caption="Hot take on the latest tech trend",
        image_prompt="Bold graphic with contrasting colors and a single key stat",
        platform=Platform.X,
        scheduled_for=datetime(2025, 7, 5, 16, 0, tzinfo=timezone.utc),
    )


# ---------------------------------------------------------------------------
# get_trends tests
# ---------------------------------------------------------------------------


class TestGetTrends:
    @pytest.mark.parametrize(
        "platform",
        [Platform.TIKTOK, Platform.YOUTUBE, Platform.INSTAGRAM, Platform.LINKEDIN, Platform.X],
    )
    def test_returns_trend_context_for_all_platforms(self, platform: Platform) -> None:
        trends = get_trends(platform)
        assert isinstance(trends, TrendContext)
        assert trends.platform == platform

    @pytest.mark.parametrize("platform", [Platform.TIKTOK, Platform.YOUTUBE, Platform.INSTAGRAM])
    def test_trends_have_nonempty_data(self, platform: Platform) -> None:
        trends = get_trends(platform)
        assert len(trends.trending_topics) > 0
        assert len(trends.style_hints) > 0
        assert len(trends.trending_audio_cues) > 0
        assert trends.hook_type != ""


# ---------------------------------------------------------------------------
# adapt_prompt_for_platform tests
# ---------------------------------------------------------------------------


class TestAdaptPromptForPlatform:
    def test_tiktok_returns_vertical_aspect_ratio(
        self, slot_tiktok: ContentSlot, brand: BrandKit
    ) -> None:
        trends = get_trends(Platform.TIKTOK)
        result = adapt_prompt_for_platform(slot_tiktok, brand, trends)
        assert isinstance(result, VideoRequest)
        assert result.aspect_ratio == "9:16"
        assert result.platform == Platform.TIKTOK

    def test_youtube_returns_horizontal_aspect_ratio(
        self, slot_youtube: ContentSlot, brand: BrandKit
    ) -> None:
        trends = get_trends(Platform.YOUTUBE)
        result = adapt_prompt_for_platform(slot_youtube, brand, trends)
        assert result.aspect_ratio == "16:9"
        assert result.platform == Platform.YOUTUBE

    def test_instagram_returns_vertical_aspect_ratio(
        self, slot_instagram: ContentSlot, brand: BrandKit
    ) -> None:
        trends = get_trends(Platform.INSTAGRAM)
        result = adapt_prompt_for_platform(slot_instagram, brand, trends)
        assert result.aspect_ratio == "9:16"
        assert result.platform == Platform.INSTAGRAM

    def test_linkedin_returns_horizontal_aspect_ratio(
        self, slot_linkedin: ContentSlot, brand: BrandKit
    ) -> None:
        trends = get_trends(Platform.LINKEDIN)
        result = adapt_prompt_for_platform(slot_linkedin, brand, trends)
        assert result.aspect_ratio == "16:9"
        assert result.platform == Platform.LINKEDIN

    def test_x_returns_horizontal_aspect_ratio(self, slot_x: ContentSlot, brand: BrandKit) -> None:
        trends = get_trends(Platform.X)
        result = adapt_prompt_for_platform(slot_x, brand, trends)
        assert result.aspect_ratio == "16:9"
        assert result.platform == Platform.X

    def test_tiktok_prompt_includes_hook(self, slot_tiktok: ContentSlot, brand: BrandKit) -> None:
        trends = get_trends(Platform.TIKTOK)
        result = adapt_prompt_for_platform(slot_tiktok, brand, trends)
        prompt_lower = result.prompt.lower()
        assert "hook" in prompt_lower or "2 second" in prompt_lower

    def test_youtube_prompt_includes_narrative(
        self, slot_youtube: ContentSlot, brand: BrandKit
    ) -> None:
        trends = get_trends(Platform.YOUTUBE)
        result = adapt_prompt_for_platform(slot_youtube, brand, trends)
        prompt_lower = result.prompt.lower()
        assert "narrative" in prompt_lower or "story" in prompt_lower or "intro" in prompt_lower

    def test_prompt_contains_brand_context(self, slot_tiktok: ContentSlot, brand: BrandKit) -> None:
        trends = get_trends(Platform.TIKTOK)
        result = adapt_prompt_for_platform(slot_tiktok, brand, trends)
        assert brand.name in result.brand_context
        assert brand.voice_description in result.brand_context
        assert brand.target_audience in result.brand_context
        assert brand.industry in result.brand_context

    def test_prompt_includes_slot_content(self, slot_tiktok: ContentSlot, brand: BrandKit) -> None:
        trends = get_trends(Platform.TIKTOK)
        result = adapt_prompt_for_platform(slot_tiktok, brand, trends)
        assert slot_tiktok.image_prompt in result.prompt or slot_tiktok.caption in result.prompt

    def test_slot_id_is_preserved(self, slot_tiktok: ContentSlot, brand: BrandKit) -> None:
        trends = get_trends(Platform.TIKTOK)
        result = adapt_prompt_for_platform(slot_tiktok, brand, trends)
        assert result.slot_id == slot_tiktok.slot_id

    def test_audio_cue_is_set(self, slot_tiktok: ContentSlot, brand: BrandKit) -> None:
        trends = get_trends(Platform.TIKTOK)
        result = adapt_prompt_for_platform(slot_tiktok, brand, trends)
        assert result.audio_cue is not None
        assert result.audio_cue in trends.trending_audio_cues

    def test_all_platforms_produce_valid_video_request(self, brand: BrandKit) -> None:
        for platform in [
            Platform.TIKTOK,
            Platform.YOUTUBE,
            Platform.INSTAGRAM,
            Platform.LINKEDIN,
            Platform.X,
        ]:
            slot = ContentSlot(
                slot_id=f"slot-{platform.value}",
                slot_number=1,
                caption="Test caption",
                image_prompt="Test visual",
                platform=platform,
                scheduled_for=datetime(2025, 7, 1, tzinfo=timezone.utc),
            )
            trends = get_trends(platform)
            result = adapt_prompt_for_platform(slot, brand, trends)
            assert isinstance(result, VideoRequest)
            assert result.aspect_ratio == ASPECT_RATIOS[platform.value]
            assert result.prompt != ""
            assert result.brand_context != ""
            assert result.duration_seconds > 0
