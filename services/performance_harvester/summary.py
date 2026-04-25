"""BrandPerformanceSummary builder.

Reads all ``perf:{brand_id}:*`` PerformanceRecords from ctx.storage and
computes an actionable summary the Strategist can use to optimise the next
content slate.
"""

from __future__ import annotations

import logging
from collections import defaultdict

from uagents import Context

from services.shared.models import BrandPerformanceSummary, PerformanceRecord

logger = logging.getLogger(__name__)


def build_performance_summary(
    ctx: Context,
    brand_id: str,
) -> BrandPerformanceSummary | None:
    """Aggregate stored PerformanceRecords into a BrandPerformanceSummary.

    Returns ``None`` when no records exist for the given *brand_id* (new
    accounts that have no history yet).
    """
    records = _load_records(ctx, brand_id)
    if not records:
        return None

    top_formats = _top_content_types(records)
    best_times = _best_times(records)
    avoid_patterns = _avoid_patterns(records)

    return BrandPerformanceSummary(
        brand_id=brand_id,
        top_formats=top_formats,
        best_times=best_times,
        avoid_patterns=avoid_patterns,
    )


# ── internal helpers ──


def _load_records(ctx: Context, brand_id: str) -> list[PerformanceRecord]:
    """Scan ctx.storage for all perf:{brand_id}:* keys."""
    prefix = f"perf:{brand_id}:"
    records: list[PerformanceRecord] = []

    all_keys: list[str] = []
    try:
        all_keys = ctx.storage._data.keys() if hasattr(ctx.storage, "_data") else []
    except Exception:
        pass

    if not all_keys:
        try:
            all_keys = list(ctx.storage.keys()) if hasattr(ctx.storage, "keys") else []
        except Exception:
            pass

    for key in all_keys:
        if not key.startswith(prefix):
            continue
        raw = ctx.storage.get(key)
        if raw is None:
            continue
        try:
            record = PerformanceRecord.model_validate_json(raw)
            records.append(record)
        except Exception:
            logger.warning("Skipping malformed perf record at key %s", key)
    return records


def _top_content_types(
    records: list[PerformanceRecord],
    top_n: int = 3,
) -> list[dict]:
    """Top *top_n* content types by average engagement_rate, per platform."""
    buckets: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in records:
        buckets[r.platform.value][r.content_type].append(r.engagement_rate)

    results: list[dict] = []
    for platform, types in buckets.items():
        ranked = sorted(
            types.items(),
            key=lambda kv: sum(kv[1]) / len(kv[1]),
            reverse=True,
        )
        for content_type, rates in ranked[:top_n]:
            avg = round(sum(rates) / len(rates), 4)
            results.append(
                {
                    "platform": platform,
                    "content_type": content_type,
                    "avg_engagement_rate": avg,
                    "sample_size": len(rates),
                }
            )
    return results


def _best_times(records: list[PerformanceRecord]) -> dict:
    """Best performing day-of-week and hour per platform."""
    day_buckets: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    hour_buckets: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))

    for r in records:
        plat = r.platform.value
        day_name = r.published_at.strftime("%A")
        day_buckets[plat][day_name].append(r.engagement_rate)
        hour_buckets[plat][r.published_at.hour].append(r.engagement_rate)

    result: dict[str, dict] = {}
    for plat in day_buckets:
        best_day = max(
            day_buckets[plat].items(),
            key=lambda kv: sum(kv[1]) / len(kv[1]),
        )
        best_hour = max(
            hour_buckets[plat].items(),
            key=lambda kv: sum(kv[1]) / len(kv[1]),
        )
        result[plat] = {
            "best_day": best_day[0],
            "best_day_avg_engagement": round(sum(best_day[1]) / len(best_day[1]), 4),
            "best_hour_utc": best_hour[0],
            "best_hour_avg_engagement": round(sum(best_hour[1]) / len(best_hour[1]), 4),
        }
    return result


def _avoid_patterns(
    records: list[PerformanceRecord],
    threshold_percentile: float = 0.25,
) -> list[str]:
    """Content patterns whose engagement is in the bottom quartile."""
    if not records:
        return []

    rates = sorted(r.engagement_rate for r in records)
    cutoff_idx = max(1, int(len(rates) * threshold_percentile))
    cutoff = rates[cutoff_idx - 1]

    weak: dict[str, list[float]] = defaultdict(list)
    for r in records:
        if r.engagement_rate <= cutoff:
            label = f"{r.content_type} on {r.platform.value}"
            weak[label].append(r.engagement_rate)

    patterns: list[str] = []
    for label, eng_rates in sorted(weak.items(), key=lambda kv: sum(kv[1]) / len(kv[1])):
        avg = round(sum(eng_rates) / len(eng_rates), 4)
        patterns.append(f"{label} (avg engagement {avg}%)")
    return patterns
