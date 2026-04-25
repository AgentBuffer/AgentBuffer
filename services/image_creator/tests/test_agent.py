"""Unit tests for the Image Creator agent logic."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from services.image_creator import imagen_client as imagen_client_module
from services.image_creator.agent import process_approved_slate, wrap_results_as_envelope
from services.image_creator.imagen_client import ImagenClient
from services.image_creator.tests.test_imagen_client import _make_success_response
from services.shared.models import (
    AgentEnvelope,
    ApprovedSlate,
    BrandKit,
    ContentSlot,
    CriticScore,
    CriticVerdict,
    ImageResult,
    Platform,
    Slate,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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
            slot_id="slot-approved-1",
            slot_number=1,
            caption="Approved content one",
            image_prompt="beautiful landscape",
            platform=Platform.INSTAGRAM,
            scheduled_for=datetime(2025, 7, 1, tzinfo=timezone.utc),
        ),
        ContentSlot(
            slot_id="slot-approved-2",
            slot_number=2,
            caption="Approved content two",
            image_prompt="professional portrait",
            platform=Platform.LINKEDIN,
            scheduled_for=datetime(2025, 7, 2, tzinfo=timezone.utc),
        ),
        ContentSlot(
            slot_id="slot-unapproved",
            slot_number=3,
            caption="Unapproved content",
            image_prompt="low quality",
            platform=Platform.X,
            scheduled_for=datetime(2025, 7, 3, tzinfo=timezone.utc),
        ),
    ]
    verdicts = [
        CriticVerdict(
            slot_id="slot-approved-1",
            scores=[CriticScore(axis="relevance", score=9.0, reasoning="Great")],
            average=9.0,
            approved=True,
            summary="Approved",
        ),
        CriticVerdict(
            slot_id="slot-approved-2",
            scores=[CriticScore(axis="relevance", score=8.0, reasoning="Good")],
            average=8.0,
            approved=True,
            summary="Approved",
        ),
        CriticVerdict(
            slot_id="slot-unapproved",
            scores=[CriticScore(axis="relevance", score=2.0, reasoning="Poor")],
            average=2.0,
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


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestProcessApprovedSlate:
    @pytest.mark.asyncio()
    async def test_skips_unapproved_slots(
        self,
        approved_slate: ApprovedSlate,
        brand: BrandKit,
        tmp_path,
    ) -> None:
        mock_client = MagicMock()
        mock_client.models.generate_images.return_value = _make_success_response()

        with patch.object(imagen_client_module, "OUTPUT_DIR", tmp_path):
            imagen = ImagenClient(client=mock_client)
            results = await process_approved_slate(approved_slate, brand, imagen)

        result_ids = {r.slot_id for r in results}
        assert "slot-unapproved" not in result_ids
        assert len(results) == 2

    @pytest.mark.asyncio()
    async def test_generates_images_for_approved_slots(
        self,
        approved_slate: ApprovedSlate,
        brand: BrandKit,
        tmp_path,
    ) -> None:
        mock_client = MagicMock()
        mock_client.models.generate_images.return_value = _make_success_response()

        with patch.object(imagen_client_module, "OUTPUT_DIR", tmp_path):
            imagen = ImagenClient(client=mock_client)
            results = await process_approved_slate(approved_slate, brand, imagen)

        assert all(r.status == "success" for r in results)
        assert {r.slot_id for r in results} == {"slot-approved-1", "slot-approved-2"}


class TestWrapResultsAsEnvelope:
    def test_produces_correct_envelope(self) -> None:
        results = [
            ImageResult(
                slot_id="slot-001",
                image_url="https://cdn.example.com/img.png",
                local_path="/tmp/img.png",
                platform=Platform.INSTAGRAM,
                status="success",
            ),
            ImageResult(
                slot_id="slot-002",
                platform=Platform.LINKEDIN,
                status="error",
                error="API failure",
            ),
        ]

        envelope = wrap_results_as_envelope(results)

        assert isinstance(envelope, AgentEnvelope)
        assert envelope.from_agent == "image_creator"
        assert envelope.to_agent == "publisher"
        assert envelope.envelope_type == "image_results"
        assert len(envelope.payload["images"]) == 2
