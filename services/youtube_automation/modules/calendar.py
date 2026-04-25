"""Content calendar and scheduling system."""

import datetime
from dataclasses import dataclass

from youtube_automation.database import ContentCalendar, Video, get_db


@dataclass
class ScheduleEntry:
    date: datetime.datetime
    day_of_week: str
    content_type: str
    platform: str
    video_id: int | None
    title: str
    status: str


class ContentScheduler:
    """Manage content calendar and publishing schedule."""

    # Default publishing schedule (EST)
    DEFAULT_SCHEDULE = {
        "Monday": [
            {"time": "14:00", "type": "long_form", "platform": "youtube"},
            {"time": "19:00", "type": "short", "platform": "tiktok"},
            {"time": "12:00", "type": "short", "platform": "youtube_shorts"},
        ],
        "Tuesday": [
            {"time": "18:00", "type": "short", "platform": "instagram_reels"},
            {"time": "21:00", "type": "short", "platform": "tiktok"},
        ],
        "Wednesday": [
            {"time": "15:00", "type": "long_form", "platform": "youtube"},
            {"time": "15:00", "type": "short", "platform": "youtube_shorts"},
            {"time": "19:00", "type": "short", "platform": "tiktok"},
        ],
        "Thursday": [
            {"time": "12:00", "type": "short", "platform": "instagram_reels"},
            {"time": "20:00", "type": "short", "platform": "tiktok"},
        ],
        "Friday": [
            {"time": "14:00", "type": "long_form", "platform": "youtube"},
            {"time": "17:00", "type": "short", "platform": "youtube_shorts"},
            {"time": "19:00", "type": "short", "platform": "tiktok"},
        ],
        "Saturday": [
            {"time": "14:00", "type": "short", "platform": "all"},
        ],
        "Sunday": [
            {"time": "16:00", "type": "short", "platform": "all"},
        ],
    }

    def generate_calendar(
        self,
        start_date: datetime.date | None = None,
        weeks: int = 4,
        video_ids: list[int] | None = None,
    ) -> list[ScheduleEntry]:
        """Generate a content calendar for the specified number of weeks."""
        if not start_date:
            start_date = datetime.date.today()
            # Start from next Monday
            days_until_monday = (7 - start_date.weekday()) % 7
            start_date += datetime.timedelta(days=days_until_monday)

        db = get_db()
        try:
            entries = []
            video_idx = 0
            available_videos = video_ids or []

            for week in range(weeks):
                for day_offset in range(7):
                    current_date = start_date + datetime.timedelta(days=week * 7 + day_offset)
                    day_name = current_date.strftime("%A")

                    schedule = self.DEFAULT_SCHEDULE.get(day_name, [])

                    for slot in schedule:
                        hour, minute = map(int, slot["time"].split(":"))
                        slot_datetime = datetime.datetime.combine(
                            current_date,
                            datetime.time(hour, minute),
                        )

                        vid_id = None
                        title = f"[{slot['type']}] Scheduled content"

                        if (
                            slot["type"] == "long_form"
                            and available_videos
                            and video_idx < len(available_videos)
                        ):
                            vid_id = available_videos[video_idx]
                            video = db.query(Video).filter(Video.id == vid_id).first()
                            if video:
                                title = video.title
                            video_idx += 1

                        entry = ScheduleEntry(
                            date=slot_datetime,
                            day_of_week=day_name,
                            content_type=slot["type"],
                            platform=slot["platform"],
                            video_id=vid_id,
                            title=title,
                            status="planned",
                        )
                        entries.append(entry)

                        # Save to database
                        cal_entry = ContentCalendar(
                            date=slot_datetime,
                            day_of_week=day_name,
                            content_type=slot["type"],
                            platform=slot["platform"],
                            video_id=vid_id,
                            title=title,
                            status="planned",
                        )
                        db.add(cal_entry)

            db.commit()
            return entries
        finally:
            db.close()

    def get_upcoming(self, days: int = 7) -> list[dict]:
        """Get upcoming scheduled content."""
        db = get_db()
        try:
            now = datetime.datetime.utcnow()
            end = now + datetime.timedelta(days=days)

            entries = (
                db.query(ContentCalendar)
                .filter(ContentCalendar.date >= now, ContentCalendar.date <= end)
                .order_by(ContentCalendar.date)
                .all()
            )

            return [
                {
                    "id": e.id,
                    "date": e.date.isoformat(),
                    "day": e.day_of_week,
                    "type": e.content_type,
                    "platform": e.platform,
                    "video_id": e.video_id,
                    "title": e.title,
                    "status": e.status,
                }
                for e in entries
            ]
        finally:
            db.close()

    def mark_completed(self, entry_id: int):
        """Mark a calendar entry as completed."""
        db = get_db()
        try:
            entry = db.query(ContentCalendar).filter(ContentCalendar.id == entry_id).first()
            if entry:
                entry.status = "completed"
                db.commit()
        finally:
            db.close()

    def get_weekly_summary(self) -> dict:
        """Get a summary of this week's content schedule."""
        db = get_db()
        try:
            now = datetime.datetime.utcnow()
            week_start = now - datetime.timedelta(days=now.weekday())
            week_end = week_start + datetime.timedelta(days=7)

            entries = (
                db.query(ContentCalendar)
                .filter(ContentCalendar.date >= week_start, ContentCalendar.date <= week_end)
                .all()
            )

            return {
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "total_entries": len(entries),
                "long_form": sum(1 for e in entries if e.content_type == "long_form"),
                "shorts": sum(1 for e in entries if e.content_type == "short"),
                "completed": sum(1 for e in entries if e.status == "completed"),
                "pending": sum(1 for e in entries if e.status == "planned"),
                "entries": [
                    {
                        "id": e.id,
                        "date": e.date.isoformat(),
                        "day": e.day_of_week,
                        "type": e.content_type,
                        "platform": e.platform,
                        "title": e.title,
                        "status": e.status,
                    }
                    for e in entries
                ],
            }
        finally:
            db.close()
