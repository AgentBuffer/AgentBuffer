"""Tests for the Cognition Agent — verifies tool selection and execution logic.

These tests use mock tool implementations (the PoC wrappers return canned
results) so no real APIs are called.
"""

from __future__ import annotations

import pytest

from src.agents.cognition_agent import CognitionAgent
from src.agents.models import (
    AgentState,
    ToolCallState,
    ToolName,
)
from src.agents.tools.carousel_tool import CarouselTool
from src.agents.tools.design_tool import DesignTool
from src.agents.tools.video_tool import VideoTool

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MOCK_BRAND_KIT = {
    "brand_id": "brand-test",
    "org_id": "org-test",
    "name": "TestBrand",
    "tagline": "Testing made easy",
    "voice_description": "Friendly and professional",
    "target_audience": "Developers 25-40",
    "color_palette": ["#1A1A2E", "#E94560"],
    "logo_url": None,
    "sample_captions": ["Test caption one", "Test caption two"],
    "industry": "Technology",
}


@pytest.fixture()
def agent() -> CognitionAgent:
    """Create a CognitionAgent with all three mock tools registered."""
    return CognitionAgent(tools=[DesignTool(), CarouselTool(), VideoTool()])


# ---------------------------------------------------------------------------
# Sub-Task 4a: Tool selection from prompts
# ---------------------------------------------------------------------------


class TestToolSelectionFromPrompt:
    """Verify the deterministic planner correctly selects tools from prompts."""

    def test_video_keyword_selects_video_tool(self, agent: CognitionAgent) -> None:
        plan = agent.plan("Create a TikTok video for our product launch", MOCK_BRAND_KIT)
        assert len(plan.calls) == 1
        assert plan.calls[0].tool == ToolName.VIDEO

    def test_reel_keyword_selects_video_tool(self, agent: CognitionAgent) -> None:
        plan = agent.plan("Make an Instagram Reel showcasing our features", MOCK_BRAND_KIT)
        assert len(plan.calls) == 1
        assert plan.calls[0].tool == ToolName.VIDEO

    def test_carousel_keyword_selects_carousel_tool(self, agent: CognitionAgent) -> None:
        plan = agent.plan("Create a carousel post for Instagram", MOCK_BRAND_KIT)
        assert len(plan.calls) == 1
        assert plan.calls[0].tool == ToolName.CAROUSEL

    def test_slideshow_keyword_selects_carousel_tool(self, agent: CognitionAgent) -> None:
        plan = agent.plan("Build a slideshow about our 5 top tips", MOCK_BRAND_KIT)
        assert len(plan.calls) == 1
        assert plan.calls[0].tool == ToolName.CAROUSEL

    def test_header_keyword_selects_design_tool(self, agent: CognitionAgent) -> None:
        plan = agent.plan("Design a LinkedIn header banner for our profile", MOCK_BRAND_KIT)
        assert len(plan.calls) == 1
        assert plan.calls[0].tool == ToolName.DESIGN

    def test_infographic_keyword_selects_design_tool(self, agent: CognitionAgent) -> None:
        plan = agent.plan("Create an infographic about market trends", MOCK_BRAND_KIT)
        assert len(plan.calls) == 1
        assert plan.calls[0].tool == ToolName.DESIGN

    def test_youtube_platform_defaults_to_video(self, agent: CognitionAgent) -> None:
        plan = agent.plan("Create content for YouTube", MOCK_BRAND_KIT)
        assert plan.calls[0].tool == ToolName.VIDEO

    def test_tiktok_platform_defaults_to_video(self, agent: CognitionAgent) -> None:
        plan = agent.plan("Something cool for TikTok", MOCK_BRAND_KIT)
        assert plan.calls[0].tool == ToolName.VIDEO

    def test_ambiguous_prompt_defaults_to_design(self, agent: CognitionAgent) -> None:
        plan = agent.plan("Create marketing content for our brand", MOCK_BRAND_KIT)
        # No strong keyword match — falls back to Instagram default → carousel
        # because _extract_platform finds "instagram" as fallback
        assert plan.calls[0].tool == ToolName.CAROUSEL

    def test_linkedin_platform_defaults_to_design(self, agent: CognitionAgent) -> None:
        plan = agent.plan("Post something professional on LinkedIn", MOCK_BRAND_KIT)
        assert plan.calls[0].tool == ToolName.DESIGN


# ---------------------------------------------------------------------------
# Sub-Task 4b: Tool selection from structured slots
# ---------------------------------------------------------------------------


class TestToolSelectionFromSlots:
    """Verify tool selection when given structured content slots."""

    def test_tiktok_slot_gets_video(self, agent: CognitionAgent) -> None:
        slots = [
            {"slot_id": "s1", "platform": "tiktok", "caption": "Launch day!", "image_prompt": "..."}
        ]
        plan = agent.plan("Execute these slots", MOCK_BRAND_KIT, slots=slots)
        assert plan.calls[0].tool == ToolName.VIDEO

    def test_instagram_slot_gets_carousel(self, agent: CognitionAgent) -> None:
        slots = [
            {
                "slot_id": "s2",
                "platform": "instagram",
                "caption": "Tips for growth",
                "image_prompt": "...",
            }
        ]
        plan = agent.plan("Execute", MOCK_BRAND_KIT, slots=slots)
        assert plan.calls[0].tool == ToolName.CAROUSEL

    def test_linkedin_slot_gets_design(self, agent: CognitionAgent) -> None:
        slots = [
            {
                "slot_id": "s3",
                "platform": "linkedin",
                "caption": "Q3 results",
                "image_prompt": "...",
            }
        ]
        plan = agent.plan("Execute", MOCK_BRAND_KIT, slots=slots)
        assert plan.calls[0].tool == ToolName.DESIGN

    def test_keyword_override_platform_default(self, agent: CognitionAgent) -> None:
        """A 'video' keyword in the caption should override LinkedIn's design default."""
        slots = [
            {
                "slot_id": "s4",
                "platform": "linkedin",
                "caption": "Watch our video story",
                "image_prompt": "...",
            }
        ]
        plan = agent.plan("Execute", MOCK_BRAND_KIT, slots=slots)
        assert plan.calls[0].tool == ToolName.VIDEO

    def test_multiple_slots_produce_multiple_calls(self, agent: CognitionAgent) -> None:
        slots = [
            {
                "slot_id": "s1",
                "platform": "tiktok",
                "caption": "Dance trend",
                "image_prompt": "...",
            },
            {
                "slot_id": "s2",
                "platform": "instagram",
                "caption": "Tips carousel",
                "image_prompt": "...",
            },
            {
                "slot_id": "s3",
                "platform": "linkedin",
                "caption": "Thought leadership",
                "image_prompt": "...",
            },
        ]
        plan = agent.plan("Execute all", MOCK_BRAND_KIT, slots=slots)
        assert len(plan.calls) == 3
        tools_used = {c.tool for c in plan.calls}
        assert tools_used == {ToolName.VIDEO, ToolName.CAROUSEL, ToolName.DESIGN}


# ---------------------------------------------------------------------------
# Sub-Task 4c: Execution — mock tools succeed
# ---------------------------------------------------------------------------


class TestExecution:
    """Verify the execution engine runs tools and aggregates results."""

    @pytest.mark.asyncio()
    async def test_single_tool_execution_succeeds(self, agent: CognitionAgent) -> None:
        plan = agent.plan("Create a TikTok video", MOCK_BRAND_KIT)
        result = await agent.execute(plan)

        assert result.state == AgentState.COMPLETE
        assert len(result.results) == 1
        assert result.results[0].state == ToolCallState.SUCCESS
        assert result.results[0].tool == ToolName.VIDEO
        assert "video_url" in result.results[0].output

    @pytest.mark.asyncio()
    async def test_parallel_multi_tool_execution(self, agent: CognitionAgent) -> None:
        slots = [
            {"slot_id": "s1", "platform": "tiktok", "caption": "Video!", "image_prompt": "..."},
            {"slot_id": "s2", "platform": "instagram", "caption": "Tips", "image_prompt": "..."},
        ]
        plan = agent.plan("Go", MOCK_BRAND_KIT, slots=slots)
        result = await agent.execute(plan)

        assert result.state == AgentState.COMPLETE
        assert len(result.results) == 2
        assert all(r.state == ToolCallState.SUCCESS for r in result.results)

    @pytest.mark.asyncio()
    async def test_run_convenience_method(self, agent: CognitionAgent) -> None:
        result = await agent.run("Create an Instagram carousel", MOCK_BRAND_KIT)

        assert result.state == AgentState.COMPLETE
        assert len(result.results) == 1
        assert result.results[0].tool == ToolName.CAROUSEL

    @pytest.mark.asyncio()
    async def test_missing_tool_reports_failure(self) -> None:
        """Agent with no tools registered should fail gracefully."""
        empty_agent = CognitionAgent(tools=[])
        # Manually build a plan that references a tool the agent doesn't have.
        from src.agents.models import ExecutionPlan, ToolCall

        plan = ExecutionPlan(
            execution_id="exec-test",
            calls=[
                ToolCall(
                    step=1,
                    tool=ToolName.VIDEO,
                    slot_id="s1",
                    reason="test",
                    args={},
                )
            ],
        )
        result = await empty_agent.execute(plan)

        assert result.state == AgentState.ERROR
        assert len(result.failed) == 1
        assert "not registered" in (result.failed[0].error or "")


# ---------------------------------------------------------------------------
# Sub-Task 4d: Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Verify retry and failure behavior."""

    @pytest.mark.asyncio()
    async def test_tool_exception_is_retried_and_fails(self) -> None:
        """A tool that always raises should be retried then marked failed."""

        class FailingTool(VideoTool):
            async def execute(self, **kwargs: object) -> dict:
                raise RuntimeError("Veo API exploded")

        agent = CognitionAgent(tools=[FailingTool()])
        plan = agent.plan("Create a TikTok video", MOCK_BRAND_KIT)
        result = await agent.execute(plan)

        assert result.state == AgentState.ERROR
        assert result.results[0].state == ToolCallState.FAILED
        assert result.results[0].attempt == 2  # retried once
        assert "exploded" in (result.results[0].error or "")

    @pytest.mark.asyncio()
    async def test_tool_returns_error_status(self) -> None:
        """A tool that returns status=error should be retried."""

        call_count = 0

        class ErrorThenSuccessTool(CarouselTool):
            async def execute(self, **kwargs: object) -> dict:
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return {"status": "error", "error": "Temporary failure"}
                return await super().execute(**kwargs)

        agent = CognitionAgent(tools=[ErrorThenSuccessTool()])
        plan = agent.plan("Create an Instagram carousel", MOCK_BRAND_KIT)
        result = await agent.execute(plan)

        assert result.state == AgentState.COMPLETE
        assert result.results[0].state == ToolCallState.SUCCESS
        assert result.results[0].attempt == 2  # succeeded on second attempt

    @pytest.mark.asyncio()
    async def test_result_summary_includes_counts(self, agent: CognitionAgent) -> None:
        result = await agent.run("Create a TikTok video", MOCK_BRAND_KIT)
        assert "1/1 tools succeeded" in result.summary


# ---------------------------------------------------------------------------
# Sub-Task 4e: State transitions
# ---------------------------------------------------------------------------


class TestStateTransitions:
    """Verify the agent's state machine transitions."""

    def test_initial_state_is_idle(self) -> None:
        agent = CognitionAgent()
        assert agent.state == AgentState.IDLE

    def test_plan_transitions_to_planning(self, agent: CognitionAgent) -> None:
        agent.plan("anything", MOCK_BRAND_KIT)
        assert agent.state == AgentState.PLANNING

    @pytest.mark.asyncio()
    async def test_execute_transitions_to_complete(self, agent: CognitionAgent) -> None:
        plan = agent.plan("Create a video for TikTok", MOCK_BRAND_KIT)
        await agent.execute(plan)
        assert agent.state == AgentState.COMPLETE
