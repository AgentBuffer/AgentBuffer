"""Google Imagen API wrapper — handles image generation and file saving."""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path

from google import genai
from google.genai import types as genai_types

from services.image_creator.config import (
    IMAGEN_MODEL,
    MAX_RETRIES,
    OUTPUT_DIR,
    RETRY_DELAY_SEC,
)
from services.shared.models import ImageRequest, ImageResult

logger = logging.getLogger(__name__)


class ImagenClient:
    """Wraps the Google GenAI SDK to generate images via Imagen."""

    def __init__(self, client: genai.Client | None = None) -> None:
        self._client = client or genai.Client()

    async def generate_image(self, request: ImageRequest) -> ImageResult:
        """Generate an image from a prompt. Retries on transient failures.

        Returns an ImageResult with status "success" or "error".
        Never raises — all failures are captured in the result.
        """
        result: ImageResult | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            result = await self._attempt_generate(request, attempt)
            if result.status == "success":
                return result
            if attempt < MAX_RETRIES:
                logger.warning(
                    "Imagen attempt %d/%d failed for slot %s: %s — retrying",
                    attempt,
                    MAX_RETRIES,
                    request.slot_id,
                    result.error,
                )
                await asyncio.sleep(RETRY_DELAY_SEC * attempt)
        if result is None:
            return ImageResult(
                slot_id=request.slot_id,
                platform=request.platform,
                status="error",
                error="MAX_RETRIES is 0 — no attempts were made",
            )
        return result

    async def _attempt_generate(
        self,
        request: ImageRequest,
        attempt: int,
    ) -> ImageResult:
        try:
            response = await asyncio.to_thread(self._submit_generation, request)
        except Exception as exc:
            logger.error(
                "Imagen submission failed (attempt %d) for slot %s: %s",
                attempt,
                request.slot_id,
                exc,
            )
            return ImageResult(
                slot_id=request.slot_id,
                platform=request.platform,
                status="error",
                error=f"Submission failed: {exc}",
            )

        return self._extract_result(response, request)

    def _submit_generation(
        self,
        request: ImageRequest,
    ) -> genai_types.GenerateImagesResponse:
        """Synchronous call to generate an image via Imagen."""
        return self._client.models.generate_images(
            model=IMAGEN_MODEL,
            prompt=request.prompt,
            config=genai_types.GenerateImagesConfig(
                negative_prompt=request.negative_prompt or None,
                aspect_ratio=request.aspect_ratio,
                number_of_images=1,
            ),
        )

    def _extract_result(
        self,
        response: genai_types.GenerateImagesResponse,
        request: ImageRequest,
    ) -> ImageResult:
        """Extract image data from the response and save to disk."""
        try:
            if not response or not response.generated_images:
                return ImageResult(
                    slot_id=request.slot_id,
                    platform=request.platform,
                    status="error",
                    error="No images in response",
                )

            image = response.generated_images[0]
            if not image.image or not image.image.image_bytes:
                return ImageResult(
                    slot_id=request.slot_id,
                    platform=request.platform,
                    status="error",
                    error="Image object missing bytes",
                )

            local_path = self._save_image(image.image.image_bytes, request)

            return ImageResult(
                slot_id=request.slot_id,
                image_url=None,
                local_path=str(local_path),
                platform=request.platform,
                status="success",
            )
        except Exception as exc:
            logger.error(
                "Failed to extract Imagen result for slot %s: %s",
                request.slot_id,
                exc,
            )
            return ImageResult(
                slot_id=request.slot_id,
                platform=request.platform,
                status="error",
                error=f"Result extraction failed: {exc}",
            )

    def _save_image(
        self,
        image_bytes: bytes,
        request: ImageRequest,
    ) -> Path:
        """Write image bytes to the output directory."""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = int(time.time())
        filename = f"{request.platform.value}_{request.slot_id}_{timestamp}.png"
        path = OUTPUT_DIR / filename

        with open(path, "wb") as f:
            f.write(image_bytes)

        logger.info("Saved image to %s", path)
        return path
