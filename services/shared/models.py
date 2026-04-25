"""Shared Pydantic models — source of truth for all agents and codegen."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class Platform(str, Enum):
    LINKEDIN = "linkedin"
    X = "x"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    BLUESKY = "bluesky"


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


class BrandRegistryEntry(BaseModel):
    """A single brand owned by a user."""

    brand_id: str
    brand_name: str
    created_at: datetime
    last_active: datetime


class ApprovalQueueItem(BaseModel):
    slot_id: str
    platform: Platform
    scheduled_time: datetime
    content_text: str
    video_url: str | None = None
    critic_score: float
    status: str = "pending"


class ApprovalDecision(BaseModel):
    session_id: str
    slot_id: str
    action: str  # "approve", "skip", "regenerate"


class AgentEnvelope(BaseModel):
    from_agent: str
    to_agent: str
    envelope_type: str
    payload: dict
    signature: str
    timestamp: datetime


class PerformanceRecord(BaseModel):
    post_id: str
    platform: Platform
    published_at: datetime
    content_type: str
    likes: int = 0
    shares: int = 0
    comments: int = 0
    reach: int = 0
    engagement_rate: float = 0.0


class BrandPerformanceSummary(BaseModel):
    brand_id: str
    top_formats: list[dict]
    best_times: dict
    avoid_patterns: list[str]



class TrendContext(BaseModel):
    platform: Platform
    trending_topics: list[str]
    style_hints: list[str]
    hook_type: str
    trending_audio_cues: list[str]


class VideoRequest(BaseModel):
    slot_id: str
    prompt: str
    aspect_ratio: str
    platform: Platform
    audio_cue: str | None = None
    brand_context: str
    duration_seconds: int = 8


class VideoResult(BaseModel):
    slot_id: str
    video_url: str | None = None
    local_path: str | None = None
    platform: Platform
    duration_seconds: int | None = None
    status: str
    error: str | None = None


class ImageRequest(BaseModel):
    slot_id: str
    prompt: str
    aspect_ratio: str
    platform: Platform
    style: str | None = None
    brand_context: str
    negative_prompt: str = ""


class ImageResult(BaseModel):
    slot_id: str
    image_url: str | None = None
    local_path: str | None = None
    platform: Platform
    status: str  # "success", "error"
    error: str | None = None


class MarketingAnalysis(BaseModel):
    """LLM-generated marketing analysis of a business."""

    brand_name: str
    industry: str
    competitive_positioning: str
    key_differentiators: list[str]
    target_audience_insights: str
    recommended_platforms: list[Platform]
    content_themes: list[str]
    tone_guidelines: str
    weekly_cadence: str


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
