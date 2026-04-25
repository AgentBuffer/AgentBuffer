"""End-to-end mock test: Main Agent Payload → Director → Plan → Layout → Image."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest
from PIL import Image

from services.design_director.main import handle_request
from services.design_director.registry import register
from services.design_specialists.layout_specialist import LayoutSpecialist
from services.shared.models import (
    AgentEnvelope,
    BrandKit,
    DesignTaskType,
)

OUTPUT_DIR = Path("output/designs")

_BRAND_KIT = BrandKit(
    brand_id="e2e-brand",
    org_id="e2e-org",
    name="E2E Corp",
    tagline="End to end testing",
    voice_description="Friendly",
    target_audience="QA Engineers",
    color_palette=["#1A1A2E", "#16213E", "#E94560"],
    logo_url=None,
    sample_captions=["Test caption"],
    industry="Testing",
)


@pytest.fixture(autouse=True)
def _register_layout():
    """Ensure the layout specialist is registered for every test."""
    register("layout", LayoutSpecialist)
    yield


@pytest.fixture(autouse=True)
def _cleanup():
    """Remove generated test assets after each test."""
    yield
    for d in OUTPUT_DIR.iterdir():
        if d.is_dir() and d.name.startswith("dtask-"):
            shutil.rmtree(d, ignore_errors=True)


def test_e2e_design_request():
    """Full pipeline: envelope → director → plan → layout specialist → image."""
    envelope = AgentEnvelope(
        from_agent="strategist",
        to_agent="design_director",
        envelope_type="design_request",
        payload={
            "task_description": "Create a LinkedIn header for our spring campaign",
            "task_type": DesignTaskType.MARKETING_HEADER.value,
            "brand_kit": _BRAND_KIT.model_dump(),
            "platform": "linkedin",
            "inputs": {
                "headline": "Spring Into Savings",
                "body": "Up to 40% off all plans this April.",
                "cta": "Start Free Trial",
            },
        },
        signature="test-sig",
        timestamp=datetime.now(tz=timezone.utc),
    )

    result_envelope = handle_request(envelope)

    # Director returns a design_complete envelope back to strategist
    assert result_envelope.envelope_type == "design_complete"
    assert result_envelope.from_agent == "design_director"
    assert result_envelope.to_agent == "strategist"

    payload = result_envelope.payload
    assert "task_id" in payload
    assert "results" in payload

    results = payload["results"]
    assert len(results) == 1

    first = results[0]
    assert first["agent"] == "layout"
    assert first["success"] is True
    assert len(first["output_paths"]) == 1

    # Verify the generated image
    img_path = Path(first["output_paths"][0])
    assert img_path.exists()
    assert img_path.stat().st_size > 0

    img = Image.open(img_path)
    assert img.size == (1200, 628)

    # Verify plan.json was persisted
    task_id = payload["task_id"]
    plan_path = OUTPUT_DIR / task_id / "plan.json"
    assert plan_path.exists()
