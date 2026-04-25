"""Prompt Adaptation — formats content into platform-optimized image prompts."""

from __future__ import annotations

from services.image_creator.config import IMAGE_ASPECT_RATIOS
from services.shared.models import BrandKit, ContentSlot, ImageRequest, Platform


def adapt_prompt(slot: ContentSlot, brand: BrandKit) -> ImageRequest:
    """Transform a ContentSlot + BrandKit into an Imagen-ready ImageRequest."""
    platform = slot.platform
    aspect_ratio = IMAGE_ASPECT_RATIOS.get(platform.value, "16:9")

    brand_context = (
        f"Brand: {brand.name}. "
        f"Voice: {brand.voice_description}. "
        f"Audience: {brand.target_audience}. "
        f"Industry: {brand.industry}."
    )

    base_visual = slot.image_prompt
    caption_context = slot.caption

    if platform == Platform.INSTAGRAM:
        prompt = _build_instagram_prompt(base_visual, caption_context, brand)
    elif platform == Platform.LINKEDIN:
        prompt = _build_linkedin_prompt(base_visual, caption_context, brand)
    elif platform == Platform.X:
        prompt = _build_x_prompt(base_visual, caption_context, brand)
    elif platform == Platform.TIKTOK:
        prompt = _build_tiktok_prompt(base_visual, caption_context, brand)
    elif platform == Platform.YOUTUBE:
        prompt = _build_youtube_prompt(base_visual, caption_context, brand)
    else:
        prompt = _build_default_prompt(base_visual, caption_context, brand)

    negative_prompt = (
        "No text, no watermarks, no logos, no words, no letters, "
        "no signatures, no blurry elements, no distorted faces"
    )

    return ImageRequest(
        slot_id=slot.slot_id,
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        platform=platform,
        brand_context=brand_context,
        negative_prompt=negative_prompt,
    )


def _build_instagram_prompt(
    visual: str,
    caption: str,
    brand: BrandKit,
) -> str:
    return (
        f"Create a stunning 3:4 vertical Instagram image. "
        f"Aesthetic, lifestyle photography style. "
        f"Visual concept: {visual}. "
        f"Context: {caption}. "
        f"Color palette inspired by warm, inviting tones. "
        f"Brand: {brand.name} — {brand.tagline}. "
        f"Target audience: {brand.target_audience}. "
        f"High-quality, editorial feel with natural lighting."
    )


def _build_linkedin_prompt(
    visual: str,
    caption: str,
    brand: BrandKit,
) -> str:
    return (
        f"Create a professional landscape image for LinkedIn. "
        f"Clean, data-driven, corporate visual style. "
        f"Visual concept: {visual}. "
        f"Key message: {caption}. "
        f"Brand: {brand.name}, {brand.industry}. "
        f"Target audience: {brand.target_audience}. "
        f"Professional color scheme, modern and polished."
    )


def _build_x_prompt(
    visual: str,
    caption: str,
    brand: BrandKit,
) -> str:
    return (
        f"Create a bold, high-contrast landscape image for X (Twitter). "
        f"Attention-grabbing, punchy visual style. "
        f"Visual concept: {visual}. "
        f"Message: {caption}. "
        f"Brand voice: {brand.voice_description}. "
        f"Target audience: {brand.target_audience}. "
        f"Vibrant colors, strong focal point, eye-catching composition."
    )


def _build_tiktok_prompt(
    visual: str,
    caption: str,
    brand: BrandKit,
) -> str:
    return (
        f"Create a vibrant vertical 9:16 image for TikTok. "
        f"Trend-aware, energetic, youthful visual style. "
        f"Visual concept: {visual}. "
        f"Context: {caption}. "
        f"Brand: {brand.name}. "
        f"Target audience: {brand.target_audience}. "
        f"Bold colors, dynamic composition, scroll-stopping appeal."
    )


def _build_youtube_prompt(
    visual: str,
    caption: str,
    brand: BrandKit,
) -> str:
    return (
        f"Create a cinematic landscape thumbnail image for YouTube. "
        f"Visual concept: {visual}. "
        f"Story context: {caption}. "
        f"Brand: {brand.name} — {brand.tagline}. "
        f"Target audience: {brand.target_audience}. "
        f"High-quality, professional photography with depth."
    )


def _build_default_prompt(
    visual: str,
    caption: str,
    brand: BrandKit,
) -> str:
    return (
        f"Create a promotional image. "
        f"Visual concept: {visual}. "
        f"Message: {caption}. "
        f"Brand: {brand.name} — {brand.voice_description}. "
        f"Target audience: {brand.target_audience}."
    )
