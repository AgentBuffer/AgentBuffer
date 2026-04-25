"""Tests for the LLM planner — verifies fallback when no API key is set."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.agents.planner import llm_plan

BRAND_KIT = {
    "brand_id": "brand-test",
    "org_id": "org-test",
    "name": "PlannerCo",
    "tagline": "Plan everything",
    "voice_description": "Clear and direct",
    "target_audience": "Developers",
    "color_palette": ["#000000"],
    "logo_url": None,
    "sample_captions": ["Test"],
    "industry": "Tech",
}


class TestLLMPlanner:
    def test_returns_none_without_api_key(self) -> None:
        with patch("src.agents.planner._API_KEY", ""):
            result = llm_plan("Create a video", BRAND_KIT)
            assert result is None

    def test_returns_plan_with_valid_llm_response(self) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """[
            {
                "step": 1,
                "tool": "generate_video",
                "slot_id": "slot-001",
                "reason": "TikTok = video",
                "platform": "tiktok"
            }
        ]"""

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with (
            patch("src.agents.planner._API_KEY", "test-key"),
            patch("src.agents.planner.OpenAI", return_value=mock_client),
        ):
            result = llm_plan("Create a TikTok video", BRAND_KIT)

        assert result is not None
        assert len(result.calls) == 1
        assert result.calls[0].tool.value == "generate_video"
        assert result.calls[0].slot_id == "slot-001"

    def test_returns_none_on_empty_llm_response(self) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "[]"

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with (
            patch("src.agents.planner._API_KEY", "test-key"),
            patch("src.agents.planner.OpenAI", return_value=mock_client),
        ):
            result = llm_plan("Do something", BRAND_KIT)

        assert result is None

    def test_returns_none_on_exception(self) -> None:
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("API down")

        with (
            patch("src.agents.planner._API_KEY", "test-key"),
            patch("src.agents.planner.OpenAI", return_value=mock_client),
        ):
            result = llm_plan("Create something", BRAND_KIT)

        assert result is None

    def test_skips_unknown_tools(self) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """[
            {
                "step": 1,
                "tool": "unknown_tool",
                "slot_id": "slot-bad",
                "reason": "???",
                "platform": "tiktok"
            },
            {
                "step": 2,
                "tool": "generate_carousel",
                "slot_id": "slot-good",
                "reason": "carousel",
                "platform": "instagram"
            }
        ]"""

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with (
            patch("src.agents.planner._API_KEY", "test-key"),
            patch("src.agents.planner.OpenAI", return_value=mock_client),
        ):
            result = llm_plan("Do things", BRAND_KIT)

        assert result is not None
        assert len(result.calls) == 1
        assert result.calls[0].tool.value == "generate_carousel"

    def test_handles_slots_input(self) -> None:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """[
            {
                "step": 1,
                "tool": "generate_design_asset",
                "slot_id": "s1",
                "reason": "LinkedIn header",
                "platform": "linkedin"
            }
        ]"""

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        slots = [
            {
                "slot_id": "s1",
                "platform": "linkedin",
                "caption": "Professional content",
                "image_prompt": "Business visual",
            }
        ]

        with (
            patch("src.agents.planner._API_KEY", "test-key"),
            patch("src.agents.planner.OpenAI", return_value=mock_client),
        ):
            result = llm_plan("Execute", BRAND_KIT, slots=slots)

        assert result is not None
        assert result.calls[0].args["task_description"] == "Professional content"
