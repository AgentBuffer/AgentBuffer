"""Design Tool — wraps the autonomous design system pipeline."""

from __future__ import annotations

from src.agents.models import ToolName
from src.agents.tools.base import BaseTool


class DesignTool(BaseTool):
    """Generate marketing design assets via the Design Director pipeline."""

    @property
    def name(self) -> ToolName:
        return ToolName.DESIGN

    @property
    def description(self) -> str:
        return (
            "Generate marketing design assets (headers, infographics, logo "
            "variations, social rebrands) using the autonomous design system. "
            "Renders high-quality PNG images with brand styling."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "required": ["task_description", "brand_kit"],
            "properties": {
                "task_description": {
                    "type": "string",
                    "description": "Free-text description of the desired design asset.",
                },
                "task_type": {
                    "type": "string",
                    "enum": [
                        "logo_variation",
                        "marketing_header",
                        "infographic",
                        "social_rebrand",
                    ],
                    "description": "Explicit task type. Auto-classified if omitted.",
                },
                "brand_kit": {"type": "object", "description": "Full BrandKit object."},
                "platform": {
                    "type": "string",
                    "enum": ["linkedin", "x", "instagram", "tiktok", "youtube"],
                    "description": "Target platform for dimension sizing.",
                },
                "headline": {"type": "string"},
                "body": {"type": "string"},
                "cta": {"type": "string"},
            },
        }

    async def execute(self, **kwargs: object) -> dict:
        """Execute the design pipeline.

        In the full implementation this calls:
            services.design_director.main.handle_request()

        For the PoC this returns a mock result.
        """
        platform = kwargs.get("platform", "linkedin")
        return {
            "task_id": "dtask-mock-001",
            "success": True,
            "output_paths": [f"output/designs/dtask-mock-001/{platform}_asset.png"],
            "error": None,
        }
