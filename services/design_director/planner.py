"""Task classification and plan generation for the Design Director."""

from __future__ import annotations

import re
import uuid

from services.shared.models import (
    DesignPlan,
    DesignRequest,
    DesignTaskType,
    PlanStep,
)

_TASK_KEYWORDS: dict[DesignTaskType, list[str]] = {
    DesignTaskType.LOGO_VARIATION: ["logo", "icon", "mark", "emblem", "symbol"],
    DesignTaskType.MARKETING_HEADER: [
        "header",
        "banner",
        "cover",
        "thumbnail",
        "hero",
    ],
    DesignTaskType.INFOGRAPHIC: ["infographic", "data visual", "chart", "diagram"],
    DesignTaskType.SOCIAL_REBRAND: ["rebrand", "refresh", "redesign", "overhaul"],
}

_TASK_TO_STEPS: dict[DesignTaskType, list[tuple[str, str]]] = {
    DesignTaskType.LOGO_VARIATION: [("logo_maker", "generate_logo")],
    DesignTaskType.MARKETING_HEADER: [("layout", "render_header")],
    DesignTaskType.INFOGRAPHIC: [("layout", "render_infographic")],
    DesignTaskType.SOCIAL_REBRAND: [
        ("logo_maker", "generate_logo"),
        ("layout", "render_header"),
    ],
}


def classify_task(description: str) -> DesignTaskType:
    """Match a free-text description to the best ``DesignTaskType``."""
    lower = description.lower()
    scores: dict[DesignTaskType, int] = {}
    for task_type, keywords in _TASK_KEYWORDS.items():
        scores[task_type] = sum(
            1 for kw in keywords if re.search(rf"\b{re.escape(kw)}\b", lower)
        )
    best = max(scores, key=lambda t: scores[t])
    if scores[best] == 0:
        return DesignTaskType.MARKETING_HEADER
    return best


def build_plan(request: DesignRequest) -> DesignPlan:
    """Decompose a ``DesignRequest`` into an ordered ``DesignPlan``."""
    task_id = f"dtask-{uuid.uuid4().hex[:12]}"
    agent_actions = _TASK_TO_STEPS[request.task_type]

    steps: list[PlanStep] = []
    prev_id: str | None = None
    for idx, (agent, action) in enumerate(agent_actions):
        step_id = f"step-{idx:03d}"
        steps.append(
            PlanStep(
                step_id=step_id,
                agent=agent,
                action=action,
                params={
                    "brand_kit": request.brand_kit.model_dump(),
                    "platform": request.platform.value if request.platform else None,
                    **request.inputs,
                },
                depends_on=[prev_id] if prev_id else [],
            )
        )
        prev_id = step_id

    execution_order = "sequential" if len(steps) > 1 else "sequential"
    return DesignPlan(
        task_id=task_id,
        request=request,
        steps=steps,
        execution_order=execution_order,
    )
