"""Integration tests for the real tool wrappers.

Design and Carousel tools exercise the actual rendering pipelines (Pillow).
Video tool uses a mock VeoClient to avoid calling the real Veo API.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.shared.models import Platform, VideoRequest, VideoResult
from src.agents.tools.carousel_tool import CarouselTool
from src.agents.tools.design_tool import DesignTool
from src.agents.tools.video_tool import VideoTool

BRAND_KIT = {
    "brand_id": "brand-int-test",
    "org_id": "org-int-test",
    "name": "IntegrationCo",
    "tagline": "Integration made simple",
    "voice_description": "Professional and clear",
    "target_audience": "Developers 25-40",
    "color_palette": ["#1A1A2E", "#E94560", "#533483"],
    "logo_url": None,
    "sample_captions": ["Ship faster with IntegrationCo", "Automate everything"],
    "industry": "Technology",
}


# ---------------------------------------------------------------------------
# Design Tool — real pipeline
# ---------------------------------------------------------------------------


class TestDesignToolReal:
    @pytest.mark.asyncio()
    async def test_generates_real_png(self, tmp_path: Path) -> None:
        tool = DesignTool()
        result = await tool.execute(
            task_description="Create a marketing header for our product launch",
            brand_kit=BRAND_KIT,
            platform="linkedin",
            headline="Launch Day",
            body="We are live!",
            cta="Learn More",
        )

        assert result["success"] is True
        assert result["status"] == "success"
        assert len(result["output_paths"]) >= 1
        # The design pipeline writes to output/designs/<task_id>/
        for p in result["output_paths"]:
            assert Path(p).suffix == ".png"

    @pytest.mark.asyncio()
    async def test_auto_classifies_task_type(self) -> None:
        tool = DesignTool()
        result = await tool.execute(
            task_description="Design an infographic showing our metrics",
            brand_kit=BRAND_KIT,
            platform="instagram",
        )

        assert result["success"] is True
        assert result["task_id"].startswith("dtask-")

    @pytest.mark.asyncio()
    async def test_invalid_brand_kit_returns_error(self) -> None:
        tool = DesignTool()
        result = await tool.execute(
            task_description="Make a header",
            brand_kit={"invalid": "data"},
        )
        assert result["success"] is False
        assert result["status"] == "error"
        assert result["error"] is not None


# ---------------------------------------------------------------------------
# Carousel Tool — real pipeline
# ---------------------------------------------------------------------------


class TestCarouselToolReal:
    @pytest.mark.asyncio()
    async def test_generates_real_slides(self) -> None:
        tool = CarouselTool()
        result = await tool.execute(
            caption=(
                "5 tips for better marketing. "
                "Tip 1: Know your audience. "
                "Tip 2: Be consistent. "
                "Tip 3: Use data. "
                "Tip 4: Tell stories. "
                "Tip 5: Measure everything."
            ),
            image_prompt="Marketing tips visual",
            brand_kit=BRAND_KIT,
            platform="instagram",
            slot_id="slot-carousel-int",
        )

        assert result["status"] == "success"
        assert result["slide_count"] >= 5
        assert len(result["slide_paths"]) == result["slide_count"]
        for p in result["slide_paths"]:
            assert Path(p).exists()
            assert Path(p).suffix == ".png"
        assert Path(result["output_dir"]).is_dir()

    @pytest.mark.asyncio()
    async def test_respects_min_max_slides(self) -> None:
        tool = CarouselTool()
        result = await tool.execute(
            caption="Short caption.",
            image_prompt="Simple visual",
            brand_kit=BRAND_KIT,
            platform="linkedin",
            slot_id="slot-minmax",
            min_slides=3,
            max_slides=5,
        )

        assert result["status"] == "success"
        assert 3 <= result["slide_count"] <= 5

    @pytest.mark.asyncio()
    async def test_invalid_brand_kit_returns_error(self) -> None:
        tool = CarouselTool()
        result = await tool.execute(
            caption="Some caption",
            brand_kit={"bad": True},
            platform="instagram",
        )
        assert result["status"] == "error"
        assert result["error"] is not None


# ---------------------------------------------------------------------------
# Video Tool — mock VeoClient
# ---------------------------------------------------------------------------


def _make_mock_veo_client(
    status: str = "success",
    error: str | None = None,
) -> MagicMock:
    mock_client = MagicMock()
    mock_result = VideoResult(
        slot_id="slot-mock",
        video_url="gs://mock/video.mp4" if status == "success" else None,
        local_path="output/videos/mock.mp4" if status == "success" else None,
        platform=Platform.TIKTOK,
        duration_seconds=8,
        status=status,
        error=error,
    )
    mock_client.generate_video = AsyncMock(return_value=mock_result)
    return mock_client


class TestVideoToolReal:
    @pytest.mark.asyncio()
    async def test_calls_veo_client(self) -> None:
        mock_veo = _make_mock_veo_client()
        tool = VideoTool(veo_client=mock_veo)

        result = await tool.execute(
            caption="Amazing product reveal",
            image_prompt="A dynamic product shot with motion",
            brand_kit=BRAND_KIT,
            platform="tiktok",
            slot_id="slot-video-int",
            duration_seconds=8,
        )

        assert result["status"] == "success"
        assert result["video_url"] is not None
        assert result["slot_id"] == "slot-mock"
        mock_veo.generate_video.assert_awaited_once()

        # Verify the VideoRequest was properly constructed
        call_args = mock_veo.generate_video.call_args
        video_req: VideoRequest = call_args[0][0]
        assert video_req.platform == Platform.TIKTOK
        assert video_req.aspect_ratio == "9:16"
        assert "IntegrationCo" in video_req.brand_context

    @pytest.mark.asyncio()
    async def test_veo_error_propagated(self) -> None:
        mock_veo = _make_mock_veo_client(status="error", error="Quota exceeded")
        tool = VideoTool(veo_client=mock_veo)

        result = await tool.execute(
            caption="Another video",
            image_prompt="Visual concept",
            brand_kit=BRAND_KIT,
            platform="youtube",
            slot_id="slot-err",
        )

        assert result["status"] == "error"
        assert result["error"] == "Quota exceeded"

    @pytest.mark.asyncio()
    async def test_invalid_brand_kit_returns_error(self) -> None:
        mock_veo = _make_mock_veo_client()
        tool = VideoTool(veo_client=mock_veo)

        result = await tool.execute(
            caption="Test",
            image_prompt="Visual",
            brand_kit={"missing": "fields"},
            platform="tiktok",
        )

        assert result["status"] == "error"
        assert result["error"] is not None


# ---------------------------------------------------------------------------
# End-to-end: CognitionAgent with real tools
# ---------------------------------------------------------------------------


class TestCognitionAgentEndToEnd:
    @pytest.mark.asyncio()
    async def test_full_run_design_plus_carousel(self) -> None:
        from src.agents.cognition_agent import CognitionAgent
        from src.agents.models import AgentState, ToolCallState

        mock_veo = _make_mock_veo_client()
        agent = CognitionAgent(
            tools=[DesignTool(), CarouselTool(), VideoTool(veo_client=mock_veo)]
        )

        slots = [
            {
                "slot_id": "s-design",
                "platform": "linkedin",
                "caption": "Q4 header banner",
                "image_prompt": "Professional look",
            },
            {
                "slot_id": "s-carousel",
                "platform": "instagram",
                "caption": (
                    "5 marketing tips. "
                    "Tip one: know your audience. "
                    "Tip two: be consistent."
                ),
                "image_prompt": "Tips visual",
            },
        ]

        result = await agent.run("Execute slots", BRAND_KIT, slots=slots)

        assert result.state == AgentState.COMPLETE
        assert len(result.results) == 2
        assert all(r.state == ToolCallState.SUCCESS for r in result.results)
        assert "2/2" in result.summary
