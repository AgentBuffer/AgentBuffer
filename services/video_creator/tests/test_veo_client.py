"""Mock tests for the Veo API integration.

Tests cover:
- Successful video generation flow (submit → poll → download)
- Timeout handling (polling exceeds max time)
- API submission errors (4xx, 5xx equivalent)
- Poll refresh errors mid-flight
- Empty/malformed API responses
- Retry logic on transient failures
- Parent agent is never crashed by any failure mode
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from services.shared.models import (
    ApprovedSlate,
    BrandKit,
    ContentSlot,
    CriticScore,
    CriticVerdict,
    Platform,
    Slate,
    VideoRequest,
    VideoResult,
)
from services.video_creator import veo_client as veo_client_module
from services.video_creator.agent import process_approved_slate
from services.video_creator.veo_client import VeoClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def video_request() -> VideoRequest:
    return VideoRequest(
        slot_id="slot-001",
        prompt="Create a vertical 9:16 TikTok video with fast cuts.",
        aspect_ratio="9:16",
        platform=Platform.TIKTOK,
        audio_cue="upbeat lo-fi remix",
        brand_context="Brand: TestBrand. Voice: Friendly. Audience: Millennials.",
        duration_seconds=8,
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
            slot_id="slot-tt",
            slot_number=1,
            caption="TikTok content",
            image_prompt="product on desk",
            platform=Platform.TIKTOK,
            scheduled_for=datetime(2025, 7, 1, tzinfo=timezone.utc),
        ),
        ContentSlot(
            slot_id="slot-yt",
            slot_number=2,
            caption="YouTube content",
            image_prompt="cinematic factory shot",
            platform=Platform.YOUTUBE,
            scheduled_for=datetime(2025, 7, 2, tzinfo=timezone.utc),
        ),
        ContentSlot(
            slot_id="slot-rejected",
            slot_number=3,
            caption="Rejected content",
            image_prompt="bad visual",
            platform=Platform.INSTAGRAM,
            scheduled_for=datetime(2025, 7, 3, tzinfo=timezone.utc),
        ),
    ]
    verdicts = [
        CriticVerdict(
            slot_id="slot-tt",
            scores=[CriticScore(axis="relevance", score=9.0, reasoning="Great")],
            average=9.0,
            approved=True,
            summary="Approved",
        ),
        CriticVerdict(
            slot_id="slot-yt",
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


def _make_done_operation(video_uri: str = "gs://bucket/video.mp4") -> MagicMock:
    """Create a mock operation that is already done with a successful result."""
    video_obj = SimpleNamespace(uri=video_uri)
    generated_video = SimpleNamespace(video=video_obj)
    response = SimpleNamespace(generated_videos=[generated_video])
    op = MagicMock()
    op.done = True
    op.result = response
    return op


def _make_pending_then_done_operation(
    polls_until_done: int = 2,
    video_uri: str = "gs://bucket/video.mp4",
) -> MagicMock:
    """Create a mock operation that takes N polls to complete."""
    video_obj = SimpleNamespace(uri=video_uri)
    generated_video = SimpleNamespace(video=video_obj)
    response = SimpleNamespace(generated_videos=[generated_video])

    call_count = 0

    op = MagicMock()
    type(op).done = property(lambda self: self._check_done())
    op._polls_until_done = polls_until_done
    op._call_count = 0
    op.result = response

    def check_done() -> bool:
        nonlocal call_count
        call_count += 1
        return call_count > polls_until_done

    op._check_done = check_done
    return op


# ---------------------------------------------------------------------------
# VeoClient tests
# ---------------------------------------------------------------------------


class TestVeoClientSuccess:
    @pytest.mark.asyncio()
    async def test_successful_generation(self, video_request: VideoRequest, tmp_path: Path) -> None:
        mock_client = MagicMock()
        done_op = _make_done_operation()
        mock_client.models.generate_videos.return_value = done_op
        mock_client.files.download.return_value = [b"fake-video-bytes"]

        with patch.object(veo_client_module, "OUTPUT_DIR", tmp_path):
            client = VeoClient(client=mock_client)
            result = await client.generate_video(video_request)

        assert result.status == "success"
        assert result.slot_id == "slot-001"
        assert result.video_url == "gs://bucket/video.mp4"
        assert result.local_path is not None
        assert Path(result.local_path).name.startswith("tiktok_slot-001_")
        assert Path(result.local_path).suffix == ".mp4"

    @pytest.mark.asyncio()
    async def test_video_file_is_written(self, video_request: VideoRequest, tmp_path: Path) -> None:
        mock_client = MagicMock()
        done_op = _make_done_operation()
        mock_client.models.generate_videos.return_value = done_op
        mock_client.files.download.return_value = [b"video-data-chunk"]

        with patch.object(veo_client_module, "OUTPUT_DIR", tmp_path):
            client = VeoClient(client=mock_client)
            result = await client.generate_video(video_request)

        saved = Path(result.local_path)
        assert saved.exists()
        assert saved.read_bytes() == b"video-data-chunk"


class TestVeoClientTimeout:
    @pytest.mark.asyncio()
    async def test_timeout_returns_timeout_status(self, video_request: VideoRequest) -> None:
        mock_client = MagicMock()
        never_done_op = MagicMock()
        never_done_op.done = False
        mock_client.models.generate_videos.return_value = never_done_op
        mock_client.operations.get.return_value = never_done_op

        with (
            patch.object(veo_client_module, "POLL_TIMEOUT_SEC", 0.1),
            patch.object(veo_client_module, "POLL_INITIAL_DELAY_SEC", 0.05),
            patch.object(veo_client_module, "POLL_MAX_DELAY_SEC", 0.05),
        ):
            client = VeoClient(client=mock_client)
            result = await client.generate_video(video_request)

        assert result.status == "timeout"
        assert "timed out" in result.error.lower()
        assert result.slot_id == "slot-001"

    @pytest.mark.asyncio()
    async def test_timeout_does_not_raise(self, video_request: VideoRequest) -> None:
        """Ensure timeouts never bubble up as exceptions."""
        mock_client = MagicMock()
        never_done_op = MagicMock()
        never_done_op.done = False
        mock_client.models.generate_videos.return_value = never_done_op
        mock_client.operations.get.return_value = never_done_op

        with (
            patch.object(veo_client_module, "POLL_TIMEOUT_SEC", 0.1),
            patch.object(veo_client_module, "POLL_INITIAL_DELAY_SEC", 0.05),
            patch.object(veo_client_module, "POLL_MAX_DELAY_SEC", 0.05),
        ):
            client = VeoClient(client=mock_client)
            result = await client.generate_video(video_request)

        assert isinstance(result, VideoResult)


class TestVeoClientErrors:
    @pytest.mark.asyncio()
    async def test_submission_error_returns_error_status(self, video_request: VideoRequest) -> None:
        mock_client = MagicMock()
        mock_client.models.generate_videos.side_effect = RuntimeError("API 500")

        with patch.object(veo_client_module, "MAX_RETRIES", 1):
            client = VeoClient(client=mock_client)
            result = await client.generate_video(video_request)

        assert result.status == "error"
        assert "API 500" in result.error

    @pytest.mark.asyncio()
    async def test_poll_refresh_error_returns_error_status(
        self, video_request: VideoRequest
    ) -> None:
        mock_client = MagicMock()
        pending_op = MagicMock()
        pending_op.done = False
        mock_client.models.generate_videos.return_value = pending_op
        mock_client.operations.get.side_effect = ConnectionError("Network down")

        with (
            patch.object(veo_client_module, "POLL_INITIAL_DELAY_SEC", 0.01),
            patch.object(veo_client_module, "MAX_RETRIES", 1),
        ):
            client = VeoClient(client=mock_client)
            result = await client.generate_video(video_request)

        assert result.status == "error"
        assert "Network down" in result.error

    @pytest.mark.asyncio()
    async def test_empty_response_returns_error(self, video_request: VideoRequest) -> None:
        mock_client = MagicMock()
        op = MagicMock()
        op.done = True
        op.result = SimpleNamespace(generated_videos=[])
        mock_client.models.generate_videos.return_value = op

        with patch.object(veo_client_module, "MAX_RETRIES", 1):
            client = VeoClient(client=mock_client)
            result = await client.generate_video(video_request)

        assert result.status == "error"
        assert "no videos" in result.error.lower()

    @pytest.mark.asyncio()
    async def test_missing_video_uri_returns_error(self, video_request: VideoRequest) -> None:
        mock_client = MagicMock()
        op = MagicMock()
        op.done = True
        generated = SimpleNamespace(video=SimpleNamespace(uri=None))
        op.result = SimpleNamespace(generated_videos=[generated])
        mock_client.models.generate_videos.return_value = op

        with patch.object(veo_client_module, "MAX_RETRIES", 1):
            client = VeoClient(client=mock_client)
            result = await client.generate_video(video_request)

        assert result.status == "error"

    @pytest.mark.asyncio()
    async def test_errors_never_raise_exceptions(self, video_request: VideoRequest) -> None:
        """All error paths must return VideoResult, never raise."""
        mock_client = MagicMock()
        mock_client.models.generate_videos.side_effect = Exception("Catastrophic")

        with patch.object(veo_client_module, "MAX_RETRIES", 1):
            client = VeoClient(client=mock_client)
            result = await client.generate_video(video_request)

        assert isinstance(result, VideoResult)
        assert result.status == "error"


class TestVeoClientRetries:
    @pytest.mark.asyncio()
    async def test_retries_on_transient_failure_then_succeeds(
        self, video_request: VideoRequest, tmp_path: Path
    ) -> None:
        mock_client = MagicMock()
        done_op = _make_done_operation()
        mock_client.models.generate_videos.side_effect = [
            RuntimeError("Transient 503"),
            done_op,
        ]
        mock_client.files.download.return_value = [b"video-data"]

        with (
            patch.object(veo_client_module, "OUTPUT_DIR", tmp_path),
            patch.object(veo_client_module, "MAX_RETRIES", 3),
            patch.object(veo_client_module, "POLL_INITIAL_DELAY_SEC", 0.01),
        ):
            client = VeoClient(client=mock_client)
            result = await client.generate_video(video_request)

        assert result.status == "success"
        assert mock_client.models.generate_videos.call_count == 2


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
        done_op = _make_done_operation()
        mock_client.models.generate_videos.return_value = done_op
        mock_client.files.download.return_value = [b"video"]

        with patch.object(veo_client_module, "OUTPUT_DIR", tmp_path):
            veo = VeoClient(client=mock_client)
            results = await process_approved_slate(approved_slate, brand, veo)

        assert len(results) == 2
        result_ids = {r.slot_id for r in results}
        assert "slot-tt" in result_ids
        assert "slot-yt" in result_ids
        assert "slot-rejected" not in result_ids

    @pytest.mark.asyncio()
    async def test_one_failure_does_not_crash_others(
        self,
        approved_slate: ApprovedSlate,
        brand: BrandKit,
        tmp_path: Path,
    ) -> None:
        mock_client = MagicMock()
        done_op = _make_done_operation()
        mock_client.models.generate_videos.side_effect = [
            RuntimeError("First slot fails"),
            done_op,
        ]
        mock_client.files.download.return_value = [b"video"]

        with (
            patch.object(veo_client_module, "OUTPUT_DIR", tmp_path),
            patch.object(veo_client_module, "MAX_RETRIES", 1),
        ):
            veo = VeoClient(client=mock_client)
            results = await process_approved_slate(approved_slate, brand, veo)

        assert len(results) == 2
        statuses = {r.slot_id: r.status for r in results}
        assert statuses["slot-tt"] == "error"
        assert statuses["slot-yt"] == "success"

    @pytest.mark.asyncio()
    async def test_never_crashes_parent_agent(
        self,
        approved_slate: ApprovedSlate,
        brand: BrandKit,
    ) -> None:
        """Even with a totally broken client, process_approved_slate returns results."""
        mock_client = MagicMock()
        mock_client.models.generate_videos.side_effect = Exception("Total failure")

        with patch.object(veo_client_module, "MAX_RETRIES", 1):
            veo = VeoClient(client=mock_client)
            results = await process_approved_slate(approved_slate, brand, veo)

        assert isinstance(results, list)
        for r in results:
            assert isinstance(r, VideoResult)
