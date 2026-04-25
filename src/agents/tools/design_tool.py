"""Design Tool — wraps the autonomous design system pipeline."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from services.design_director.main import handle_request as _handle_design_request
from services.design_director.registry import register, registered_names
from services.shared.models import AgentEnvelope, BrandKit, DesignRequest, DesignTaskType
from src.agents.models import ToolName
from src.agents.tools.base import BaseTool

logger = logging.getLogger(__name__)


def _ensure_specialists_registered() -> None:
    """Register the LayoutSpecialist if not already present."""
    if "layout" not in registered_names():
        from services.design_specialists.layout_specialist import LayoutSpecialist

        register("layout", LayoutSpecialist)


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
        """Execute the design pipeline via design_director.main.handle_request."""
        _ensure_specialists_registered()

        try:
            brand_kit_data = kwargs.get("brand_kit", {})
            brand_kit = (
                BrandKit(**brand_kit_data)
                if isinstance(brand_kit_data, dict)
                else brand_kit_data
            )

            task_description = str(kwargs.get("task_description", ""))
            task_type_str = kwargs.get("task_type")
            if task_type_str and isinstance(task_type_str, str):
                task_type = DesignTaskType(task_type_str)
            else:
                from services.design_director.planner import classify_task

                task_type = classify_task(task_description)

            platform_str = kwargs.get("platform")
            platform = None
            if platform_str:
                from services.shared.models import Platform

                platform = Platform(platform_str)

            inputs: dict = {}
            for key in ("headline", "body", "cta", "background_image"):
                val = kwargs.get(key)
                if val:
                    inputs[key] = val

            design_request = DesignRequest(
                task_description=task_description,
                task_type=task_type,
                brand_kit=brand_kit,
                platform=platform,
                inputs=inputs,
            )

            envelope = AgentEnvelope(
                from_agent="cognition_agent",
                to_agent="design_director",
                envelope_type="design_request",
                payload=design_request.model_dump(),
                signature="",
                timestamp=datetime.now(tz=timezone.utc),
            )

            result_envelope = _handle_design_request(envelope)
            payload = result_envelope.payload
            task_id = payload.get("task_id", "unknown")
            results = payload.get("results", [])

            all_success = all(r.get("success", False) for r in results)
            output_paths = []
            for r in results:
                output_paths.extend(r.get("output_paths", []))

            errors = [r.get("error") for r in results if r.get("error")]

            return {
                "task_id": task_id,
                "success": all_success,
                "output_paths": output_paths,
                "error": "; ".join(errors) if errors else None,
                "status": "success" if all_success else "error",
            }

        except Exception as exc:
            logger.exception("DesignTool execution failed")
            return {
                "task_id": f"dtask-err-{uuid.uuid4().hex[:8]}",
                "success": False,
                "output_paths": [],
                "error": str(exc),
                "status": "error",
            }
