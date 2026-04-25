"""Layout Specialist — programmatically renders marketing assets using Pillow.

All vertical positions are computed as cumulative offsets from the top of the
safe zone.  If content overflows, font sizes are iteratively reduced until the
layout fits.  No coordinates are hardcoded.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from services.shared.models import BrandKit, PlanStep, SpecialistResult

from .common.brand_presets import PLATFORM_DIMENSIONS, BrandPreset
from .common.canvas import create_canvas, draw_pill_button, place_logo
from .common.text_layout import fit_text, load_font, measure_text_block

OUTPUT_DIR = Path("output/designs")

_MIN_FONT_SIZE = 14
_LINE_SPACING = 6
_SECTION_GAP = 20
_CTA_BOTTOM_MARGIN = 40


class LayoutSpecialist:
    """Renders marketing assets from structured text + brand context."""

    def execute(self, step: PlanStep, task_id: str) -> SpecialistResult:
        params = step.params
        brand_kit = BrandKit(**params["brand_kit"])
        platform = params.get("platform") or "linkedin"
        headline = params.get("headline", "")
        body = params.get("body", "")
        cta = params.get("cta", "")
        bg_image_path = params.get("background_image")

        try:
            out_path = self.render(
                brand_kit=brand_kit,
                platform=platform,
                headline=headline,
                body=body,
                cta=cta,
                background_image=bg_image_path,
                task_id=task_id,
            )
            return SpecialistResult(
                task_id=task_id,
                step_id=step.step_id,
                agent="layout",
                success=True,
                output_paths=[str(out_path)],
            )
        except Exception as exc:  # noqa: BLE001
            return SpecialistResult(
                task_id=task_id,
                step_id=step.step_id,
                agent="layout",
                success=False,
                error=str(exc),
            )

    def render(
        self,
        *,
        brand_kit: BrandKit,
        platform: str,
        headline: str,
        body: str,
        cta: str,
        background_image: str | None = None,
        task_id: str = "preview",
    ) -> Path:
        preset = BrandPreset.from_brand_kit(brand_kit)
        width, height = PLATFORM_DIMENSIONS.get(platform, (1200, 628))

        canvas = create_canvas(width, height, preset.primary_color)

        if background_image:
            try:
                bg = Image.open(background_image).convert("RGBA")
                bg = bg.resize((width, height), Image.LANCZOS)
                canvas = Image.alpha_composite(canvas, bg)
            except Exception:  # noqa: BLE001
                pass

        margin = preset.margin
        safe_w = width - 2 * margin
        safe_top = margin
        safe_bottom = height - margin

        cta_font = load_font(preset.body_font, preset.cta_size)
        cta_block_h = 0
        if cta:
            cta_bbox = cta_font.getbbox(cta)
            cta_text_h = cta_bbox[3] - cta_bbox[1]
            cta_block_h = cta_text_h + 28 + _CTA_BOTTOM_MARGIN

        available_h = safe_bottom - safe_top - cta_block_h - _SECTION_GAP

        headline_max_h = int(available_h * 0.4) if body else int(available_h * 0.8)
        body_max_h = available_h - headline_max_h - _SECTION_GAP if body else 0

        head_lines, head_font, _ = fit_text(
            headline,
            preset.heading_font,
            preset.heading_size,
            _MIN_FONT_SIZE,
            safe_w,
            headline_max_h,
        )
        _, head_block_h = measure_text_block(head_lines, head_font, _LINE_SPACING)

        body_lines: list[str] = []
        body_font = load_font(preset.body_font, preset.body_size)
        body_block_h = 0
        if body:
            body_lines, body_font, _ = fit_text(
                body,
                preset.body_font,
                preset.body_size,
                _MIN_FONT_SIZE,
                safe_w,
                body_max_h,
            )
            _, body_block_h = measure_text_block(body_lines, body_font, _LINE_SPACING)

        draw = ImageDraw.Draw(canvas)

        y = safe_top
        for line in head_lines:
            draw.text((margin, y), line, font=head_font, fill=preset.secondary_color)
            bbox = head_font.getbbox(line)
            y += (bbox[3] - bbox[1]) + _LINE_SPACING

        if body_lines:
            y += _SECTION_GAP
            for line in body_lines:
                draw.text((margin, y), line, font=body_font, fill="#FFFFFF")
                bbox = body_font.getbbox(line)
                y += (bbox[3] - bbox[1]) + _LINE_SPACING

        if cta:
            cta_y = safe_bottom - cta_block_h
            canvas = draw_pill_button(
                canvas,
                cta,
                cta_font,
                center_x=width // 2,
                y=cta_y,
                fill=preset.accent_color,
            )

        if brand_kit.logo_url:
            try:
                logo = Image.open(brand_kit.logo_url).convert("RGBA")
                canvas = place_logo(
                    canvas,
                    logo,
                    position=preset.logo_position,
                    padding=preset.logo_padding,
                    max_scale=preset.logo_max_scale,
                )
            except Exception:  # noqa: BLE001
                pass

        out_dir = OUTPUT_DIR / task_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "asset.png"
        canvas.save(str(out_path))
        return out_path
