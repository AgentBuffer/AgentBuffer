"""Tests for the carousel slide renderer."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from services.carousel_creator.renderer import SLIDE_HEIGHT, SLIDE_WIDTH, render_slide
from services.shared.models import BrandKit, SlideContent


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
        "sample_captions": ["Grow your business with us."],
        "industry": "Technology",
    }
    defaults.update(overrides)
    return BrandKit(**defaults)


def _make_slide(**overrides: object) -> SlideContent:
    defaults: dict = {
        "slide_number": 1,
        "slide_type": "hook",
        "headline": "Grab Attention Now",
        "body": "This is the body text of the slide.",
    }
    defaults.update(overrides)
    return SlideContent(**defaults)


class TestOutputDimensions:
    def test_output_dimensions_are_1080x1350(self, tmp_path: Path) -> None:
        slide = _make_slide()
        brand = _make_brand()
        output = tmp_path / "slide_01.png"
        render_slide(slide, brand, output)

        img = Image.open(output)
        assert img.size == (SLIDE_WIDTH, SLIDE_HEIGHT)
        assert img.size == (1080, 1350)


class TestOutputFileCreation:
    def test_output_file_created(self, tmp_path: Path) -> None:
        slide = _make_slide()
        brand = _make_brand()
        output = tmp_path / "slide_01.png"
        result = render_slide(slide, brand, output)

        assert result == output
        assert output.exists()
        assert output.stat().st_size > 0

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        slide = _make_slide()
        brand = _make_brand()
        output = tmp_path / "nested" / "deep" / "slide_01.png"
        render_slide(slide, brand, output)

        assert output.exists()


class TestSequentialNaming:
    def test_sequential_naming(self, tmp_path: Path) -> None:
        brand = _make_brand()
        slot_id = "slot-abc123"
        slot_dir = tmp_path / slot_id

        for i in range(1, 6):
            slide = _make_slide(slide_number=i, slide_type="body")
            filename = f"{slot_id}_slide_{i:02d}.png"
            render_slide(slide, brand, slot_dir / filename, total_slides=5)

        files = sorted(slot_dir.iterdir())
        expected = [f"{slot_id}_slide_{i:02d}.png" for i in range(1, 6)]
        assert [f.name for f in files] == expected


class TestRenderWithMissingLogo:
    def test_render_with_missing_logo(self, tmp_path: Path) -> None:
        slide = _make_slide()
        brand = _make_brand(logo_url=None)
        output = tmp_path / "slide_no_logo.png"
        render_slide(slide, brand, output)

        img = Image.open(output)
        assert img.size == (1080, 1350)

    def test_render_with_nonexistent_logo_path(self, tmp_path: Path) -> None:
        slide = _make_slide()
        brand = _make_brand(logo_url="/nonexistent/path/logo.png")
        output = tmp_path / "slide_bad_logo.png"
        render_slide(slide, brand, output)

        img = Image.open(output)
        assert img.size == (1080, 1350)
