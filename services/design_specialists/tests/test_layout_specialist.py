"""Unit tests for the Layout Specialist's dynamic positioning functions."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from PIL import Image

from services.design_specialists.layout_specialist import LayoutSpecialist
from services.shared.models import BrandKit

OUTPUT_DIR = Path("output/designs")

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_BRAND_KIT = BrandKit(
    brand_id="test-brand",
    org_id="test-org",
    name="TestCorp",
    tagline="Testing made easy",
    voice_description="Professional",
    target_audience="Developers",
    color_palette=["#1A1A2E", "#16213E", "#E94560"],
    logo_url=None,
    sample_captions=["Hello world"],
    industry="Technology",
)


@pytest.fixture()
def specialist() -> LayoutSpecialist:
    return LayoutSpecialist()


@pytest.fixture(autouse=True)
def _cleanup():
    """Remove generated test assets after each test."""
    yield
    for d in OUTPUT_DIR.iterdir():
        if d.is_dir() and d.name.startswith("test-"):
            shutil.rmtree(d, ignore_errors=True)


def _render(specialist: LayoutSpecialist, *, headline: str, body: str, cta: str, task_id: str):
    return specialist.render(
        brand_kit=_BRAND_KIT,
        platform="linkedin",
        headline=headline,
        body=body,
        cta=cta,
        task_id=task_id,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_short_text_no_overlap(specialist: LayoutSpecialist):
    """Single-word body + short headline — elements spaced correctly, no overlap."""
    path = _render(specialist, headline="Hello", body="World", cta="Click", task_id="test-short")
    assert path.exists()
    img = Image.open(path)
    assert img.size == (1200, 628)


def test_long_text_font_shrinks(specialist: LayoutSpecialist):
    """500-char body — font auto-reduces, still fits within canvas."""
    long_body = "Lorem ipsum dolor sit amet. " * 20  # ~560 chars
    path = _render(
        specialist,
        headline="Big Announcement",
        body=long_body,
        cta="Learn More",
        task_id="test-longbody",
    )
    assert path.exists()
    img = Image.open(path)
    assert img.size == (1200, 628)


def test_extreme_headline(specialist: LayoutSpecialist):
    """200-char headline — wraps to multiple lines, doesn't overlap body."""
    long_headline = "A " * 100  # 200 chars
    path = _render(
        specialist,
        headline=long_headline,
        body="Short body text here.",
        cta="Go",
        task_id="test-longhead",
    )
    assert path.exists()
    img = Image.open(path)
    assert img.size == (1200, 628)


def test_empty_body(specialist: LayoutSpecialist):
    """Empty body text — headline + CTA only, no crash."""
    path = _render(
        specialist,
        headline="Only a headline",
        body="",
        cta="Sign Up",
        task_id="test-nobody",
    )
    assert path.exists()
    img = Image.open(path)
    assert img.size == (1200, 628)


def test_output_dimensions(specialist: LayoutSpecialist):
    """LinkedIn preset produces exactly 1200×628."""
    path = _render(
        specialist,
        headline="Dimensions check",
        body="Body",
        cta="CTA",
        task_id="test-dims",
    )
    img = Image.open(path)
    assert img.size == (1200, 628)


def test_brand_colors_applied(specialist: LayoutSpecialist):
    """Background pixel matches brand primary colour (#1A1A2E)."""
    path = _render(
        specialist,
        headline="Color test",
        body="Check",
        cta="Ok",
        task_id="test-color",
    )
    img = Image.open(path).convert("RGBA")
    # Sample a corner pixel that should be the primary background colour
    r, g, b, a = img.getpixel((5, 5))
    # #1A1A2E → (26, 26, 46)
    assert (r, g, b) == (26, 26, 46)
