"""Carousel Tool — wraps the carousel generator pipeline."""

from __future__ import annotations

from src.agents.models import ToolName
from src.agents.tools.base import BaseTool


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
        """Execute the carousel pipeline.

        In the full implementation this calls:
            services.carousel_creator.agent.process_approved_slate()
            or a simplified single-slot path through pagination + renderer.

        For the PoC this returns a mock result.
        """
        slot_id = kwargs.get("slot_id", "slot-carousel-mock")
        platform = kwargs.get("platform", "instagram")
        slide_count = 7
        return {
            "slot_id": slot_id,
            "platform": platform,
            "slide_count": slide_count,
            "slide_paths": [
                f"output/carousels/{slot_id}/slide_{i:02d}.png" for i in range(1, slide_count + 1)
            ],
            "output_dir": f"output/carousels/{slot_id}",
            "status": "success",
            "error": None,
        }
