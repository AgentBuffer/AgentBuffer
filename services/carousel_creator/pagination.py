"""Narrative pagination — splits marketing content into a carousel slide sequence."""

from __future__ import annotations

import re

from services.shared.models import BrandKit, SlideContent

MAX_BODY_CHARS = 120
DEFAULT_MIN_SLIDES = 5
DEFAULT_MAX_SLIDES = 10

DEFAULT_CTA_HEADLINE = "Let's Connect"
DEFAULT_CTA_BODY = "Follow for more insights. DM us to get started!"


def _split_sentences(text: str) -> list[str]:
    """Split text on sentence boundaries (.!?) while preserving delimiters."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _word_wrap_chunks(text: str, max_chars: int = MAX_BODY_CHARS) -> list[str]:
    """Break text into chunks of at most *max_chars* without splitting mid-word."""
    words = text.split()
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for word in words:
        added_len = len(word) + (1 if current else 0)
        if current_len + added_len > max_chars and current:
            chunks.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += added_len

    if current:
        chunks.append(" ".join(current))

    return chunks


def paginate_content(
    caption: str,
    image_prompt: str,
    brand: BrandKit,
    *,
    min_slides: int = DEFAULT_MIN_SLIDES,
    max_slides: int = DEFAULT_MAX_SLIDES,
) -> list[SlideContent]:
    """Convert a marketing message into a 5-to-10 slide carousel sequence.

    Slide structure:
      - Slide 1: Hook (attention-grabbing headline)
      - Slides 2…N-1: Core value / educational content
      - Slide N: Call to action

    Args:
        caption: The full caption text from the ContentSlot.
        image_prompt: Supplementary image prompt (used for speaker notes context).
        brand: The BrandKit for fallback content.
        min_slides: Minimum number of slides (default 5).
        max_slides: Maximum number of slides (default 10).

    Returns:
        An ordered list of SlideContent objects.
    """
    sentences = _split_sentences(caption) if caption.strip() else []

    # --- Hook slide (always slide 1) ---
    if sentences:
        hook_text = sentences[0]
        remaining_sentences = sentences[1:]
    else:
        hook_text = brand.tagline or brand.name
        remaining_sentences = []

    slides: list[SlideContent] = [
        SlideContent(
            slide_number=1,
            slide_type="hook",
            headline=hook_text,
            body="",
            speaker_notes=image_prompt,
        ),
    ]

    # --- Body slides ---
    body_text = " ".join(remaining_sentences)
    if body_text:
        chunks = _word_wrap_chunks(body_text, MAX_BODY_CHARS)
    else:
        chunks = []

    for chunk in chunks:
        slides.append(
            SlideContent(
                slide_number=len(slides) + 1,
                slide_type="body",
                headline="",
                body=chunk,
            ),
        )

    # Pad with brand-derived filler if below min_slides (reserve 1 slot for CTA)
    filler_sources = [brand.tagline] + brand.sample_captions
    filler_idx = 0
    while len(slides) < min_slides - 1 and filler_idx < len(filler_sources):
        slides.append(
            SlideContent(
                slide_number=len(slides) + 1,
                slide_type="body",
                headline="",
                body=filler_sources[filler_idx],
            ),
        )
        filler_idx += 1

    # If still too few, repeat brand tagline
    while len(slides) < min_slides - 1:
        slides.append(
            SlideContent(
                slide_number=len(slides) + 1,
                slide_type="body",
                headline="",
                body=brand.tagline,
            ),
        )

    # Trim body slides to leave room for CTA within max_slides
    if len(slides) >= max_slides:
        slides = slides[: max_slides - 1]

    # --- CTA slide (always last) ---
    cta_body = brand.sample_captions[-1] if brand.sample_captions else DEFAULT_CTA_BODY
    slides.append(
        SlideContent(
            slide_number=len(slides) + 1,
            slide_type="cta",
            headline=DEFAULT_CTA_HEADLINE,
            body=cta_body,
        ),
    )

    # Re-number slides sequentially
    for idx, slide in enumerate(slides, start=1):
        slide.slide_number = idx

    return slides
