"""Carousel Tool — wraps the carousel generator pipeline."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from services.carousel_creator.pagination import paginate_content
from services.carousel_creator.renderer import render_slide
from services.shared.models import BrandKit
from src.agents.models import ToolName
from src.agents.tools.base import BaseTool

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_ROOT = Path("output/carousels")


class CarouselTool(BaseTool):
    """Generate multi-slide carousel images for Instagram/LinkedIn."""

    @property
    def name(self) -> ToolName:
        return ToolName.CAROUSEL

    @property
    def description(self) -> str:
        return (
            "Generate a multi-slide carousel image set (5-10 slides) for "
            "Instagram or LinkedIn. Converts marketing copy into a visual "
            "narrative: hook slide, body slides, and CTA closing slide. "
            "Each slide is 1080x1350 PNG."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "required": ["caption", "brand_kit", "platform"],
            "properties": {
                "caption": {
                    "type": "string",
                    "description": "Full marketing copy to paginate across slides.",
                },
                "image_prompt": {
                    "type": "string",
                    "description": "Visual direction for speaker-notes context.",
                },
                "brand_kit": {"type": "object", "description": "Full BrandKit object."},
                "platform": {
                    "type": "string",
                    "enum": ["instagram", "linkedin"],
                    "description": "Target platform.",
                },
                "slot_id": {"type": "string"},
                "min_slides": {"type": "integer", "default": 5},
                "max_slides": {"type": "integer", "default": 10},
            },
        }

    async def execute(self, **kwargs: object) -> dict:
        """Execute the carousel pipeline using pagination + renderer directly."""
        try:
            brand_kit_data = kwargs.get("brand_kit", {})
            brand_kit = (
                BrandKit(**brand_kit_data) if isinstance(brand_kit_data, dict) else brand_kit_data
            )

            caption = str(kwargs.get("caption", ""))
            image_prompt = str(kwargs.get("image_prompt", ""))
            platform_str = str(kwargs.get("platform", "instagram"))
            slot_id = str(kwargs.get("slot_id", f"slot-{uuid.uuid4().hex[:8]}"))
            min_slides = int(kwargs.get("min_slides", 5))
            max_slides = int(kwargs.get("max_slides", 10))

            slides = paginate_content(
                caption,
                image_prompt,
                brand_kit,
                min_slides=min_slides,
                max_slides=max_slides,
            )

            slot_dir = DEFAULT_OUTPUT_ROOT / slot_id
            slide_paths: list[str] = []

            for slide in slides:
                filename = f"{slot_id}_slide_{slide.slide_number:02d}.png"
                output_path = slot_dir / filename
                render_slide(slide, brand_kit, output_path, total_slides=len(slides))
                slide_paths.append(str(output_path))

            logger.info(
                "Generated %d carousel slides for slot %s → %s",
                len(slides),
                slot_id,
                slot_dir,
            )

            return {
                "slot_id": slot_id,
                "platform": platform_str,
                "slide_count": len(slides),
                "slide_paths": slide_paths,
                "output_dir": str(slot_dir),
                "status": "success",
                "error": None,
            }

        except Exception as exc:
            logger.exception("CarouselTool execution failed")
            return {
                "slot_id": str(kwargs.get("slot_id", "unknown")),
                "platform": str(kwargs.get("platform", "instagram")),
                "slide_count": 0,
                "slide_paths": [],
                "output_dir": "",
                "status": "error",
                "error": str(exc),
            }
