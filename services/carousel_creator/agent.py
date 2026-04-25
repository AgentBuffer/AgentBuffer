"""Carousel Creator sub-agent — receives ApprovedSlates and generates carousel images.

This agent sits between the Critic and Publisher in the pipeline. It:
1. Receives an ApprovedSlate with critic-approved ContentSlots
2. Filters for Instagram and LinkedIn slots (carousel-appropriate platforms)
3. Paginates each slot's caption into a multi-slide narrative
4. Renders each slide as a 1080x1350 PNG image
5. Returns CarouselResults for the Publisher to upload
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from services.carousel_creator.pagination import paginate_content
from services.carousel_creator.renderer import render_slide
from services.shared.models import (
    AgentEnvelope,
    ApprovedSlate,
    BrandKit,
    CarouselResult,
    Platform,
)

logger = logging.getLogger(__name__)

CAROUSEL_PLATFORMS = {Platform.INSTAGRAM, Platform.LINKEDIN}
DEFAULT_OUTPUT_ROOT = Path("output/carousels")


def process_approved_slate(
    slate: ApprovedSlate,
    brand: BrandKit,
    output_root: Path | None = None,
) -> list[CarouselResult]:
    """Generate carousel images for all approved slots in a slate.

    Args:
        slate: The critic-approved slate containing content slots.
        brand: The brand kit for styling and fallback content.
        output_root: Root directory for carousel output (default: output/carousels/).

    Returns:
        A list of CarouselResult objects — one per processed slot.
    """
    root = output_root or DEFAULT_OUTPUT_ROOT
    approved_slot_ids = {v.slot_id for v in slate.verdicts if v.approved}

    results: list[CarouselResult] = []
    for slot in slate.slate.slots:
        if slot.slot_id not in approved_slot_ids:
            logger.info("Skipping unapproved slot %s", slot.slot_id)
            continue

        if slot.platform not in CAROUSEL_PLATFORMS:
            logger.info(
                "Skipping non-carousel platform %s for slot %s",
                slot.platform,
                slot.slot_id,
            )
            continue

        try:
            slides = paginate_content(slot.caption, slot.image_prompt, brand)
            slot_dir = root / slot.slot_id
            slide_paths: list[str] = []

            for slide in slides:
                filename = f"{slot.slot_id}_slide_{slide.slide_number:02d}.png"
                output_path = slot_dir / filename
                render_slide(slide, brand, output_path, total_slides=len(slides))
                slide_paths.append(str(output_path))

            results.append(
                CarouselResult(
                    slot_id=slot.slot_id,
                    platform=slot.platform,
                    slide_paths=slide_paths,
                    output_dir=str(slot_dir),
                    status="success",
                )
            )
            logger.info(
                "Generated %d carousel slides for slot %s → %s",
                len(slides),
                slot.slot_id,
                slot_dir,
            )

        except Exception as exc:
            logger.error(
                "Unexpected error processing slot %s: %s",
                slot.slot_id,
                exc,
            )
            results.append(
                CarouselResult(
                    slot_id=slot.slot_id,
                    platform=slot.platform,
                    slide_paths=[],
                    output_dir="",
                    status="error",
                    error=f"Unexpected error: {exc}",
                )
            )

    return results


def wrap_results_as_envelope(results: list[CarouselResult]) -> AgentEnvelope:
    """Package carousel results into an AgentEnvelope for the Publisher."""
    return AgentEnvelope(
        from_agent="carousel_creator",
        to_agent="publisher",
        envelope_type="carousel_results",
        payload={"carousels": [r.model_dump() for r in results]},
        signature="placeholder",
        timestamp=datetime.now(tz=timezone.utc),
    )
