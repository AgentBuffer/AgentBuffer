"""Unit tests for the image prompt adaptation engine."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from services.image_creator.config import IMAGE_ASPECT_RATIOS
from services.image_creator.prompt_adapter import adapt_prompt
from services.shared.models import (
    BrandKit,
    ContentSlot,
    ImageRequest,
    Platform,
)

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
def slot_instagram() -> ContentSlot:
    return ContentSlot(
        slot_id="slot-ig-001",
        slot_number=1,
        caption="Transform your workflow",
        image_prompt="Aesthetic flat-lay of productivity tools with soft pastels",
        platform=Platform.INSTAGRAM,
        scheduled_for=datetime(2025, 7, 1, 10, 0, tzinfo=timezone.utc),
    )


@pytest.fixture()
def slot_linkedin() -> ContentSlot:
    return ContentSlot(
        slot_id="slot-li-001",
        slot_number=2,
        caption="Industry insights from our CEO",
        image_prompt="Professional headshot with data visualization background",
        platform=Platform.LINKEDIN,
        scheduled_for=datetime(2025, 7, 2, 9, 0, tzinfo=timezone.utc),
    )


@pytest.fixture()
def slot_x() -> ContentSlot:
    return ContentSlot(
        slot_id="slot-x-001",
        slot_number=3,
        caption="Hot take on the latest tech trend",
        image_prompt="Bold graphic with contrasting colors and a single key stat",
        platform=Platform.X,
        scheduled_for=datetime(2025, 7, 3, 16, 0, tzinfo=timezone.utc),
    )


@pytest.fixture()
def slot_tiktok() -> ContentSlot:
    return ContentSlot(
        slot_id="slot-tt-001",
        slot_number=4,
        caption="Check out our latest gadget!",
        image_prompt="A sleek smartphone on a minimalist desk",
        platform=Platform.TIKTOK,
        scheduled_for=datetime(2025, 7, 4, 12, 0, tzinfo=timezone.utc),
    )


@pytest.fixture()
def slot_youtube() -> ContentSlot:
    return ContentSlot(
        slot_id="slot-yt-001",
        slot_number=5,
        caption="The full story behind our product line",
        image_prompt="Cinematic factory shot",
        platform=Platform.YOUTUBE,
        scheduled_for=datetime(2025, 7, 5, 14, 0, tzinfo=timezone.utc),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAdaptPrompt:
    def test_instagram_returns_correct_aspect_ratio(
        self, slot_instagram: ContentSlot, brand: BrandKit
    ) -> None:
        result = adapt_prompt(slot_instagram, brand)
        assert isinstance(result, ImageRequest)
        assert result.aspect_ratio == "4:5"
        assert result.platform == Platform.INSTAGRAM

    def test_linkedin_returns_correct_aspect_ratio(
        self, slot_linkedin: ContentSlot, brand: BrandKit
    ) -> None:
        result = adapt_prompt(slot_linkedin, brand)
        assert result.aspect_ratio == "1.91:1"
        assert result.platform == Platform.LINKEDIN

    def test_x_returns_correct_aspect_ratio(self, slot_x: ContentSlot, brand: BrandKit) -> None:
        result = adapt_prompt(slot_x, brand)
        assert result.aspect_ratio == "16:9"
        assert result.platform == Platform.X

    def test_tiktok_returns_correct_aspect_ratio(
        self, slot_tiktok: ContentSlot, brand: BrandKit
    ) -> None:
        result = adapt_prompt(slot_tiktok, brand)
        assert result.aspect_ratio == "9:16"
        assert result.platform == Platform.TIKTOK

    def test_youtube_returns_correct_aspect_ratio(
        self, slot_youtube: ContentSlot, brand: BrandKit
    ) -> None:
        result = adapt_prompt(slot_youtube, brand)
        assert result.aspect_ratio == "16:9"
        assert result.platform == Platform.YOUTUBE

    def test_prompt_contains_brand_context(
        self, slot_instagram: ContentSlot, brand: BrandKit
    ) -> None:
        result = adapt_prompt(slot_instagram, brand)
        assert brand.name in result.brand_context
        assert brand.voice_description in result.brand_context
        assert brand.target_audience in result.brand_context
        assert brand.industry in result.brand_context

    def test_prompt_includes_slot_content(
        self, slot_instagram: ContentSlot, brand: BrandKit
    ) -> None:
        result = adapt_prompt(slot_instagram, brand)
        assert (
            slot_instagram.image_prompt in result.prompt or slot_instagram.caption in result.prompt
        )

    def test_slot_id_is_preserved(self, slot_instagram: ContentSlot, brand: BrandKit) -> None:
        result = adapt_prompt(slot_instagram, brand)
        assert result.slot_id == slot_instagram.slot_id

    def test_negative_prompt_is_set(self, slot_instagram: ContentSlot, brand: BrandKit) -> None:
        result = adapt_prompt(slot_instagram, brand)
        assert result.negative_prompt != ""
        assert "watermark" in result.negative_prompt.lower()

    def test_all_platforms_produce_valid_image_request(self, brand: BrandKit) -> None:
        for platform in Platform:
            slot = ContentSlot(
                slot_id=f"slot-{platform.value}",
                slot_number=1,
                caption="Test caption",
                image_prompt="Test visual",
                platform=platform,
                scheduled_for=datetime(2025, 7, 1, tzinfo=timezone.utc),
            )
            result = adapt_prompt(slot, brand)
            assert isinstance(result, ImageRequest)
            assert result.aspect_ratio == IMAGE_ASPECT_RATIOS[platform.value]
            assert result.prompt != ""
            assert result.brand_context != ""
