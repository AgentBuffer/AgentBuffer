"""Unit tests for the Design Director's planner and registry."""

from __future__ import annotations

import pytest

from services.design_director.planner import build_plan, classify_task
from services.design_director.registry import get_specialist, register, registered_names
from services.shared.models import (
    BrandKit,
    DesignRequest,
    DesignTaskType,
    Platform,
)

_BRAND_KIT = BrandKit(
    brand_id="dir-brand",
    org_id="dir-org",
    name="DirCorp",
    tagline="Directing design",
    voice_description="Authoritative",
    target_audience="Marketers",
    color_palette=["#000000", "#111111", "#FF0000"],
    logo_url=None,
    sample_captions=["Sample"],
    industry="Marketing",
)

# ---------------------------------------------------------------------------
# classify_task
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("description", "expected"),
    [
        ("Design a new logo variation", DesignTaskType.LOGO_VARIATION),
        ("Create a LinkedIn header image", DesignTaskType.MARKETING_HEADER),
        ("Build an infographic about our Q3 results", DesignTaskType.INFOGRAPHIC),
        ("Rebrand our social media headers", DesignTaskType.SOCIAL_REBRAND),
        ("Something completely unrelated", DesignTaskType.MARKETING_HEADER),  # default
    ],
)
def test_classify_task(description: str, expected: DesignTaskType):
    assert classify_task(description) == expected


# ---------------------------------------------------------------------------
# build_plan
# ---------------------------------------------------------------------------


def test_build_plan_single_step():
    request = DesignRequest(
        task_description="Create a banner",
        task_type=DesignTaskType.MARKETING_HEADER,
        brand_kit=_BRAND_KIT,
        platform=Platform.LINKEDIN,
        inputs={"headline": "Hi"},
    )
    plan = build_plan(request)
    assert plan.task_id.startswith("dtask-")
    assert len(plan.steps) == 1
    assert plan.steps[0].agent == "layout"
    assert plan.steps[0].action == "render_header"
    assert plan.steps[0].params["headline"] == "Hi"


def test_build_plan_multi_step():
    request = DesignRequest(
        task_description="Rebrand everything",
        task_type=DesignTaskType.SOCIAL_REBRAND,
        brand_kit=_BRAND_KIT,
        platform=Platform.X,
    )
    plan = build_plan(request)
    assert len(plan.steps) == 2
    assert plan.steps[0].agent == "logo_maker"
    assert plan.steps[1].agent == "layout"
    assert plan.steps[1].depends_on == [plan.steps[0].step_id]


# ---------------------------------------------------------------------------
# registry
# ---------------------------------------------------------------------------


class _DummySpecialist:
    def execute(self, step, task_id):
        pass


def test_register_and_get():
    register("dummy", _DummySpecialist)
    specialist = get_specialist("dummy")
    assert isinstance(specialist, _DummySpecialist)
    assert "dummy" in registered_names()


def test_get_unregistered():
    with pytest.raises(KeyError, match="nonexistent"):
        get_specialist("nonexistent")
