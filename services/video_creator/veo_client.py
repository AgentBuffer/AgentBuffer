"""Google Veo API wrapper — handles authentication, video generation, and polling."""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path

from google import genai
from google.genai import types as genai_types

from services.shared.models import VideoRequest, VideoResult
from services.video_creator.config import (
    MAX_RETRIES,
    OUTPUT_DIR,
    POLL_BACKOFF_FACTOR,
    POLL_INITIAL_DELAY_SEC,
    POLL_MAX_DELAY_SEC,
    POLL_TIMEOUT_SEC,
    VEO_MODEL,
)

logger = logging.getLogger(__name__)


class VeoClient:
    """Wraps the Google GenAI SDK to generate videos via Veo."""

    def __init__(self, client: genai.Client | None = None) -> None:
        self._client = client or genai.Client()

    async def generate_video(self, request: VideoRequest) -> VideoResult:
        """Submit a video generation request and poll until completion.

        Returns a VideoResult with status "success", "error", or "timeout".
        Never raises — all failures are captured in the result.
        """
        result: VideoResult | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            result = await self._attempt_generate(request, attempt)
            if result.status == "success" or result.status == "timeout":
                return result
            if attempt < MAX_RETRIES:
                logger.warning(
                    "Veo attempt %d/%d failed for slot %s: %s — retrying",
                    attempt,
                    MAX_RETRIES,
                    request.slot_id,
                    result.error,
                )
                await asyncio.sleep(POLL_INITIAL_DELAY_SEC * attempt)
        if result is None:
            return VideoResult(
                slot_id=request.slot_id,
                platform=request.platform,
                status="error",
                error="MAX_RETRIES is 0 — no attempts were made",
            )
        return result

    async def _attempt_generate(
        self,
        request: VideoRequest,
        attempt: int,
    ) -> VideoResult:
        try:
            operation = await asyncio.to_thread(
                self._submit_generation, request
            )
        except Exception as exc:
            logger.error(
                "Veo submission failed (attempt %d) for slot %s: %s",
                attempt,
                request.slot_id,
                exc,
            )
            return VideoResult(
                slot_id=request.slot_id,
                platform=request.platform,
                status="error",
                error=f"Submission failed: {exc}",
            )

        return await self._poll_for_result(operation, request)

    def _submit_generation(
        self,
        request: VideoRequest,
    ) -> genai_types.GenerateVideosOperation:
        """Synchronous call to submit video generation."""
        return self._client.models.generate_videos(
            model=VEO_MODEL,
            prompt=request.prompt,
            config=genai_types.GenerateVideosConfig(
                aspect_ratio=request.aspect_ratio,
                number_of_videos=1,
            ),
        )

    async def _poll_for_result(
        self,
        operation: genai_types.GenerateVideosOperation,
        request: VideoRequest,
    ) -> VideoResult:
        """Poll the operation with exponential backoff until done or timeout."""
        delay = POLL_INITIAL_DELAY_SEC
        start = time.monotonic()

        while not operation.done:
            elapsed = time.monotonic() - start
            if elapsed >= POLL_TIMEOUT_SEC:
                logger.error(
                    "Veo polling timed out after %.0fs for slot %s",
                    elapsed,
                    request.slot_id,
                )
                return VideoResult(
                    slot_id=request.slot_id,
                    platform=request.platform,
                    status="timeout",
                    error=f"Polling timed out after {elapsed:.0f}s",
                )

            await asyncio.sleep(delay)
            delay = min(delay * POLL_BACKOFF_FACTOR, POLL_MAX_DELAY_SEC)

            try:
                operation = await asyncio.to_thread(
                    self._refresh_operation, operation
                )
            except Exception as exc:
                logger.error(
                    "Veo poll refresh failed for slot %s: %s",
                    request.slot_id,
                    exc,
                )
                return VideoResult(
                    slot_id=request.slot_id,
                    platform=request.platform,
                    status="error",
                    error=f"Poll refresh failed: {exc}",
                )

        return self._extract_result(operation, request)

    def _refresh_operation(
        self,
        operation: genai_types.GenerateVideosOperation,
    ) -> genai_types.GenerateVideosOperation:
        """Refresh the operation status."""
        return self._client.operations.get(operation)

    def _extract_result(
        self,
        operation: genai_types.GenerateVideosOperation,
        request: VideoRequest,
    ) -> VideoResult:
        """Extract video data from a completed operation and save to disk."""
        try:
            response = operation.result
            if not response or not response.generated_videos:
                return VideoResult(
                    slot_id=request.slot_id,
                    platform=request.platform,
                    status="error",
                    error="No videos in response",
                )

            video = response.generated_videos[0]
            if not video.video or not video.video.uri:
                return VideoResult(
                    slot_id=request.slot_id,
                    platform=request.platform,
                    status="error",
                    error="Video object missing URI",
                )

            local_path = self._save_video(video.video, request)

            return VideoResult(
                slot_id=request.slot_id,
                video_url=video.video.uri,
                local_path=str(local_path),
                platform=request.platform,
                duration_seconds=request.duration_seconds,
                status="success",
            )
        except Exception as exc:
            logger.error(
                "Failed to extract Veo result for slot %s: %s",
                request.slot_id,
                exc,
            )
            return VideoResult(
                slot_id=request.slot_id,
                platform=request.platform,
                status="error",
                error=f"Result extraction failed: {exc}",
            )

    def _save_video(
        self,
        video: genai_types.Video,
        request: VideoRequest,
    ) -> Path:
        """Download video bytes and write to the output directory."""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = int(time.time())
        filename = f"{request.platform.value}_{request.slot_id}_{timestamp}.mp4"
        path = OUTPUT_DIR / filename

        video_bytes = self._client.files.download(file=video)
        with open(path, "wb") as f:
            for chunk in video_bytes:
                f.write(chunk)

        logger.info("Saved video to %s", path)
        return path
