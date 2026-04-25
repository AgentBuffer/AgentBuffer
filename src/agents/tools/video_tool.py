"""Video Tool — wraps the generative video pipeline."""

from __future__ import annotations

import logging
import uuid

from services.shared.models import BrandKit, ContentSlot, Platform, VideoResult
from services.video_creator.trends import adapt_prompt_for_platform, get_trends
from services.video_creator.veo_client import VeoClient
from src.agents.models import ToolName
from src.agents.tools.base import BaseTool

logger = logging.getLogger(__name__)


class VideoTool(BaseTool):
    """Generate platform-optimized marketing videos via Google Veo."""

    def __init__(self, veo_client: VeoClient | None = None) -> None:
        self._veo_client = veo_client

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
        """Execute the video pipeline via VeoClient with trend adaptation."""
        try:
            brand_kit_data = kwargs.get("brand_kit", {})
            brand_kit = (
                BrandKit(**brand_kit_data)
                if isinstance(brand_kit_data, dict)
                else brand_kit_data
            )

            caption = str(kwargs.get("caption", ""))
            image_prompt = str(kwargs.get("image_prompt", ""))
            platform_str = str(kwargs.get("platform", "tiktok"))
            slot_id = str(kwargs.get("slot_id", f"slot-{uuid.uuid4().hex[:8]}"))
            duration = int(kwargs.get("duration_seconds", 8))

            platform = Platform(platform_str)

            from datetime import datetime, timezone

            content_slot = ContentSlot(
                slot_id=slot_id,
                slot_number=1,
                caption=caption,
                image_prompt=image_prompt,
                platform=platform,
                scheduled_for=datetime.now(tz=timezone.utc),
            )

            trends = get_trends(platform)
            video_request = adapt_prompt_for_platform(content_slot, brand_kit, trends)
            video_request = video_request.model_copy(
                update={"duration_seconds": duration}
            )

            client = self._veo_client or VeoClient()
            result: VideoResult = await client.generate_video(video_request)

            return {
                "slot_id": result.slot_id,
                "video_url": result.video_url,
                "local_path": result.local_path,
                "platform": result.platform.value,
                "duration_seconds": result.duration_seconds,
                "status": result.status,
                "error": result.error,
            }

        except Exception as exc:
            logger.exception("VideoTool execution failed")
            return {
                "slot_id": str(kwargs.get("slot_id", "unknown")),
                "video_url": None,
                "local_path": None,
                "platform": str(kwargs.get("platform", "tiktok")),
                "duration_seconds": None,
                "status": "error",
                "error": str(exc),
            }
