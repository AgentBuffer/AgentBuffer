"""FastAPI routes for the YouTube Automation dashboard and API."""

import json
import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from youtube_automation.database import (
    Video,
    VideoStatus,
    ContentPillar,
    Short,
    ShortStatus,
    ContentCalendar,
    AnalyticsSnapshot,
    get_db,
    init_db,
)
from youtube_automation.modules.script_generator import ScriptGenerator
from youtube_automation.modules.seo import SEOOptimizer
from youtube_automation.modules.thumbnail import ThumbnailGenerator
from youtube_automation.modules.voiceover import VoiceoverGenerator
from youtube_automation.modules.shorts import ShortsExtractor
from youtube_automation.modules.analytics import AnalyticsTracker
from youtube_automation.modules.calendar import ContentScheduler
from youtube_automation.modules.file_organizer import FileOrganizer
from youtube_automation.modules.webhooks import WebhookHandler, WebhookEvent
from youtube_automation.config import settings

router = APIRouter()


# ── Pydantic models ──────────────────────────────────────────────────────

class VideoCreate(BaseModel):
    title: str
    pillar: str | None = None
    hook: str | None = None
    script: str | None = None


class VideoUpdate(BaseModel):
    title: str | None = None
    status: str | None = None
    hook: str | None = None
    script: str | None = None
    description: str | None = None
    tags: str | None = None


class GenerateScriptRequest(BaseModel):
    title: str
    pillar: str = "dark_psychology"
    target_minutes: int = 10
    num_points: int = 7


class GenerateVoiceoverRequest(BaseModel):
    video_id: int
    preset: str = "authoritative_male"


class GenerateThumbnailRequest(BaseModel):
    video_id: int
    template: str = "bold_text"
    color_scheme: str = "dark_dramatic"
    title_override: str | None = None


class GenerateIdeasRequest(BaseModel):
    count: int = 10
    pillar: str | None = None


class SEOOptimizeRequest(BaseModel):
    video_id: int


class GenerateCalendarRequest(BaseModel):
    weeks: int = 4
    video_ids: list[int] | None = None


class WebhookPayload(BaseModel):
    event_type: str
    payload: dict
    source: str = "external"


class AnalyticsUpdateRequest(BaseModel):
    video_id: int
    views: int | None = None
    likes: int | None = None
    comments_count: int | None = None
    ctr: float | None = None
    retention_rate: float | None = None


class ExtractShortsRequest(BaseModel):
    video_id: int
    video_path: str
    clips: list[dict] | None = None


# ── Dashboard (HTML) ─────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"settings": settings},
    )


@router.get("/videos", response_class=HTMLResponse)
async def videos_page(request: Request):
    """Videos management page."""
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="videos.html",
    )


@router.get("/calendar-view", response_class=HTMLResponse)
async def calendar_page(request: Request):
    """Content calendar page."""
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="calendar.html",
    )


# ── API: Videos ──────────────────────────────────────────────────────────

@router.get("/api/videos")
async def list_videos(
    status: str | None = None,
    pillar: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    """List all videos with optional filtering."""
    db = get_db()
    try:
        query = db.query(Video)
        if status:
            query = query.filter(Video.status == status)
        if pillar:
            query = query.filter(Video.pillar == pillar)

        total = query.count()
        videos = query.order_by(Video.created_at.desc()).offset(offset).limit(limit).all()

        return {
            "total": total,
            "videos": [
                {
                    "id": v.id,
                    "title": v.title,
                    "status": v.status.value if v.status else None,
                    "pillar": v.pillar.value if v.pillar else None,
                    "hook": v.hook,
                    "youtube_url": v.youtube_url,
                    "views": v.views,
                    "ctr": v.ctr,
                    "retention_rate": v.retention_rate,
                    "scheduled_date": v.scheduled_date.isoformat() if v.scheduled_date else None,
                    "published_date": v.published_date.isoformat() if v.published_date else None,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                    "has_script": bool(v.script),
                    "has_voiceover": bool(v.voiceover_path),
                    "has_thumbnail": bool(v.thumbnail_path),
                }
                for v in videos
            ],
        }
    finally:
        db.close()


@router.post("/api/videos")
async def create_video(data: VideoCreate):
    """Create a new video entry."""
    db = get_db()
    try:
        video = Video(
            title=data.title,
            pillar=ContentPillar(data.pillar) if data.pillar else None,
            hook=data.hook,
            script=data.script,
            status=VideoStatus.SCRIPTED if data.script else VideoStatus.IDEA,
        )
        db.add(video)
        db.commit()
        db.refresh(video)
        return {"id": video.id, "title": video.title, "status": video.status.value}
    finally:
        db.close()


@router.get("/api/videos/{video_id}")
async def get_video(video_id: int):
    """Get full video details."""
    db = get_db()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        shorts = [
            {
                "id": s.id,
                "title": s.title,
                "clip_type": s.clip_type,
                "status": s.status.value if s.status else None,
                "file_path": s.file_path,
            }
            for s in video.shorts
        ]

        return {
            "id": video.id,
            "title": video.title,
            "status": video.status.value if video.status else None,
            "pillar": video.pillar.value if video.pillar else None,
            "hook": video.hook,
            "script": video.script,
            "visual_notes": video.visual_notes,
            "voiceover_direction": video.voiceover_direction,
            "description": video.description,
            "tags": video.tags,
            "voiceover_path": video.voiceover_path,
            "thumbnail_path": video.thumbnail_path,
            "video_path": video.video_path,
            "youtube_id": video.youtube_id,
            "youtube_url": video.youtube_url,
            "views": video.views,
            "likes": video.likes,
            "ctr": video.ctr,
            "retention_rate": video.retention_rate,
            "scheduled_date": video.scheduled_date.isoformat() if video.scheduled_date else None,
            "published_date": video.published_date.isoformat() if video.published_date else None,
            "shorts": shorts,
        }
    finally:
        db.close()


@router.patch("/api/videos/{video_id}")
async def update_video(video_id: int, data: VideoUpdate):
    """Update video metadata."""
    db = get_db()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        if data.title is not None:
            video.title = data.title
        if data.status is not None:
            video.status = VideoStatus(data.status)
        if data.hook is not None:
            video.hook = data.hook
        if data.script is not None:
            video.script = data.script
        if data.description is not None:
            video.description = data.description
        if data.tags is not None:
            video.tags = data.tags

        video.updated_at = datetime.datetime.utcnow()
        db.commit()

        return {"id": video.id, "status": video.status.value, "updated": True}
    finally:
        db.close()


@router.delete("/api/videos/{video_id}")
async def delete_video(video_id: int):
    """Delete a video entry."""
    db = get_db()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        db.delete(video)
        db.commit()
        return {"deleted": True}
    finally:
        db.close()


# ── API: Script Generation ───────────────────────────────────────────────

@router.post("/api/generate/script")
async def generate_script(data: GenerateScriptRequest):
    """Generate a full video script using AI."""
    try:
        generator = ScriptGenerator()
        result = generator.generate(
            title=data.title,
            pillar=data.pillar,
            target_minutes=data.target_minutes,
            num_points=data.num_points,
        )

        # Save to database
        db = get_db()
        try:
            video = Video(
                title=result.title,
                hook=result.hook,
                script=result.raw_narration,
                visual_notes=json.dumps(result.full_script),
                voiceover_direction=result.voiceover_direction,
                description=result.description,
                tags=",".join(result.seo_tags),
                pillar=ContentPillar(data.pillar) if data.pillar in [e.value for e in ContentPillar] else None,
                status=VideoStatus.SCRIPTED,
            )
            db.add(video)
            db.commit()
            db.refresh(video)

            return {
                "video_id": video.id,
                "title": result.title,
                "hook": result.hook,
                "script": result.full_script,
                "narration": result.raw_narration,
                "voiceover_direction": result.voiceover_direction,
                "seo_tags": result.seo_tags,
            }
        finally:
            db.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/generate/ideas")
async def generate_ideas(data: GenerateIdeasRequest):
    """Generate video ideas using AI."""
    try:
        generator = ScriptGenerator()
        ideas = generator.generate_video_ideas(count=data.count, pillar=data.pillar)
        return {"ideas": ideas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/generate/titles")
async def generate_titles(topic: str, count: int = 10):
    """Generate CTR-optimized title variants."""
    try:
        generator = ScriptGenerator()
        titles = generator.generate_titles(topic, count)
        return {"titles": titles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── API: Voiceover ───────────────────────────────────────────────────────

@router.post("/api/generate/voiceover")
async def generate_voiceover(data: GenerateVoiceoverRequest):
    """Generate voiceover for a video script."""
    db = get_db()
    try:
        video = db.query(Video).filter(Video.id == data.video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        if not video.script:
            raise HTTPException(status_code=400, detail="Video has no script")

        organizer = FileOrganizer()
        project_dirs = organizer.create_video_project(video.id, video.title)
        output_path = Path(project_dirs["voiceover"]) / "voiceover.mp3"

        with VoiceoverGenerator() as gen:
            result = gen.generate(
                text=video.script,
                output_path=output_path,
                preset=data.preset,
            )

        video.voiceover_path = result.audio_path
        video.status = VideoStatus.VOICEOVER_DONE
        db.commit()

        return {
            "video_id": video.id,
            "audio_path": result.audio_path,
            "duration_seconds": result.duration_seconds,
            "preset": result.preset_name,
            "characters_used": result.char_count,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/api/voiceover/voices")
async def list_voices():
    """List available ElevenLabs voices."""
    try:
        with VoiceoverGenerator() as gen:
            voices = gen.list_voices()
        return {"voices": voices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/voiceover/usage")
async def voiceover_usage():
    """Get ElevenLabs API usage."""
    try:
        with VoiceoverGenerator() as gen:
            usage = gen.get_usage()
        return usage
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── API: Thumbnails ──────────────────────────────────────────────────────

@router.post("/api/generate/thumbnail")
async def generate_thumbnail(data: GenerateThumbnailRequest):
    """Generate a thumbnail for a video."""
    db = get_db()
    try:
        video = db.query(Video).filter(Video.id == data.video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        organizer = FileOrganizer()
        project_dirs = organizer.create_video_project(video.id, video.title)
        output_path = Path(project_dirs["thumbnail"]) / "thumbnail.png"

        gen = ThumbnailGenerator()
        title_text = data.title_override or video.title
        result = gen.generate(
            title_text=title_text,
            output_path=output_path,
            template=data.template,
            color_scheme=data.color_scheme,
        )

        video.thumbnail_path = result.path
        video.status = VideoStatus.THUMBNAIL_DONE
        db.commit()

        return {
            "video_id": video.id,
            "thumbnail_path": result.path,
            "template": result.template_name,
            "dimensions": result.dimensions,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


# ── API: SEO ─────────────────────────────────────────────────────────────

@router.post("/api/seo/optimize")
async def optimize_seo(data: SEOOptimizeRequest):
    """Generate SEO-optimized metadata for a video."""
    db = get_db()
    try:
        video = db.query(Video).filter(Video.id == data.video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        optimizer = SEOOptimizer()
        result = optimizer.optimize(
            title=video.title,
            script=video.script or "",
        )

        video.seo_title = result.title
        video.description = result.description
        video.tags = ",".join(result.tags)
        db.commit()

        return {
            "video_id": video.id,
            "title": result.title,
            "description": result.description,
            "tags": result.tags,
            "hashtags": result.hashtags,
            "timestamps": result.timestamps,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/api/seo/analyze-titles")
async def analyze_titles(titles: list[str]):
    """Score titles for CTR potential."""
    try:
        optimizer = SEOOptimizer()
        scores = optimizer.analyze_title_ctr(titles)
        return {"scores": scores}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── API: Shorts ──────────────────────────────────────────────────────────

@router.post("/api/shorts/extract")
async def extract_shorts(data: ExtractShortsRequest):
    """Extract short-form clips from a long-form video."""
    db = get_db()
    try:
        video = db.query(Video).filter(Video.id == data.video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        organizer = FileOrganizer()
        project_dirs = organizer.create_video_project(video.id, video.title)

        extractor = ShortsExtractor()

        if data.clips:
            clips = data.clips
        else:
            script_data = json.loads(video.visual_notes) if video.visual_notes else {}
            clips = extractor.plan_clips(script_data, 600)  # assume 10 min

        results = extractor.batch_extract(
            video_path=data.video_path,
            clips=clips,
            output_dir=project_dirs["shorts"],
        )

        # Save to database
        for r in results:
            short = Short(
                video_id=video.id,
                title=r.title,
                clip_type=r.clip_type,
                start_time=r.start_time,
                end_time=r.end_time,
                file_path=r.output_path,
                hook=r.hook,
                status=ShortStatus.EXTRACTED,
            )
            db.add(short)
        db.commit()

        return {
            "video_id": video.id,
            "clips_extracted": len(results),
            "clips": [
                {
                    "title": r.title,
                    "type": r.clip_type,
                    "duration": r.duration,
                    "path": r.output_path,
                }
                for r in results
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/api/shorts/schedule")
async def shorts_schedule():
    """Get the optimal posting schedule for shorts."""
    extractor = ShortsExtractor()
    return {"schedule": extractor.get_posting_schedule()}


# ── API: Calendar ────────────────────────────────────────────────────────

@router.post("/api/calendar/generate")
async def generate_calendar(data: GenerateCalendarRequest):
    """Generate a content calendar."""
    scheduler = ContentScheduler()
    entries = scheduler.generate_calendar(weeks=data.weeks, video_ids=data.video_ids)
    return {
        "entries_created": len(entries),
        "entries": [
            {
                "date": e.date.isoformat(),
                "day": e.day_of_week,
                "type": e.content_type,
                "platform": e.platform,
                "title": e.title,
                "video_id": e.video_id,
            }
            for e in entries
        ],
    }


@router.get("/api/calendar/upcoming")
async def upcoming_content(days: int = 7):
    """Get upcoming scheduled content."""
    scheduler = ContentScheduler()
    return {"entries": scheduler.get_upcoming(days)}


@router.get("/api/calendar/weekly")
async def weekly_summary():
    """Get this week's content summary."""
    scheduler = ContentScheduler()
    return scheduler.get_weekly_summary()


@router.post("/api/calendar/{entry_id}/complete")
async def complete_calendar_entry(entry_id: int):
    """Mark a calendar entry as completed."""
    scheduler = ContentScheduler()
    scheduler.mark_completed(entry_id)
    return {"completed": True}


# ── API: Analytics ───────────────────────────────────────────────────────

@router.get("/api/analytics/report")
async def analytics_report(days: int = 30):
    """Get performance report."""
    tracker = AnalyticsTracker()
    report = tracker.get_performance_report(days)
    return {
        "total_videos": report.total_videos,
        "total_views": report.total_views,
        "avg_ctr": report.avg_ctr,
        "avg_retention": report.avg_retention,
        "total_revenue": report.total_revenue,
        "growth_rate": report.growth_rate,
        "top_videos": report.top_videos,
        "worst_videos": report.worst_videos,
        "recommendations": report.recommendations,
    }


@router.post("/api/analytics/update")
async def update_analytics(data: AnalyticsUpdateRequest):
    """Update video analytics."""
    tracker = AnalyticsTracker()
    tracker.update_video_stats(
        video_id=data.video_id,
        views=data.views,
        likes=data.likes,
        comments_count=data.comments_count,
        ctr=data.ctr,
        retention_rate=data.retention_rate,
    )
    return {"updated": True}


@router.get("/api/analytics/pillars")
async def pillar_performance():
    """Analyze performance by content pillar."""
    tracker = AnalyticsTracker()
    return {"pillars": tracker.get_content_pillar_performance()}


@router.get("/api/analytics/underperformers")
async def underperformers(ctr_threshold: float = 3.0, retention_threshold: float = 30.0):
    """Flag underperforming videos."""
    tracker = AnalyticsTracker()
    return {"underperformers": tracker.flag_underperformers(ctr_threshold, retention_threshold)}


# ── API: Webhooks ────────────────────────────────────────────────────────

@router.post("/api/webhooks/incoming")
async def incoming_webhook(data: WebhookPayload):
    """Handle incoming webhooks from Make.com/Zapier."""
    handler = WebhookHandler()
    event = WebhookEvent(
        event_type=data.event_type,
        payload=data.payload,
        timestamp=datetime.datetime.utcnow().isoformat(),
        source=data.source,
    )
    result = handler.handle_event(event)
    return result


# ── API: File Organization ───────────────────────────────────────────────

@router.post("/api/files/setup")
async def setup_files(base_dir: str | None = None):
    """Create the production folder structure."""
    organizer = FileOrganizer(base_dir)
    created = organizer.setup()
    return {"directories_created": len(created), "base_dir": str(organizer.base_dir)}


@router.get("/api/files/stats")
async def file_stats(base_dir: str | None = None):
    """Get file system statistics."""
    organizer = FileOrganizer(base_dir)
    return organizer.get_stats()


@router.post("/api/files/project/{video_id}")
async def create_project(video_id: int):
    """Create a project folder for a video."""
    db = get_db()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        organizer = FileOrganizer()
        dirs = organizer.create_video_project(video.id, video.title)
        video.project_path = str(Path(dirs["script"]).parent)
        db.commit()

        return {"video_id": video.id, "directories": dirs}
    finally:
        db.close()


# ── API: Pipeline (Orchestrated Workflow) ────────────────────────────────

@router.post("/api/pipeline/full")
async def run_full_pipeline(title: str, pillar: str = "dark_psychology"):
    """Run the complete production pipeline for a video.

    Steps: Generate Script → Generate Voiceover → Generate Thumbnail → SEO Optimize
    """
    results = {"steps": []}

    # Step 1: Generate script
    try:
        generator = ScriptGenerator()
        script = generator.generate(title=title, pillar=pillar)
        results["steps"].append({"step": "script", "status": "success", "title": script.title})
    except Exception as e:
        results["steps"].append({"step": "script", "status": "error", "error": str(e)})
        return results

    # Step 2: Save to database
    db = get_db()
    try:
        video = Video(
            title=script.title,
            hook=script.hook,
            script=script.raw_narration,
            visual_notes=json.dumps(script.full_script),
            voiceover_direction=script.voiceover_direction,
            tags=",".join(script.seo_tags),
            pillar=ContentPillar(pillar) if pillar in [e.value for e in ContentPillar] else None,
            status=VideoStatus.SCRIPTED,
        )
        db.add(video)
        db.commit()
        db.refresh(video)
        video_id = video.id
    finally:
        db.close()

    results["video_id"] = video_id
    results["steps"].append({"step": "save", "status": "success", "video_id": video_id})

    # Step 3: Create project folders
    organizer = FileOrganizer()
    organizer.setup()
    project_dirs = organizer.create_video_project(video_id, script.title)
    results["steps"].append({"step": "folders", "status": "success"})

    # Step 4: Generate voiceover (if ElevenLabs key available)
    if settings.elevenlabs_api_key:
        try:
            with VoiceoverGenerator() as vo_gen:
                vo_result = vo_gen.generate(
                    text=script.raw_narration,
                    output_path=Path(project_dirs["voiceover"]) / "voiceover.mp3",
                )
            db = get_db()
            try:
                v = db.query(Video).filter(Video.id == video_id).first()
                v.voiceover_path = vo_result.audio_path
                v.status = VideoStatus.VOICEOVER_DONE
                db.commit()
            finally:
                db.close()
            results["steps"].append({
                "step": "voiceover",
                "status": "success",
                "duration": vo_result.duration_seconds,
            })
        except Exception as e:
            results["steps"].append({"step": "voiceover", "status": "error", "error": str(e)})
    else:
        results["steps"].append({"step": "voiceover", "status": "skipped", "reason": "No API key"})

    # Step 5: Generate thumbnail
    try:
        thumb_gen = ThumbnailGenerator()
        thumb_result = thumb_gen.generate(
            title_text=script.title,
            output_path=Path(project_dirs["thumbnail"]) / "thumbnail.png",
            template="bold_text",
        )
        db = get_db()
        try:
            v = db.query(Video).filter(Video.id == video_id).first()
            v.thumbnail_path = thumb_result.path
            db.commit()
        finally:
            db.close()
        results["steps"].append({"step": "thumbnail", "status": "success", "path": thumb_result.path})
    except Exception as e:
        results["steps"].append({"step": "thumbnail", "status": "error", "error": str(e)})

    # Step 6: SEO optimization
    if settings.openai_api_key:
        try:
            seo = SEOOptimizer()
            seo_result = seo.optimize(title=script.title, script=script.raw_narration)
            db = get_db()
            try:
                v = db.query(Video).filter(Video.id == video_id).first()
                v.description = seo_result.description
                v.tags = ",".join(seo_result.tags)
                db.commit()
            finally:
                db.close()
            results["steps"].append({"step": "seo", "status": "success"})
        except Exception as e:
            results["steps"].append({"step": "seo", "status": "error", "error": str(e)})
    else:
        results["steps"].append({"step": "seo", "status": "skipped", "reason": "No API key"})

    # Save script to file
    script_path = Path(project_dirs["script"]) / "script.md"
    script_path.write_text(
        f"# {script.title}\n\n"
        f"**Hook:** {script.hook}\n\n"
        f"**Voiceover Direction:** {script.voiceover_direction}\n\n"
        f"---\n\n"
        f"{script.raw_narration}\n"
    )
    results["steps"].append({"step": "save_script_file", "status": "success", "path": str(script_path)})

    results["status"] = "complete"
    results["project_dir"] = str(Path(project_dirs["script"]).parent)

    return results
