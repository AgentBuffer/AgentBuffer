"""Pillow helper functions for creating and compositing design canvases."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont


def create_canvas(width: int, height: int, bg_color: str) -> Image.Image:
    """Return a new RGBA canvas filled with *bg_color*."""
    return Image.new("RGBA", (width, height), bg_color)


def place_logo(
    canvas: Image.Image,
    logo: Image.Image,
    position: str = "top-right",
    padding: int = 30,
    max_scale: float = 0.15,
) -> Image.Image:
    """Composite *logo* onto *canvas* respecting placement rules."""
    max_w = int(canvas.width * max_scale)
    ratio = max_w / logo.width if logo.width > max_w else 1.0
    new_size = (int(logo.width * ratio), int(logo.height * ratio))
    logo_resized = logo.resize(new_size, Image.LANCZOS)

    if position == "top-right":
        x = canvas.width - logo_resized.width - padding
        y = padding
    elif position == "top-left":
        x = padding
        y = padding
    else:
        x = canvas.width - logo_resized.width - padding
        y = padding

    canvas.paste(logo_resized, (x, y), logo_resized if logo_resized.mode == "RGBA" else None)
    return canvas


def draw_pill_button(
    canvas: Image.Image,
    text: str,
    font: ImageFont.FreeTypeFont,
    center_x: int,
    y: int,
    fill: str,
    text_color: str = "#FFFFFF",
    h_padding: int = 40,
    v_padding: int = 14,
) -> Image.Image:
    """Draw a pill-shaped CTA button centred at *center_x*."""
    draw = ImageDraw.Draw(canvas)
    bbox = font.getbbox(text)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    btn_w = text_w + h_padding * 2
    btn_h = text_h + v_padding * 2
    x0 = center_x - btn_w // 2
    y0 = y
    radius = btn_h // 2
    draw.rounded_rectangle(
        [(x0, y0), (x0 + btn_w, y0 + btn_h)],
        radius=radius,
        fill=fill,
    )
    text_x = x0 + h_padding
    text_y = y0 + v_padding
    draw.text((text_x, text_y), text, font=font, fill=text_color)
    return canvas
