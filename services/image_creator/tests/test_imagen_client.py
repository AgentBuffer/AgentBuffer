"""Mock tests for the Imagen API integration.

Tests cover:
- Successful image generation flow (submit → extract → save)
- API submission errors
- Empty/malformed API responses
- Retry logic on transient failures
- File saving to correct path
- Parent agent is never crashed by any failure mode
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from services.image_creator import imagen_client as imagen_client_module
from services.image_creator.agent import process_approved_slate
from services.image_creator.imagen_client import ImagenClient
from services.shared.models import (
    ApprovedSlate,
    BrandKit,
    ContentSlot,
    CriticScore,
    CriticVerdict,
    ImageRequest,
    ImageResult,
    Platform,
    Slate,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def image_request() -> ImageRequest:
    return ImageRequest(
        slot_id="slot-001",
        prompt="Create a stunning 4:5 vertical Instagram image.",
        aspect_ratio="4:5",
        platform=Platform.INSTAGRAM,
        brand_context="Brand: TestBrand. Voice: Friendly. Audience: Millennials.",
        negative_prompt="No text, no watermarks",
    )


@pytest.fixture()
def brand() -> BrandKit:
    return BrandKit(
        brand_id="brand-001",
        org_id="org-001",
        name="TestBrand",
        tagline="Innovation for everyone",
        voice_description="Friendly and authoritative",
        target_audience="Tech-savvy millennials",
        color_palette=["#FF5733"],
        sample_captions=["Test caption"],
        industry="Technology",
    )


@pytest.fixture()
def approved_slate() -> ApprovedSlate:
    slots = [
        ContentSlot(
            slot_id="slot-ig",
            slot_number=1,
            caption="Instagram content",
            image_prompt="aesthetic flat-lay",
            platform=Platform.INSTAGRAM,
            scheduled_for=datetime(2025, 7, 1, tzinfo=timezone.utc),
        ),
        ContentSlot(
            slot_id="slot-li",
            slot_number=2,
            caption="LinkedIn content",
            image_prompt="professional headshot",
            platform=Platform.LINKEDIN,
            scheduled_for=datetime(2025, 7, 2, tzinfo=timezone.utc),
        ),
        ContentSlot(
            slot_id="slot-rejected",
            slot_number=3,
            caption="Rejected content",
            image_prompt="bad visual",
            platform=Platform.X,
            scheduled_for=datetime(2025, 7, 3, tzinfo=timezone.utc),
        ),
    ]
    verdicts = [
        CriticVerdict(
            slot_id="slot-ig",
            scores=[CriticScore(axis="relevance", score=9.0, reasoning="Great")],
            average=9.0,
            approved=True,
            summary="Approved",
        ),
        CriticVerdict(
            slot_id="slot-li",
            scores=[CriticScore(axis="relevance", score=8.5, reasoning="Good")],
            average=8.5,
            approved=True,
            summary="Approved",
        ),
        CriticVerdict(
            slot_id="slot-rejected",
            scores=[CriticScore(axis="relevance", score=3.0, reasoning="Weak")],
            average=3.0,
            approved=False,
            summary="Rejected",
        ),
    ]
    slate = Slate(
        slate_id="slate-001",
        brand_id="brand-001",
        org_id="org-001",
        slots=slots,
        generation_context="Weekly content plan",
    )
    return ApprovedSlate(slate=slate, verdicts=verdicts)


def _make_success_response(image_bytes: bytes = b"fake-png-bytes") -> MagicMock:
    """Create a mock Imagen response with image data."""
    image_obj = SimpleNamespace(image_bytes=image_bytes)
    generated_image = SimpleNamespace(image=image_obj)
    response = MagicMock()
    response.generated_images = [generated_image]
    return response


# ---------------------------------------------------------------------------
# ImagenClient tests
# ---------------------------------------------------------------------------


class TestImagenClientSuccess:
    @pytest.mark.asyncio()
    async def test_successful_generation(self, image_request: ImageRequest, tmp_path: Path) -> None:
        mock_client = MagicMock()
        mock_client.models.generate_images.return_value = _make_success_response()

        with patch.object(imagen_client_module, "OUTPUT_DIR", tmp_path):
            client = ImagenClient(client=mock_client)
            result = await client.generate_image(image_request)

        assert result.status == "success"
        assert result.slot_id == "slot-001"
        assert result.local_path is not None
        assert Path(result.local_path).name.startswith("instagram_slot-001_")
        assert Path(result.local_path).suffix == ".png"

    @pytest.mark.asyncio()
    async def test_image_file_is_written(self, image_request: ImageRequest, tmp_path: Path) -> None:
        mock_client = MagicMock()
        mock_client.models.generate_images.return_value = _make_success_response(b"png-data-chunk")

        with patch.object(imagen_client_module, "OUTPUT_DIR", tmp_path):
            client = ImagenClient(client=mock_client)
            result = await client.generate_image(image_request)

        saved = Path(result.local_path)
        assert saved.exists()
        assert saved.read_bytes() == b"png-data-chunk"


class TestImagenClientErrors:
    @pytest.mark.asyncio()
    async def test_submission_error_returns_error_status(self, image_request: ImageRequest) -> None:
        mock_client = MagicMock()
        mock_client.models.generate_images.side_effect = RuntimeError("API 500")

        with patch.object(imagen_client_module, "MAX_RETRIES", 1):
            client = ImagenClient(client=mock_client)
            result = await client.generate_image(image_request)

        assert result.status == "error"
        assert "API 500" in result.error

    @pytest.mark.asyncio()
    async def test_empty_response_returns_error(self, image_request: ImageRequest) -> None:
        mock_client = MagicMock()
        response = MagicMock()
        response.generated_images = []
        mock_client.models.generate_images.return_value = response

        with patch.object(imagen_client_module, "MAX_RETRIES", 1):
            client = ImagenClient(client=mock_client)
            result = await client.generate_image(image_request)

        assert result.status == "error"
        assert "no images" in result.error.lower()

    @pytest.mark.asyncio()
    async def test_missing_image_bytes_returns_error(self, image_request: ImageRequest) -> None:
        mock_client = MagicMock()
        image_obj = SimpleNamespace(image_bytes=None)
        generated_image = SimpleNamespace(image=image_obj)
        response = MagicMock()
        response.generated_images = [generated_image]
        mock_client.models.generate_images.return_value = response

        with patch.object(imagen_client_module, "MAX_RETRIES", 1):
            client = ImagenClient(client=mock_client)
            result = await client.generate_image(image_request)

        assert result.status == "error"

    @pytest.mark.asyncio()
    async def test_errors_never_raise_exceptions(self, image_request: ImageRequest) -> None:
        """All error paths must return ImageResult, never raise."""
        mock_client = MagicMock()
        mock_client.models.generate_images.side_effect = Exception("Catastrophic")

        with patch.object(imagen_client_module, "MAX_RETRIES", 1):
            client = ImagenClient(client=mock_client)
            result = await client.generate_image(image_request)

        assert isinstance(result, ImageResult)
        assert result.status == "error"


class TestImagenClientRetries:
    @pytest.mark.asyncio()
    async def test_retries_on_transient_failure_then_succeeds(
        self, image_request: ImageRequest, tmp_path: Path
    ) -> None:
        mock_client = MagicMock()
        mock_client.models.generate_images.side_effect = [
            RuntimeError("Transient 503"),
            _make_success_response(),
        ]

        with (
            patch.object(imagen_client_module, "OUTPUT_DIR", tmp_path),
            patch.object(imagen_client_module, "MAX_RETRIES", 3),
            patch.object(imagen_client_module, "RETRY_DELAY_SEC", 0.01),
        ):
            client = ImagenClient(client=mock_client)
            result = await client.generate_image(image_request)

        assert result.status == "success"
        assert mock_client.models.generate_images.call_count == 2


# ---------------------------------------------------------------------------
# Integration test: process_approved_slate
# ---------------------------------------------------------------------------


class TestProcessApprovedSlate:
    @pytest.mark.asyncio()
    async def test_processes_only_approved_slots(
        self,
        approved_slate: ApprovedSlate,
        brand: BrandKit,
        tmp_path: Path,
    ) -> None:
        mock_client = MagicMock()
        mock_client.models.generate_images.return_value = _make_success_response()

        with patch.object(imagen_client_module, "OUTPUT_DIR", tmp_path):
            imagen = ImagenClient(client=mock_client)
            results = await process_approved_slate(approved_slate, brand, imagen)

        assert len(results) == 2
        result_ids = {r.slot_id for r in results}
        assert "slot-ig" in result_ids
        assert "slot-li" in result_ids
        assert "slot-rejected" not in result_ids

    @pytest.mark.asyncio()
    async def test_one_failure_does_not_crash_others(
        self,
        approved_slate: ApprovedSlate,
        brand: BrandKit,
        tmp_path: Path,
    ) -> None:
        mock_client = MagicMock()
        mock_client.models.generate_images.side_effect = [
            RuntimeError("First slot fails"),
            _make_success_response(),
        ]

        with (
            patch.object(imagen_client_module, "OUTPUT_DIR", tmp_path),
            patch.object(imagen_client_module, "MAX_RETRIES", 1),
        ):
            imagen = ImagenClient(client=mock_client)
            results = await process_approved_slate(approved_slate, brand, imagen)

        assert len(results) == 2
        statuses = {r.slot_id: r.status for r in results}
        assert statuses["slot-ig"] == "error"
        assert statuses["slot-li"] == "success"

    @pytest.mark.asyncio()
    async def test_never_crashes_parent_agent(
        self,
        approved_slate: ApprovedSlate,
        brand: BrandKit,
    ) -> None:
        """Even with a totally broken client, process_approved_slate returns results."""
        mock_client = MagicMock()
        mock_client.models.generate_images.side_effect = Exception("Total failure")

        with patch.object(imagen_client_module, "MAX_RETRIES", 1):
            imagen = ImagenClient(client=mock_client)
            results = await process_approved_slate(approved_slate, brand, imagen)

        assert isinstance(results, list)
        for r in results:
            assert isinstance(r, ImageResult)
