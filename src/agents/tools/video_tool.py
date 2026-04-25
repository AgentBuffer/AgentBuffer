"""Video Tool — wraps the generative video pipeline."""

from __future__ import annotations

from src.agents.models import ToolName
from src.agents.tools.base import BaseTool


class VideoTool(BaseTool):
    """Generate platform-optimized marketing videos via Google Veo."""

    @property
    def name(self) -> ToolName:
        return ToolName.VIDEO

    @property
    def description(self) -> str:
        return (
            "Generate a platform-optimized marketing video using Google Veo. "
            "Adapts the prompt for platform-specific trends, hooks, and style. "
            "Produces MP4 files. Supports TikTok (9:16), Instagram Reels (9:16), "
            "YouTube (16:9), LinkedIn (16:9), and X (16:9). "
            "Async — may take 2-10 minutes per video."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "required": ["caption", "image_prompt", "brand_kit", "platform"],
            "properties": {
                "caption": {
                    "type": "string",
                    "description": "Marketing message for the video.",
                },
                "image_prompt": {
                    "type": "string",
                    "description": "Visual concept description.",
                },
                "brand_kit": {"type": "object", "description": "Full BrandKit object."},
                "platform": {
                    "type": "string",
                    "enum": ["linkedin", "x", "instagram", "tiktok", "youtube"],
                    "description": "Target platform.",
                },
                "slot_id": {"type": "string"},
                "duration_seconds": {"type": "integer", "default": 8},
            },
        }

    async def execute(self, **kwargs: object) -> dict:
        """Execute the video pipeline.

        In the full implementation this calls:
            services.video_creator.veo_client.VeoClient.generate_video()
            with trend-adapted prompts from services.video_creator.trends.

        For the PoC this returns a mock result.
        """
        slot_id = kwargs.get("slot_id", "slot-video-mock")
        platform = kwargs.get("platform", "tiktok")
        duration = kwargs.get("duration_seconds", 8)
        return {
            "slot_id": slot_id,
            "video_url": f"gs://mock-bucket/{platform}_{slot_id}.mp4",
            "local_path": f"output/videos/{platform}_{slot_id}.mp4",
            "platform": platform,
            "duration_seconds": duration,
            "status": "success",
            "error": None,
        }
