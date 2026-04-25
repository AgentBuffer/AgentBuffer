"""Tests for the BrandPerformanceSummary builder."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from services.performance_harvester.summary import build_performance_summary
from services.shared.models import BrandPerformanceSummary, PerformanceRecord, Platform


def _make_record(
    post_id: str,
    platform: Platform,
    content_type: str,
    engagement_rate: float,
    hour: int = 10,
    weekday: int = 0,
) -> PerformanceRecord:
    dt = datetime(2026, 4, 21 + weekday, hour, 0, tzinfo=timezone.utc)
    return PerformanceRecord(
        post_id=post_id,
        platform=platform,
        published_at=dt,
        content_type=content_type,
        likes=10,
        shares=2,
        comments=3,
        reach=500,
        engagement_rate=engagement_rate,
    )


def _mock_ctx(records: dict[str, PerformanceRecord]) -> MagicMock:
    """Build a mock Context whose storage holds serialised PerformanceRecords."""
    data: dict[str, str] = {}
    for key, rec in records.items():
        data[key] = rec.model_dump_json()

    storage = MagicMock()
    storage._data = data
    storage.get = lambda k: data.get(k)

    ctx = MagicMock()
    ctx.storage = storage
    return ctx


def test_returns_none_when_no_records():
    ctx = _mock_ctx({})
    result = build_performance_summary(ctx, "brand-xyz")
    assert result is None


def test_basic_summary():
    records = {
        "perf:brand-1:p1": _make_record(
            "p1", Platform.INSTAGRAM, "carousel", 5.0, hour=9, weekday=0
        ),
        "perf:brand-1:p2": _make_record("p2", Platform.INSTAGRAM, "video", 2.0, hour=14, weekday=2),
        "perf:brand-1:p3": _make_record(
            "p3", Platform.INSTAGRAM, "carousel", 4.5, hour=9, weekday=0
        ),
        "perf:brand-1:p4": _make_record("p4", Platform.LINKEDIN, "text", 3.0, hour=8, weekday=1),
    }

    ctx = _mock_ctx(records)
    summary = build_performance_summary(ctx, "brand-1")

    assert summary is not None
    assert isinstance(summary, BrandPerformanceSummary)
    assert summary.brand_id == "brand-1"
    assert len(summary.top_formats) > 0
    assert "instagram" in summary.best_times
    assert isinstance(summary.avoid_patterns, list)


def test_ignores_other_brands():
    records = {
        "perf:brand-A:p1": _make_record("p1", Platform.X, "text", 3.0),
        "perf:brand-B:p2": _make_record("p2", Platform.X, "video", 4.0),
    }
    ctx = _mock_ctx(records)

    summary_a = build_performance_summary(ctx, "brand-A")
    assert summary_a is not None
    assert summary_a.brand_id == "brand-A"
    assert all(f["sample_size"] >= 1 for f in summary_a.top_formats)

    summary_b = build_performance_summary(ctx, "brand-B")
    assert summary_b is not None


def test_top_formats_ranking():
    records = {
        "perf:brand-1:p1": _make_record("p1", Platform.INSTAGRAM, "carousel", 8.0),
        "perf:brand-1:p2": _make_record("p2", Platform.INSTAGRAM, "carousel", 7.0),
        "perf:brand-1:p3": _make_record("p3", Platform.INSTAGRAM, "video", 2.0),
        "perf:brand-1:p4": _make_record("p4", Platform.INSTAGRAM, "text", 1.0),
    }
    ctx = _mock_ctx(records)
    summary = build_performance_summary(ctx, "brand-1")

    assert summary is not None
    ig_formats = [f for f in summary.top_formats if f["platform"] == "instagram"]
    assert ig_formats[0]["content_type"] == "carousel"
