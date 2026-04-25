"""Base interface for all Cognition Agent tools."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.agents.models import ToolName


class BaseTool(ABC):
    """Abstract base class that every tool must implement."""

    @property
    @abstractmethod
    def name(self) -> ToolName:
        """Unique tool identifier matching the function-calling schema."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description surfaced in the LLM schema."""

    @property
    @abstractmethod
    def parameters_schema(self) -> dict:
        """OpenAI-compatible JSON Schema for the tool's parameters."""

    @abstractmethod
    async def execute(self, **kwargs: object) -> dict:
        """Run the tool with validated arguments and return a result dict.

        Implementations must never raise — all errors are captured in the
        returned dict as ``{"status": "error", "error": "..."}``.
        """
