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


class SlideContent(BaseModel):
    slide_number: int
    slide_type: str  # "hook", "body", "cta"
    headline: str
    body: str
    speaker_notes: str = ""


class CarouselResult(BaseModel):
    slot_id: str
    platform: Platform
    slide_paths: list[str]
    output_dir: str
    status: str  # "success", "error"
    error: str | None = None


class AgentEnvelope(BaseModel):
    from_agent: str
    to_agent: str
    envelope_type: str
    payload: dict
    signature: str
    timestamp: datetime
