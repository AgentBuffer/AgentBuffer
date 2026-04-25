"""Trend Adaptation Engine — formats content into platform-optimized video prompts.

The `get_trends` function currently returns mock trend data. Replace its
implementation with a live trend-scraping service when available.
"""

from __future__ import annotations

from services.shared.models import (
    BrandKit,
    ContentSlot,
    Platform,
    TrendContext,
    VideoRequest,
)
from services.video_creator.config import ASPECT_RATIOS, DEFAULT_DURATION_SECONDS

# ---------------------------------------------------------------------------
# Mock trend data — swap for live scraper later
# ---------------------------------------------------------------------------

_MOCK_TRENDS: dict[Platform, TrendContext] = {
    Platform.TIKTOK: TrendContext(
        platform=Platform.TIKTOK,
        trending_topics=[
            "day-in-my-life",
            "product-reveal",
            "before-and-after",
            "POV storytelling",
        ],
        style_hints=[
            "fast cuts every 1-2 seconds",
            "text overlay with bold font",
            "start with a surprising visual hook",
            "use trending transition effects",
        ],
        hook_type="pattern-interrupt",
        trending_audio_cues=[
            "upbeat lo-fi remix",
            "trending pop snippet",
            "dramatic bass drop intro",
        ],
    ),
    Platform.YOUTUBE: TrendContext(
        platform=Platform.YOUTUBE,
        trending_topics=[
            "deep-dive tutorial",
            "brand story documentary",
            "comparison review",
            "behind-the-scenes",
        ],
        style_hints=[
            "cinematic opening shot",
            "narrative arc with beginning-middle-end",
            "professional color grading",
            "branded lower-third graphics",
        ],
        hook_type="curiosity-gap",
        trending_audio_cues=[
            "ambient cinematic score",
            "uplifting corporate background music",
            "subtle sound design with whooshes",
        ],
    ),
    Platform.INSTAGRAM: TrendContext(
        platform=Platform.INSTAGRAM,
        trending_topics=[
            "aesthetic transformation",
            "mini-vlog",
            "quick tip carousel-to-reel",
            "unboxing reveal",
        ],
        style_hints=[
            "visually polished and color-coordinated",
            "smooth slow-motion moments",
            "on-screen text for silent viewing",
            "end with a clear CTA",
        ],
        hook_type="visual-hook",
        trending_audio_cues=[
            "trending reel audio clip",
            "chill acoustic background",
            "viral sound effect sequence",
        ],
    ),
    Platform.LINKEDIN: TrendContext(
        platform=Platform.LINKEDIN,
        trending_topics=[
            "thought leadership",
            "industry insight",
            "company culture spotlight",
        ],
        style_hints=[
            "professional and polished tone",
            "data-driven visuals and charts",
            "talking-head with B-roll",
        ],
        hook_type="stat-hook",
        trending_audio_cues=[
            "minimal corporate background",
            "subtle ambient music",
        ],
    ),
    Platform.X: TrendContext(
        platform=Platform.X,
        trending_topics=[
            "hot take commentary",
            "quick product demo",
            "meme-worthy moment",
        ],
        style_hints=[
            "punchy and concise under 60 seconds",
            "bold text overlays",
            "high-contrast visuals",
        ],
        hook_type="bold-statement",
        trending_audio_cues=[
            "no music or minimal background",
            "voiceover with urgency",
        ],
    ),
}


def get_trends(platform: Platform) -> TrendContext:
    """Return current trend context for a platform.

    Currently returns mock data. Replace this implementation with a live
    trend-scraping integration (e.g., TikTok Creative Center API, YouTube
    Trending API, Instagram Graph API) when available.
    """
    if platform in _MOCK_TRENDS:
        return _MOCK_TRENDS[platform]
    return _MOCK_TRENDS[Platform.INSTAGRAM]


def adapt_prompt_for_platform(
    slot: ContentSlot,
    brand: BrandKit,
    trends: TrendContext,
) -> VideoRequest:
    """Transform a ContentSlot + BrandKit + TrendContext into a Veo-ready VideoRequest."""
    platform = trends.platform
    aspect_ratio = ASPECT_RATIOS.get(platform.value, "16:9")

    brand_context = (
        f"Brand: {brand.name}. "
        f"Voice: {brand.voice_description}. "
        f"Audience: {brand.target_audience}. "
        f"Industry: {brand.industry}."
    )

    base_visual = slot.image_prompt
    caption_context = slot.caption

    if platform == Platform.TIKTOK:
        prompt = _build_tiktok_prompt(base_visual, caption_context, brand, trends)
    elif platform == Platform.YOUTUBE:
        prompt = _build_youtube_prompt(base_visual, caption_context, brand, trends)
    elif platform == Platform.INSTAGRAM:
        prompt = _build_instagram_prompt(base_visual, caption_context, brand, trends)
    elif platform == Platform.LINKEDIN:
        prompt = _build_linkedin_prompt(base_visual, caption_context, brand, trends)
    else:
        prompt = _build_default_prompt(base_visual, caption_context, brand, trends)

    audio_cue = trends.trending_audio_cues[0] if trends.trending_audio_cues else None

    return VideoRequest(
        slot_id=slot.slot_id,
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        platform=platform,
        audio_cue=audio_cue,
        brand_context=brand_context,
        duration_seconds=DEFAULT_DURATION_SECONDS,
    )


def _build_tiktok_prompt(
    visual: str,
    caption: str,
    brand: BrandKit,
    trends: TrendContext,
) -> str:
    topic = trends.trending_topics[0] if trends.trending_topics else "product showcase"
    style = "; ".join(trends.style_hints[:2]) if trends.style_hints else "fast-paced"
    return (
        f"Create a vertical 9:16 TikTok video. "
        f"Hook: Open with a {trends.hook_type} in the first 2 seconds. "
        f"Trending format: {topic}. "
        f"Visual concept: {visual}. "
        f"Message: {caption}. "
        f"Style: {style}. "
        f"Brand voice: {brand.voice_description}. "
        f"Target audience: {brand.target_audience}."
    )


def _build_youtube_prompt(
    visual: str,
    caption: str,
    brand: BrandKit,
    trends: TrendContext,
) -> str:
    topic = trends.trending_topics[0] if trends.trending_topics else "brand story"
    style = "; ".join(trends.style_hints[:2]) if trends.style_hints else "cinematic"
    return (
        f"Create a horizontal 16:9 YouTube video. "
        f"Opening: Start with a {trends.hook_type} to build curiosity. "
        f"Narrative format: {topic}. "
        f"Visual concept: {visual}. "
        f"Story: {caption}. "
        f"Begin with a branded intro for {brand.name}. "
        f"Style: {style}. "
        f"Brand voice: {brand.voice_description}. "
        f"Target audience: {brand.target_audience}."
    )


def _build_instagram_prompt(
    visual: str,
    caption: str,
    brand: BrandKit,
    trends: TrendContext,
) -> str:
    topic = trends.trending_topics[0] if trends.trending_topics else "aesthetic reveal"
    style = "; ".join(trends.style_hints[:2]) if trends.style_hints else "polished"
    return (
        f"Create a vertical 9:16 Instagram Reel. "
        f"Hook: Open with a {trends.hook_type} to stop the scroll. "
        f"Trending format: {topic}. "
        f"Visual concept: {visual}. "
        f"Caption context: {caption}. "
        f"Style: {style}. "
        f"Brand: {brand.name} — {brand.tagline}. "
        f"Target audience: {brand.target_audience}."
    )


def _build_linkedin_prompt(
    visual: str,
    caption: str,
    brand: BrandKit,
    trends: TrendContext,
) -> str:
    topic = trends.trending_topics[0] if trends.trending_topics else "industry insight"
    style = "; ".join(trends.style_hints[:2]) if trends.style_hints else "professional"
    return (
        f"Create a horizontal 16:9 LinkedIn video. "
        f"Opening: Lead with a {trends.hook_type} — a compelling data point or insight. "
        f"Format: {topic}. "
        f"Visual concept: {visual}. "
        f"Key message: {caption}. "
        f"Style: {style}. "
        f"Brand: {brand.name}, {brand.industry}. "
        f"Target audience: {brand.target_audience}."
    )


def _build_default_prompt(
    visual: str,
    caption: str,
    brand: BrandKit,
    trends: TrendContext,
) -> str:
    style = "; ".join(trends.style_hints[:2]) if trends.style_hints else "engaging"
    return (
        f"Create a promotional video. "
        f"Visual concept: {visual}. "
        f"Message: {caption}. "
        f"Style: {style}. "
        f"Brand: {brand.name} — {brand.voice_description}. "
        f"Target audience: {brand.target_audience}."
    )
