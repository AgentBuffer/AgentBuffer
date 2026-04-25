"""Analytics tracking and reporting module."""

import datetime
from dataclasses import dataclass

from sqlalchemy import func

from youtube_automation.database import (
    AnalyticsSnapshot,
    Video,
    VideoStatus,
    get_db,
)


@dataclass
class PerformanceReport:
    total_videos: int
    total_views: int
    avg_ctr: float
    avg_retention: float
    top_videos: list[dict]
    worst_videos: list[dict]
    total_revenue: float
    growth_rate: float
    recommendations: list[str]


class AnalyticsTracker:
    """Track and analyze channel and video performance."""

    def record_snapshot(
        self,
        total_views: int = 0,
        total_subscribers: int = 0,
        total_watch_hours: float = 0.0,
        avg_ctr: float = 0.0,
        avg_retention: float = 0.0,
        revenue_ads: float = 0.0,
        revenue_affiliates: float = 0.0,
        revenue_products: float = 0.0,
        revenue_sponsors: float = 0.0,
        notes: str = "",
    ) -> AnalyticsSnapshot:
        """Record a daily analytics snapshot."""
        db = get_db()
        try:
            snapshot = AnalyticsSnapshot(
                date=datetime.datetime.utcnow(),
                total_views=total_views,
                total_subscribers=total_subscribers,
                total_watch_hours=total_watch_hours,
                avg_ctr=avg_ctr,
                avg_retention=avg_retention,
                revenue_ads=revenue_ads,
                revenue_affiliates=revenue_affiliates,
                revenue_products=revenue_products,
                revenue_sponsors=revenue_sponsors,
                notes=notes,
            )
            db.add(snapshot)
            db.commit()
            db.refresh(snapshot)
            return snapshot
        finally:
            db.close()

    def get_performance_report(self, days: int = 30) -> PerformanceReport:
        """Generate a performance report for the last N days."""
        db = get_db()
        try:
            cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)

            # Get video stats
            videos = (
                db.query(Video)
                .filter(Video.status == VideoStatus.PUBLISHED)
                .all()
            )

            total_views = sum(v.views for v in videos)
            avg_ctr = sum(v.ctr for v in videos) / len(videos) if videos else 0
            avg_retention = sum(v.retention_rate for v in videos) / len(videos) if videos else 0

            # Top and worst performing
            sorted_by_views = sorted(videos, key=lambda v: v.views, reverse=True)
            top_videos = [
                {"id": v.id, "title": v.title, "views": v.views, "ctr": v.ctr}
                for v in sorted_by_views[:5]
            ]
            worst_videos = [
                {"id": v.id, "title": v.title, "views": v.views, "ctr": v.ctr}
                for v in sorted_by_views[-3:]
            ] if len(sorted_by_views) >= 3 else []

            # Revenue from snapshots
            snapshots = (
                db.query(AnalyticsSnapshot)
                .filter(AnalyticsSnapshot.date >= cutoff)
                .all()
            )
            total_revenue = sum(
                s.revenue_ads + s.revenue_affiliates + s.revenue_products + s.revenue_sponsors
                for s in snapshots
            )

            # Growth rate
            if len(snapshots) >= 2:
                first = snapshots[0].total_subscribers
                last = snapshots[-1].total_subscribers
                growth_rate = ((last - first) / first * 100) if first > 0 else 0
            else:
                growth_rate = 0.0

            # Generate recommendations
            recommendations = self._generate_recommendations(
                avg_ctr, avg_retention, top_videos, worst_videos
            )

            return PerformanceReport(
                total_videos=len(videos),
                total_views=total_views,
                avg_ctr=avg_ctr,
                avg_retention=avg_retention,
                top_videos=top_videos,
                worst_videos=worst_videos,
                total_revenue=total_revenue,
                growth_rate=growth_rate,
                recommendations=recommendations,
            )
        finally:
            db.close()

    def update_video_stats(
        self,
        video_id: int,
        views: int | None = None,
        likes: int | None = None,
        comments_count: int | None = None,
        ctr: float | None = None,
        avg_view_duration: float | None = None,
        retention_rate: float | None = None,
    ):
        """Update analytics for a specific video."""
        db = get_db()
        try:
            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                raise ValueError(f"Video {video_id} not found")

            if views is not None:
                video.views = views
            if likes is not None:
                video.likes = likes
            if comments_count is not None:
                video.comments_count = comments_count
            if ctr is not None:
                video.ctr = ctr
            if avg_view_duration is not None:
                video.avg_view_duration = avg_view_duration
            if retention_rate is not None:
                video.retention_rate = retention_rate

            db.commit()
        finally:
            db.close()

    def get_content_pillar_performance(self) -> list[dict]:
        """Analyze performance by content pillar."""
        db = get_db()
        try:
            results = (
                db.query(
                    Video.pillar,
                    func.count(Video.id).label("count"),
                    func.avg(Video.views).label("avg_views"),
                    func.avg(Video.ctr).label("avg_ctr"),
                    func.avg(Video.retention_rate).label("avg_retention"),
                )
                .filter(Video.status == VideoStatus.PUBLISHED)
                .group_by(Video.pillar)
                .all()
            )

            return [
                {
                    "pillar": r[0].value if r[0] else "unknown",
                    "video_count": r[1],
                    "avg_views": round(r[2] or 0, 0),
                    "avg_ctr": round(r[3] or 0, 2),
                    "avg_retention": round(r[4] or 0, 2),
                }
                for r in results
            ]
        finally:
            db.close()

    def flag_underperformers(self, ctr_threshold: float = 3.0, retention_threshold: float = 30.0) -> list[dict]:
        """Flag videos that are underperforming."""
        db = get_db()
        try:
            videos = (
                db.query(Video)
                .filter(
                    Video.status == VideoStatus.PUBLISHED,
                    ((Video.ctr < ctr_threshold) & (Video.ctr > 0))
                    | ((Video.retention_rate < retention_threshold) & (Video.retention_rate > 0)),
                )
                .all()
            )

            return [
                {
                    "id": v.id,
                    "title": v.title,
                    "ctr": v.ctr,
                    "retention": v.retention_rate,
                    "views": v.views,
                    "issues": [
                        issue
                        for issue in [
                            f"Low CTR ({v.ctr}%)" if v.ctr < ctr_threshold and v.ctr > 0 else None,
                            f"Low retention ({v.retention_rate}%)"
                            if v.retention_rate < retention_threshold and v.retention_rate > 0
                            else None,
                        ]
                        if issue
                    ],
                }
                for v in videos
            ]
        finally:
            db.close()

    def _generate_recommendations(
        self,
        avg_ctr: float,
        avg_retention: float,
        top_videos: list[dict],
        worst_videos: list[dict],
    ) -> list[str]:
        """Generate actionable recommendations based on analytics."""
        recs = []

        if avg_ctr < 4.0:
            recs.append(
                "CTR is below 4%. Test more provocative thumbnails and titles. "
                "Try A/B testing with numbered vs. question-based titles."
            )
        elif avg_ctr > 8.0:
            recs.append(
                "CTR is excellent (>8%). Your titles and thumbnails are working well. "
                "Focus on retention optimization."
            )

        if avg_retention < 40.0:
            recs.append(
                "Retention is below 40%. Add more pattern interrupts, "
                "strengthen your hooks, and reduce filler content."
            )

        if top_videos:
            top_titles = [v["title"] for v in top_videos[:3]]
            recs.append(
                f"Your top performers are: {', '.join(top_titles)}. "
                f"Create more content in a similar style and topic."
            )

        if len(worst_videos) >= 2:
            recs.append(
                "Consider updating thumbnails and titles on your worst performers. "
                "A/B test new versions."
            )

        return recs
