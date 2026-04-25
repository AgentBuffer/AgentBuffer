"""Cognition Agent — orchestrates creative tool execution for the Main Agent.

Sits between the Main Agent and the execution pipelines (Design, Carousel,
Video).  Given a high-level directive it:

1. Plans which tools to invoke (LLM-based or deterministic fallback).
2. Executes the tools (parallel where possible).
3. Handles errors, retries, and fallbacks.
4. Aggregates and returns results.
"""

from __future__ import annotations

import asyncio
import logging
import re
import uuid
from datetime import datetime, timezone

from src.agents.models import (
    AgentState,
    CognitionResult,
    ExecutionPlan,
    ToolCall,
    ToolCallState,
    ToolName,
    ToolResult,
)
from src.agents.tools.base import BaseTool

logger = logging.getLogger(__name__)

MAX_RETRIES = 2

# Keywords used by the deterministic planner when no LLM is available.
_VIDEO_KEYWORDS = re.compile(
    r"\b(video|reel|clip|motion|animation|tiktok|youtube)\b", re.IGNORECASE
)
_CAROUSEL_KEYWORDS = re.compile(
    r"\b(carousel|slideshow|slides|swipe|multi.?slide)\b", re.IGNORECASE
)
_DESIGN_KEYWORDS = re.compile(
    r"\b(header|banner|logo|infographic|cover|thumbnail|image|poster)\b",
    re.IGNORECASE,
)

# Platforms where a specific tool is the default choice.
_PLATFORM_DEFAULTS: dict[str, ToolName] = {
    "tiktok": ToolName.VIDEO,
    "youtube": ToolName.VIDEO,
    "instagram": ToolName.CAROUSEL,
    "linkedin": ToolName.DESIGN,
    "x": ToolName.DESIGN,
}


class CognitionAgent:
    """Central orchestrator that selects and executes creative tools."""

    def __init__(self, tools: list[BaseTool] | None = None) -> None:
        self._tools: dict[ToolName, BaseTool] = {}
        for tool in tools or []:
            self._tools[tool.name] = tool
        self._state = AgentState.IDLE

    @property
    def state(self) -> AgentState:
        return self._state

    @property
    def available_tools(self) -> list[ToolName]:
        return list(self._tools.keys())

    # ------------------------------------------------------------------
    # Planning
    # ------------------------------------------------------------------

    def plan(
        self,
        prompt: str,
        brand_kit: dict,
        slots: list[dict] | None = None,
    ) -> ExecutionPlan:
        """Produce an ``ExecutionPlan`` from a high-level prompt.

        Uses deterministic heuristics for the PoC.  The full implementation
        will add an LLM-based planning path that falls back to this logic.
        """
        self._state = AgentState.PLANNING
        execution_id = f"exec-{uuid.uuid4().hex[:12]}"

        calls: list[ToolCall] = []
        if slots:
            calls = self._plan_from_slots(slots, brand_kit)
        else:
            calls = self._plan_from_prompt(prompt, brand_kit)

        plan = ExecutionPlan(
            execution_id=execution_id,
            calls=calls,
            parallel=True,
        )
        logger.info(
            "Plan %s: %d tool call(s) generated",
            execution_id,
            len(calls),
        )
        return plan

    def _plan_from_slots(
        self,
        slots: list[dict],
        brand_kit: dict,
    ) -> list[ToolCall]:
        """Map each content slot to the best tool using platform heuristics."""
        calls: list[ToolCall] = []
        for idx, slot in enumerate(slots):
            platform = slot.get("platform", "instagram")
            caption = slot.get("caption", "")
            image_prompt = slot.get("image_prompt", "")
            slot_id = slot.get("slot_id", f"slot-{idx:03d}")

            tool = self._select_tool_for_slot(platform, caption)
            args = self._build_args(tool, slot_id, caption, image_prompt, brand_kit, platform)

            calls.append(
                ToolCall(
                    step=idx + 1,
                    tool=tool,
                    slot_id=slot_id,
                    reason=f"Platform={platform} → {tool.value}",
                    args=args,
                )
            )
        return calls

    def _plan_from_prompt(
        self,
        prompt: str,
        brand_kit: dict,
    ) -> list[ToolCall]:
        """Infer tool calls from a free-form prompt string."""
        calls: list[ToolCall] = []
        slot_id = f"slot-{uuid.uuid4().hex[:8]}"

        tool = self._select_tool_from_text(prompt)
        platform = self._extract_platform(prompt)
        args = self._build_args(tool, slot_id, prompt, prompt, brand_kit, platform)

        calls.append(
            ToolCall(
                step=1,
                tool=tool,
                slot_id=slot_id,
                reason=f"Inferred from prompt keywords → {tool.value}",
                args=args,
            )
        )
        return calls

    def _select_tool_for_slot(self, platform: str, caption: str) -> ToolName:
        """Deterministic tool selection for a known slot."""
        # Explicit content-type keywords override platform defaults.
        if _VIDEO_KEYWORDS.search(caption):
            return ToolName.VIDEO
        if _CAROUSEL_KEYWORDS.search(caption):
            return ToolName.CAROUSEL
        if _DESIGN_KEYWORDS.search(caption):
            return ToolName.DESIGN

        return _PLATFORM_DEFAULTS.get(platform, ToolName.DESIGN)

    def _select_tool_from_text(self, text: str) -> ToolName:
        """Select the best tool from a free-form text prompt."""
        if _VIDEO_KEYWORDS.search(text):
            return ToolName.VIDEO
        if _CAROUSEL_KEYWORDS.search(text):
            return ToolName.CAROUSEL
        if _DESIGN_KEYWORDS.search(text):
            return ToolName.DESIGN

        # Check for platform mentions to use defaults.
        platform = self._extract_platform(text)
        return _PLATFORM_DEFAULTS.get(platform, ToolName.DESIGN)

    @staticmethod
    def _extract_platform(text: str) -> str:
        """Find the first mentioned platform in text."""
        lower = text.lower()
        for platform in ("tiktok", "youtube", "instagram", "linkedin"):
            if platform in lower:
                return platform
        if re.search(r"\btwitter\b|\b(?<!\w)x\b", lower):
            return "x"
        return "instagram"

    @staticmethod
    def _build_args(
        tool: ToolName,
        slot_id: str,
        caption: str,
        image_prompt: str,
        brand_kit: dict,
        platform: str,
    ) -> dict:
        """Construct the argument dict for a tool call."""
        if tool == ToolName.VIDEO:
            return {
                "caption": caption,
                "image_prompt": image_prompt,
                "brand_kit": brand_kit,
                "platform": platform,
                "slot_id": slot_id,
            }
        if tool == ToolName.CAROUSEL:
            return {
                "caption": caption,
                "image_prompt": image_prompt,
                "brand_kit": brand_kit,
                "platform": platform if platform in ("instagram", "linkedin") else "instagram",
                "slot_id": slot_id,
            }
        # Design
        return {
            "task_description": caption,
            "brand_kit": brand_kit,
            "platform": platform,
            "slot_id": slot_id,
        }

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    async def execute(self, plan: ExecutionPlan) -> CognitionResult:
        """Execute an ``ExecutionPlan`` and return aggregated results."""
        self._state = AgentState.EXECUTING
        created_at = datetime.now(tz=timezone.utc)

        if plan.parallel:
            results = await asyncio.gather(*(self._run_tool_call(call) for call in plan.calls))
        else:
            results = []
            for call in plan.calls:
                results.append(await self._run_tool_call(call))

        self._state = AgentState.AGGREGATING
        succeeded = sum(1 for r in results if r.state == ToolCallState.SUCCESS)
        failed = sum(1 for r in results if r.state == ToolCallState.FAILED)

        summary = f"{succeeded}/{len(results)} tools succeeded" + (
            f", {failed} failed" if failed else ""
        )

        cognition_result = CognitionResult(
            execution_id=plan.execution_id,
            state=AgentState.COMPLETE if failed == 0 else AgentState.ERROR,
            results=results,
            summary=summary,
            created_at=created_at,
            completed_at=datetime.now(tz=timezone.utc),
        )
        self._state = AgentState.COMPLETE
        return cognition_result

    async def _run_tool_call(self, call: ToolCall) -> ToolResult:
        """Execute a single tool call with retry logic."""
        tool = self._tools.get(call.tool)
        if tool is None:
            return ToolResult(
                tool=call.tool,
                slot_id=call.slot_id,
                state=ToolCallState.FAILED,
                error=f"Tool {call.tool.value!r} not registered",
            )

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                output = await tool.execute(**call.args)
            except Exception as exc:
                logger.error(
                    "Tool %s raised (attempt %d): %s",
                    call.tool.value,
                    attempt,
                    exc,
                )
                if attempt < MAX_RETRIES:
                    continue
                return ToolResult(
                    tool=call.tool,
                    slot_id=call.slot_id,
                    state=ToolCallState.FAILED,
                    attempt=attempt,
                    error=str(exc),
                )

            status = output.get("status", "success")
            if status == "success" or output.get("success") is True:
                return ToolResult(
                    tool=call.tool,
                    slot_id=call.slot_id,
                    state=ToolCallState.SUCCESS,
                    attempt=attempt,
                    output=output,
                )

            # Tool reported an error — retry if we have attempts left.
            error_msg = output.get("error", "Unknown error")
            if attempt < MAX_RETRIES:
                logger.warning(
                    "Tool %s returned error (attempt %d): %s — retrying",
                    call.tool.value,
                    attempt,
                    error_msg,
                )
                continue

            return ToolResult(
                tool=call.tool,
                slot_id=call.slot_id,
                state=ToolCallState.FAILED,
                attempt=attempt,
                output=output,
                error=error_msg,
            )

        # Should not reach here, but satisfy the type checker.
        return ToolResult(
            tool=call.tool,
            slot_id=call.slot_id,
            state=ToolCallState.FAILED,
            error="Exhausted retries",
        )

    # ------------------------------------------------------------------
    # Convenience — plan + execute in one call
    # ------------------------------------------------------------------

    async def run(
        self,
        prompt: str,
        brand_kit: dict,
        slots: list[dict] | None = None,
    ) -> CognitionResult:
        """Plan and execute in a single call."""
        plan = self.plan(prompt, brand_kit, slots=slots)
        return await self.execute(plan)
