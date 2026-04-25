"""Slide renderer — generates 1080x1350 carousel images using Pillow."""

from __future__ import annotations

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from services.shared.models import BrandKit, SlideContent

SLIDE_WIDTH = 1080
SLIDE_HEIGHT = 1350
ACCENT_BAR_HEIGHT = 80
LOGO_MAX_SIZE = 120
LOGO_MARGIN = 30

FONT_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REGULAR_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

HEADLINE_FONT_SIZE = 48
BODY_FONT_SIZE = 32
BADGE_FONT_SIZE = 24
BODY_WRAP_WIDTH = 28  # characters per line for word-wrap at 32pt


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert a hex color string (e.g. '#FF5733') to an RGB tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )


def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a TrueType font, falling back to default if not found."""
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def _load_logo(logo_url: str | None) -> Image.Image | None:
    """Load and resize a logo from a local path. Returns None on failure."""
    if not logo_url:
        return None
    try:
        logo_path = Path(logo_url)
        if not logo_path.exists():
            return None
        logo = Image.open(logo_path).convert("RGBA")
        logo.thumbnail((LOGO_MAX_SIZE, LOGO_MAX_SIZE), Image.LANCZOS)
        return logo
    except Exception:
        return None


def render_slide(
    slide: SlideContent,
    brand: BrandKit,
    output_path: Path,
    total_slides: int = 1,
) -> Path:
    """Render a single carousel slide as a 1080x1350 PNG.

    Args:
        slide: The slide content to render.
        brand: Brand kit for colors, logo, and styling.
        output_path: File path where the PNG will be saved.
        total_slides: Total number of slides (for badge display).

    Returns:
        The output_path after saving.
    """
    colors = brand.color_palette or ["#1a1a2e"]
    bg_color = _hex_to_rgb(colors[0])
    accent_color = _hex_to_rgb(colors[1]) if len(colors) > 1 else bg_color
    text_color = (255, 255, 255)

    img = Image.new("RGB", (SLIDE_WIDTH, SLIDE_HEIGHT), bg_color)
    draw = ImageDraw.Draw(img)

    # Accent bar at the top
    draw.rectangle(
        [(0, 0), (SLIDE_WIDTH, ACCENT_BAR_HEIGHT)],
        fill=accent_color,
    )

    # Logo (top-right)
    logo = _load_logo(brand.logo_url)
    if logo:
        logo_x = SLIDE_WIDTH - logo.width - LOGO_MARGIN
        logo_y = ACCENT_BAR_HEIGHT + LOGO_MARGIN
        img.paste(logo, (logo_x, logo_y), logo)

    font_bold = _load_font(FONT_BOLD_PATH, HEADLINE_FONT_SIZE)
    font_regular = _load_font(FONT_REGULAR_PATH, BODY_FONT_SIZE)
    font_badge = _load_font(FONT_REGULAR_PATH, BADGE_FONT_SIZE)

    # Headline — centered in the upper third
    if slide.headline:
        headline_wrapped = textwrap.fill(slide.headline, width=24)
        headline_bbox = draw.multiline_textbbox(
            (0, 0), headline_wrapped, font=font_bold, align="center"
        )
        headline_w = headline_bbox[2] - headline_bbox[0]
        headline_h = headline_bbox[3] - headline_bbox[1]
        headline_x = (SLIDE_WIDTH - headline_w) // 2
        headline_y = ACCENT_BAR_HEIGHT + 80 + (250 - headline_h) // 2
        draw.multiline_text(
            (headline_x, headline_y),
            headline_wrapped,
            fill=text_color,
            font=font_bold,
            align="center",
        )

    # Body text — centered in the middle
    if slide.body:
        body_wrapped = textwrap.fill(slide.body, width=BODY_WRAP_WIDTH)
        body_bbox = draw.multiline_textbbox((0, 0), body_wrapped, font=font_regular, align="center")
        body_w = body_bbox[2] - body_bbox[0]
        body_h = body_bbox[3] - body_bbox[1]
        body_x = (SLIDE_WIDTH - body_w) // 2
        body_y = (SLIDE_HEIGHT - body_h) // 2 + 50
        draw.multiline_text(
            (body_x, body_y),
            body_wrapped,
            fill=text_color,
            font=font_regular,
            align="center",
        )

    # Slide number badge — bottom-left circle
    badge_text = f"{slide.slide_number}/{total_slides}"
    badge_bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
    badge_w = badge_bbox[2] - badge_bbox[0]
    badge_h = badge_bbox[3] - badge_bbox[1]
    badge_radius = max(badge_w, badge_h) // 2 + 16
    badge_cx = 60
    badge_cy = SLIDE_HEIGHT - 60
    draw.ellipse(
        [
            (badge_cx - badge_radius, badge_cy - badge_radius),
            (badge_cx + badge_radius, badge_cy + badge_radius),
        ],
        fill=accent_color,
    )
    draw.text(
        (badge_cx - badge_w // 2, badge_cy - badge_h // 2),
        badge_text,
        fill=text_color,
        font=font_badge,
    )

    # Brand name — bottom-right
    brand_name_font = _load_font(FONT_REGULAR_PATH, 20)
    brand_bbox = draw.textbbox((0, 0), brand.name, font=brand_name_font)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text(
        (SLIDE_WIDTH - brand_w - 40, SLIDE_HEIGHT - 70),
        brand.name,
        fill=text_color,
        font=brand_name_font,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG")
    return output_path
