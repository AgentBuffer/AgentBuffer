"""Request/response models for MCP Server tools — strict Pydantic validation."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class TargetPlatform(str, Enum):
    LINKEDIN = "linkedin"
    X = "x"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"


class ContentType(str, Enum):
    VIDEO = "video"
    CAROUSEL = "carousel"
    IMAGE = "image"
    AUTO = "auto"


class CampaignRequest(BaseModel):
    """Input schema for the generate_social_campaign MCP tool."""

    product_description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description=(
            "A detailed description of the product or business to create marketing "
            "content for. Include brand name, industry, target audience, tone, and "
            "any specific marketing goals."
        ),
    )
    target_platform: TargetPlatform = Field(
        ...,
        description=(
            "The social media platform to optimize the campaign for. "
            "One of: linkedin, x, instagram, tiktok, youtube."
        ),
    )
    content_type: ContentType = Field(
        default=ContentType.AUTO,
        description=(
            "The type of content to generate. 'auto' lets the system decide "
            "based on platform best practices. Options: video, carousel, image, auto."
        ),
    )
    brand_voice: str = Field(
        default="",
        max_length=1000,
        description="Optional brand voice/tone guidance (e.g. 'professional yet approachable').",
    )
    num_posts: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Number of content pieces to generate (1-30). Defaults to a 7-day slate.",
    )


class CampaignResponse(BaseModel):
    """Output returned after campaign generation is triggered."""

    campaign_id: str = Field(
        ..., description="Unique identifier for this campaign run."
    )
    status: str = Field(
        ..., description="Current status: queued, running, completed, failed."
    )
    message: str = Field(
        ..., description="Human-readable summary of what was triggered."
    )
    platform: TargetPlatform
    num_posts: int


class CampaignStatusRequest(BaseModel):
    """Input schema for the get_campaign_status MCP tool."""

    campaign_id: str = Field(
        ...,
        min_length=1,
        description="The campaign_id returned from a previous generate_social_campaign call.",
    )


class PipelineStageStatus(BaseModel):
    """Status of an individual pipeline stage."""

    stage: str
    status: str  # pending, running, completed, failed
    detail: str = ""


class CampaignStatusResponse(BaseModel):
    """Output describing the current state of a campaign pipeline."""

    campaign_id: str
    overall_status: str = Field(
        ..., description="Overall status: queued, running, completed, failed."
    )
    stages: list[PipelineStageStatus] = Field(
        default_factory=list,
        description="Per-stage breakdown of the pipeline.",
    )
    result_summary: str = Field(
        default="",
        description="Final summary when the campaign is completed.",
    )
