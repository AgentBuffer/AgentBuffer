"""Unit tests for design_director/main.py — handle_request, _execute_step."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from services.design_director.main import handle_request
from services.design_director.registry import register
from services.shared.models import (
    AgentEnvelope,
    BrandKit,
    DesignTaskType,
    PlanStep,
    SpecialistResult,
)

_BRAND_KIT = BrandKit(
    brand_id="main-brand",
    org_id="main-org",
    name="MainCorp",
    tagline="Testing main",
    voice_description="Professional",
    target_audience="Engineers",
    color_palette=["#000000", "#111111", "#FF0000"],
    logo_url=None,
    sample_captions=["Test"],
    industry="Engineering",
)


def _make_envelope(**overrides) -> AgentEnvelope:
    defaults = dict(
        from_agent="test_sender",
        to_agent="design_director",
        envelope_type="design_request",
        payload={
            "task_description": "Create a LinkedIn header",
            "task_type": DesignTaskType.MARKETING_HEADER.value,
            "brand_kit": _BRAND_KIT.model_dump(),
            "platform": "linkedin",
            "inputs": {"headline": "Test", "body": "Body", "cta": "CTA"},
        },
        signature="sig",
        timestamp=datetime.now(tz=timezone.utc),
    )
    defaults.update(overrides)
    return AgentEnvelope(**defaults)


# ---------------------------------------------------------------------------
# handle_request
# ---------------------------------------------------------------------------


class TestHandleRequest:
    def test_wrong_envelope_type_raises(self):
        envelope = _make_envelope(envelope_type="wrong_type")
        with pytest.raises(ValueError, match="Expected envelope_type='design_request'"):
            handle_request(envelope)

    def test_returns_design_complete_envelope(self):
        class MockLayout:
            def execute(self, step: PlanStep, task_id: str) -> SpecialistResult:
                return SpecialistResult(
                    task_id=task_id,
                    step_id=step.step_id,
                    agent="layout",
                    success=True,
                    output_paths=["/tmp/test_asset.png"],
                )

        register("layout", MockLayout)

        envelope = _make_envelope()
        result = handle_request(envelope)

        assert result.envelope_type == "design_complete"
        assert result.from_agent == "design_director"
        assert result.to_agent == "test_sender"
        assert "task_id" in result.payload
        assert result.payload["results"][0]["success"] is True

    def test_specialist_failure_triggers_retry(self):
        call_count = 0

        class FailOnceLayout:
            def execute(self, step: PlanStep, task_id: str) -> SpecialistResult:
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return SpecialistResult(
                        task_id=task_id,
                        step_id=step.step_id,
                        agent="layout",
                        success=False,
                        error="Transient failure",
                    )
                return SpecialistResult(
                    task_id=task_id,
                    step_id=step.step_id,
                    agent="layout",
                    success=True,
                    output_paths=["/tmp/retry_asset.png"],
                )

        register("layout", FailOnceLayout)

        envelope = _make_envelope()
        result = handle_request(envelope)

        assert call_count == 2
        assert result.payload["results"][0]["success"] is True

    def test_unregistered_specialist_handled(self):
        class StubLayout:
            def execute(self, step, task_id):
                return SpecialistResult(
                    task_id=task_id,
                    step_id=step.step_id,
                    agent="layout",
                    success=True,
                    output_paths=["/tmp/stub.png"],
                )

        # Register layout but NOT "logo_maker"
        register("layout", StubLayout)

        envelope = _make_envelope(
            payload={
                "task_description": "Rebrand everything",
                "task_type": DesignTaskType.SOCIAL_REBRAND.value,
                "brand_kit": _BRAND_KIT.model_dump(),
                "platform": "linkedin",
                "inputs": {},
            },
        )
        result = handle_request(envelope)
        results = result.payload["results"]
        # First step (logo_maker) should fail — not registered
        assert results[0]["success"] is False
        assert "No specialist registered" in results[0]["error"]
        # Second step (layout) should succeed
        assert results[1]["success"] is True
