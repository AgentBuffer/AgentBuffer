"""Pydantic models for the Cognition Agent orchestration layer."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ToolName(str, Enum):
    DESIGN = "generate_design_asset"
    CAROUSEL = "generate_carousel"
    VIDEO = "generate_video"


class ToolCallState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    RETRYING = "retrying"
    FALLBACK = "fallback"
    FAILED = "failed"


class AgentState(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    AGGREGATING = "aggregating"
    COMPLETE = "complete"
    ERROR = "error"


class ToolCall(BaseModel):
    """A single planned tool invocation."""

    step: int
    tool: ToolName
    slot_id: str
    reason: str = ""
    args: dict = Field(default_factory=dict)


class ExecutionPlan(BaseModel):
    """Ordered list of tool calls produced by the planning phase."""

    execution_id: str
    calls: list[ToolCall]
    parallel: bool = True


class ToolResult(BaseModel):
    """Result from a single tool execution."""

    tool: ToolName
    slot_id: str
    state: ToolCallState
    attempt: int = 1
    output: dict = Field(default_factory=dict)
    error: str | None = None


class CognitionResult(BaseModel):
    """Aggregated result from the Cognition Agent."""

    execution_id: str
    state: AgentState
    results: list[ToolResult]
    summary: str = ""
    created_at: datetime | None = None
    completed_at: datetime | None = None

    @property
    def succeeded(self) -> list[ToolResult]:
        return [r for r in self.results if r.state == ToolCallState.SUCCESS]

    @property
    def failed(self) -> list[ToolResult]:
        return [r for r in self.results if r.state == ToolCallState.FAILED]
