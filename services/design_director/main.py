"""Design Director Agent — interprets design requests and delegates to specialists."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from services.shared.models import (
    AgentEnvelope,
    DesignPlan,
    DesignRequest,
    SpecialistResult,
)

from .planner import build_plan, classify_task
from .registry import get_specialist

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("output/designs")


def handle_request(envelope: AgentEnvelope) -> AgentEnvelope:
    """Process an incoming ``design_request`` envelope end-to-end.

    Returns an ``AgentEnvelope`` with ``envelope_type="design_complete"``
    containing all specialist results.
    """
    if envelope.envelope_type != "design_request":
        raise ValueError(f"Expected envelope_type='design_request', got {envelope.envelope_type!r}")

    request = DesignRequest(**envelope.payload)

    if request.task_type is None:
        request = request.model_copy(update={"task_type": classify_task(request.task_description)})

    plan = build_plan(request)
    logger.info("Generated plan %s with %d step(s)", plan.task_id, len(plan.steps))

    _persist_plan(plan)

    results: list[SpecialistResult] = []
    for step in plan.steps:
        result = _execute_step(step, plan.task_id)
        results.append(result)
        if not result.success:
            logger.warning("Step %s failed, retrying once…", step.step_id)
            result = _execute_step(step, plan.task_id)
            results[-1] = result

    return AgentEnvelope(
        from_agent="design_director",
        to_agent=envelope.from_agent,
        envelope_type="design_complete",
        payload={
            "task_id": plan.task_id,
            "results": [r.model_dump() for r in results],
        },
        signature="",
        timestamp=datetime.now(tz=timezone.utc),
    )


def _execute_step(step, task_id: str) -> SpecialistResult:
    """Look up the specialist and run a single plan step."""
    try:
        specialist = get_specialist(step.agent)
    except KeyError:
        return SpecialistResult(
            task_id=task_id,
            step_id=step.step_id,
            agent=step.agent,
            success=False,
            error=f"No specialist registered for {step.agent!r}",
        )
    try:
        return specialist.execute(step, task_id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Specialist %s raised an error", step.agent)
        return SpecialistResult(
            task_id=task_id,
            step_id=step.step_id,
            agent=step.agent,
            success=False,
            error=str(exc),
        )


def _persist_plan(plan: DesignPlan) -> Path:
    """Write the plan to ``output/designs/<task_id>/plan.json``."""
    plan_dir = OUTPUT_DIR / plan.task_id
    plan_dir.mkdir(parents=True, exist_ok=True)
    path = plan_dir / "plan.json"
    path.write_text(json.dumps(plan.model_dump(), indent=2, default=str))
    return path
