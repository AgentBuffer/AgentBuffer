"""Shared Pydantic models — source of truth for all agents and codegen."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class Platform(str, Enum):
    LINKEDIN = "linkedin"
    X = "x"
    INSTAGRAM = "instagram"


class BrandKit(BaseModel):
    brand_id: str
    org_id: str
    name: str
    tagline: str
    voice_description: str
    target_audience: str
    color_palette: list[str]
    logo_url: str | None = None
    sample_captions: list[str]
    industry: str


class ContentSlot(BaseModel):
    slot_id: str
    slot_number: int
    caption: str
    image_prompt: str
    platform: Platform
    scheduled_for: datetime
    image_url: str | None = None
    status: str = "draft"


class Slate(BaseModel):
    slate_id: str
    brand_id: str
    org_id: str
    slots: list[ContentSlot]
    generation_context: str


class CriticScore(BaseModel):
    axis: str
    score: float
    reasoning: str


class CriticVerdict(BaseModel):
    slot_id: str
    scores: list[CriticScore]
    average: float
    approved: bool
    summary: str


class ApprovedSlate(BaseModel):
    slate: Slate
    verdicts: list[CriticVerdict]


class RejectionNotice(BaseModel):
    slots: list[CriticVerdict]


class PublishResult(BaseModel):
    slot_id: str
    platform: Platform
    success: bool
    permalink: str | None = None
    error: str | None = None
    idempotency_key: str


class AgentEnvelope(BaseModel):
    from_agent: str
    to_agent: str
    envelope_type: str
    payload: dict
    signature: str
    timestamp: datetime


# ---------------------------------------------------------------------------
# Design Agent models
# ---------------------------------------------------------------------------


class DesignTaskType(str, Enum):
    LOGO_VARIATION = "logo_variation"
    MARKETING_HEADER = "marketing_header"
    INFOGRAPHIC = "infographic"
    SOCIAL_REBRAND = "social_rebrand"


class DesignRequest(BaseModel):
    task_description: str
    task_type: DesignTaskType
    brand_kit: BrandKit
    platform: Platform | None = None
    inputs: dict = {}


class PlanStep(BaseModel):
    step_id: str
    agent: str
    action: str
    params: dict
    depends_on: list[str] = []


class DesignPlan(BaseModel):
    task_id: str
    request: DesignRequest
    steps: list[PlanStep]
    execution_order: str = "sequential"


class SpecialistResult(BaseModel):
    task_id: str
    step_id: str
    agent: str
    success: bool
    output_paths: list[str] = []
    error: str | None = None
