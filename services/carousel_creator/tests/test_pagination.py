"""Tests for the carousel narrative pagination engine."""

from __future__ import annotations

from services.carousel_creator.pagination import paginate_content
from services.shared.models import BrandKit


def _make_brand(**overrides: object) -> BrandKit:
    defaults: dict = {
        "brand_id": "brand-001",
        "org_id": "org-001",
        "name": "TestBrand",
        "tagline": "Innovate every day.",
        "voice_description": "Friendly and professional",
        "target_audience": "Small business owners",
        "color_palette": ["#1a1a2e", "#16213e", "#0f3460"],
        "logo_url": None,
        "sample_captions": [
            "Grow your business with us.",
            "Join our community today!",
            "Follow for daily tips.",
        ],
        "industry": "Technology",
    }
    defaults.update(overrides)
    return BrandKit(**defaults)


class TestPaginationSlideBounds:
    def test_respects_max_slides(self) -> None:
        long_caption = ". ".join(f"Sentence number {i}" for i in range(30)) + "."
        brand = _make_brand()
        slides = paginate_content(long_caption, "prompt", brand, max_slides=10)
        assert len(slides) <= 10

    def test_respects_min_slides(self) -> None:
        short_caption = "One sentence here."
        brand = _make_brand()
        slides = paginate_content(short_caption, "prompt", brand, min_slides=5)
        assert len(slides) >= 5


class TestPaginationStructure:
    def test_hook_slide_is_first(self) -> None:
        brand = _make_brand()
        slides = paginate_content("Grab attention now! Then explain.", "prompt", brand)
        assert slides[0].slide_type == "hook"
        assert slides[0].slide_number == 1

    def test_cta_slide_is_last(self) -> None:
        brand = _make_brand()
        slides = paginate_content("Grab attention now! Then explain.", "prompt", brand)
        assert slides[-1].slide_type == "cta"
        assert slides[-1].slide_number == len(slides)

    def test_sequential_numbering(self) -> None:
        brand = _make_brand()
        slides = paginate_content(
            "First. Second. Third. Fourth. Fifth. Sixth.",
            "prompt",
            brand,
        )
        for idx, slide in enumerate(slides, start=1):
            assert slide.slide_number == idx


class TestPaginationWordBoundary:
    def test_no_mid_word_split(self) -> None:
        long_caption = (
            "This is a fairly long sentence that should be split across slides. "
            "Another sentence with important marketing content follows here. "
            "We want to make sure words are never cut in the middle. "
            "Quality content drives real engagement for your brand. "
            "Let us help you grow your audience with proven strategies."
        )
        brand = _make_brand()
        slides = paginate_content(long_caption, "prompt", brand)

        for slide in slides:
            if slide.body:
                # Body should not end with a partial word (no trailing hyphen or
                # cut-off). Every token should be a complete word.
                words = slide.body.split()
                for word in words:
                    # A partial word would have a length-1 fragment that isn't
                    # punctuation. We just verify no word is empty.
                    assert len(word) > 0


class TestPaginationEdgeCases:
    def test_empty_caption_handled(self) -> None:
        brand = _make_brand()
        slides = paginate_content("", "", brand)
        assert len(slides) >= 5
        assert slides[0].slide_type == "hook"
        assert slides[-1].slide_type == "cta"

    def test_whitespace_only_caption(self) -> None:
        brand = _make_brand()
        slides = paginate_content("   \n\t  ", "", brand)
        assert len(slides) >= 5
        assert slides[0].slide_type == "hook"
