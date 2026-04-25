"""Dynamic text wrapping and measurement utilities using Pillow."""

from __future__ import annotations

from PIL import ImageFont


def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a TrueType font, falling back to the default bitmap font."""
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Word-wrap *text* so no line exceeds *max_width* pixels."""
    if not text:
        return []
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        bbox = font.getbbox(candidate)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def measure_text_block(
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    line_spacing: int = 6,
) -> tuple[int, int]:
    """Return ``(width, height)`` of a block of wrapped lines."""
    if not lines:
        return (0, 0)
    max_w = 0
    total_h = 0
    for i, line in enumerate(lines):
        bbox = font.getbbox(line)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        max_w = max(max_w, w)
        total_h += h
        if i < len(lines) - 1:
            total_h += line_spacing
    return (max_w, total_h)


def fit_text(
    text: str,
    font_path: str,
    start_size: int,
    min_size: int,
    max_width: int,
    max_height: int,
) -> tuple[list[str], ImageFont.FreeTypeFont, int]:
    """Iteratively shrink font until *text* fits within the bounding box.

    Returns ``(lines, font, final_size)``.
    """
    size = start_size
    while size >= min_size:
        font = load_font(font_path, size)
        lines = wrap_text(text, font, max_width)
        _, block_h = measure_text_block(lines, font)
        if block_h <= max_height:
            return lines, font, size
        size -= 2
    font = load_font(font_path, min_size)
    lines = wrap_text(text, font, max_width)
    return lines, font, min_size
