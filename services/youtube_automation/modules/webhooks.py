"""Webhook endpoints for Make.com/Zapier automation integration."""

import datetime
import hashlib
import hmac
from dataclasses import dataclass

from youtube_automation.config import settings
from youtube_automation.database import Short, ShortStatus, Video, VideoStatus, get_db


@dataclass
class WebhookEvent:
    event_type: str
    payload: dict
    timestamp: str
    source: str


class WebhookHandler:
    """Handle incoming and outgoing webhooks for automation platforms."""

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature from Make.com/Zapier."""
        if not settings.webhook_secret:
            return True  # Skip verification if no secret configured
        expected = hmac.new(
            settings.webhook_secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def handle_event(self, event: WebhookEvent) -> dict:
        """Route and process incoming webhook events."""
        handlers = {
            "script_ready": self._handle_script_ready,
            "voiceover_complete": self._handle_voiceover_complete,
            "video_published": self._handle_video_published,
            "analytics_update": self._handle_analytics_update,
            "schedule_content": self._handle_schedule_content,
        }

        handler = handlers.get(event.event_type)
        if not handler:
            return {"error": f"Unknown event type: {event.event_type}"}

        return handler(event.payload)

    def _handle_script_ready(self, payload: dict) -> dict:
        """Process a new script being ready for production."""
        db = get_db()
        try:
            video = Video(
                title=payload.get("title", "Untitled"),
                script=payload.get("script", ""),
                hook=payload.get("hook", ""),
                visual_notes=payload.get("visual_notes", ""),
                voiceover_direction=payload.get("voiceover_direction", ""),
                status=VideoStatus.SCRIPTED,
                pillar=payload.get("pillar"),
            )
            db.add(video)
            db.commit()
            db.refresh(video)

            return {"status": "created", "video_id": video.id, "next_step": "voiceover_generation"}
        finally:
            db.close()

    def _handle_voiceover_complete(self, payload: dict) -> dict:
        """Process voiceover completion notification."""
        db = get_db()
        try:
            video_id = payload.get("video_id")
            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                return {"error": f"Video {video_id} not found"}

            video.voiceover_path = payload.get("file_path", "")
            video.status = VideoStatus.VOICEOVER_DONE
            db.commit()

            return {"status": "updated", "video_id": video_id, "next_step": "visual_assembly"}
        finally:
            db.close()

    def _handle_video_published(self, payload: dict) -> dict:
        """Process video publication notification — triggers cross-posting."""
        db = get_db()
        try:
            video_id = payload.get("video_id")
            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                return {"error": f"Video {video_id} not found"}

            video.youtube_id = payload.get("youtube_id", "")
            video.youtube_url = payload.get("youtube_url", "")
            video.status = VideoStatus.PUBLISHED
            video.published_date = datetime.datetime.utcnow()
            db.commit()

            # Create shorts tasks
            shorts_tasks = []
            for clip_type in ["hook", "best_point", "twist"]:
                short = Short(
                    video_id=video_id,
                    title=f"{video.title} - {clip_type}",
                    clip_type=clip_type,
                    status=ShortStatus.PENDING,
                )
                db.add(short)
                shorts_tasks.append(clip_type)

            db.commit()

            return {
                "status": "published",
                "video_id": video_id,
                "shorts_queued": shorts_tasks,
                "next_steps": [
                    "extract_shorts",
                    "cross_post_social",
                    "send_email_notification",
                ],
            }
        finally:
            db.close()

    def _handle_analytics_update(self, payload: dict) -> dict:
        """Process analytics data from YouTube API."""
        db = get_db()
        try:
            video_id = payload.get("video_id")
            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                return {"error": f"Video {video_id} not found"}

            if "views" in payload:
                video.views = payload["views"]
            if "likes" in payload:
                video.likes = payload["likes"]
            if "comments" in payload:
                video.comments_count = payload["comments"]
            if "ctr" in payload:
                video.ctr = payload["ctr"]
            if "retention" in payload:
                video.retention_rate = payload["retention"]

            db.commit()
            return {"status": "updated", "video_id": video_id}
        finally:
            db.close()

    def _handle_schedule_content(self, payload: dict) -> dict:
        """Schedule content for future publishing."""
        db = get_db()
        try:
            video_id = payload.get("video_id")
            scheduled_date = payload.get("scheduled_date")

            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                return {"error": f"Video {video_id} not found"}

            video.scheduled_date = datetime.datetime.fromisoformat(scheduled_date)
            video.status = VideoStatus.SCHEDULED
            db.commit()

            return {"status": "scheduled", "video_id": video_id, "date": scheduled_date}
        finally:
            db.close()

    @staticmethod
    def generate_outgoing_payload(event_type: str, data: dict) -> dict:
        """Generate a payload for sending to external webhooks (Make.com/Zapier)."""
        return {
            "event": event_type,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "source": "youtube_automation",
            "data": data,
        }
