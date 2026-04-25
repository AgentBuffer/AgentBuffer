"""Video Creator sub-agent — receives ApprovedSlates and generates platform videos.

This agent sits between the Critic and Publisher in the pipeline. It:
1. Receives an ApprovedSlate with critic-approved ContentSlots
2. Fetches current trends for each slot's target platform
3. Adapts each slot into a platform-optimized video prompt
4. Calls the Veo API to generate .mp4 files
5. Returns VideoResults for the Publisher to upload
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from services.shared.models import (
    AgentEnvelope,
    ApprovedSlate,
    BrandKit,
    VideoResult,
)
from services.video_creator.trends import adapt_prompt_for_platform, get_trends
from services.video_creator.veo_client import VeoClient

logger = logging.getLogger(__name__)


async def process_approved_slate(
    slate: ApprovedSlate,
    brand: BrandKit,
    veo_client: VeoClient | None = None,
) -> list[VideoResult]:
    """Generate videos for all approved slots in a slate.

    Args:
        slate: The critic-approved slate containing content slots.
        brand: The brand kit for contextual prompt generation.
        veo_client: Optional VeoClient instance (created if not provided).

    Returns:
        A list of VideoResult objects — one per approved slot.
    """
    client = veo_client or VeoClient()
    approved_slot_ids = {
        v.slot_id for v in slate.verdicts if v.approved
    }

    results: list[VideoResult] = []
    for slot in slate.slate.slots:
        if slot.slot_id not in approved_slot_ids:
            logger.info("Skipping unapproved slot %s", slot.slot_id)
            continue

        try:
            trends = get_trends(slot.platform)
            video_request = adapt_prompt_for_platform(slot, brand, trends)
            result = await client.generate_video(video_request)
            results.append(result)

            if result.status == "success":
                logger.info(
                    "Generated video for slot %s → %s",
                    slot.slot_id,
                    result.local_path,
                )
            else:
                logger.warning(
                    "Video generation issue for slot %s: %s — %s",
                    slot.slot_id,
                    result.status,
                    result.error,
                )
        except Exception as exc:
            logger.error(
                "Unexpected error processing slot %s: %s",
                slot.slot_id,
                exc,
            )
            results.append(
                VideoResult(
                    slot_id=slot.slot_id,
                    platform=slot.platform,
                    status="error",
                    error=f"Unexpected error: {exc}",
                )
            )

    return results


def wrap_results_as_envelope(results: list[VideoResult]) -> AgentEnvelope:
    """Package video results into an AgentEnvelope for the Publisher."""
    return AgentEnvelope(
        from_agent="video_creator",
        to_agent="publisher",
        envelope_type="video_results",
        payload={"videos": [r.model_dump() for r in results]},
        signature="placeholder",
        timestamp=datetime.now(tz=timezone.utc),
    )
