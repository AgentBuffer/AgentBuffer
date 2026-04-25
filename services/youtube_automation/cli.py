"""CLI interface for YouTube Automation System."""

import json
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table

from youtube_automation.config import settings
from youtube_automation.database import ContentPillar, Video, VideoStatus, get_db, init_db

console = Console()


@click.group()
def cli():
    """YouTube Automation System - Fully automated no-face channel production."""
    init_db()


# ── Setup ────────────────────────────────────────────────────────────────


@cli.command()
@click.option("--dir", "base_dir", default=None, help="Base directory for content files")
def setup(base_dir):
    """Initialize the project: create folders, database, and templates."""
    from youtube_automation.modules.file_organizer import FileOrganizer

    console.print(
        Panel("[bold red]YouTube Automation System[/bold red]\nInitializing...", border_style="red")
    )

    # Database
    init_db()
    console.print("[green]Database initialized[/green]")

    # File structure
    organizer = FileOrganizer(base_dir)
    created = organizer.setup()
    console.print(f"[green]Created {len(created)} directories[/green] at {organizer.base_dir}")

    console.print("\n[bold]Setup complete![/bold] Next steps:")
    console.print("  1. Copy .env.example to .env and add your API keys")
    console.print("  2. Run [bold]ytauto generate-ideas[/bold] to generate video ideas")
    console.print("  3. Run [bold]ytauto pipeline[/bold] to run the full production pipeline")
    console.print("  4. Run [bold]ytauto serve[/bold] to start the web dashboard")


# ── Script Generation ────────────────────────────────────────────────────


@cli.command()
@click.argument("title")
@click.option("--pillar", default="dark_psychology", help="Content pillar")
@click.option("--minutes", default=10, help="Target video length in minutes")
@click.option("--points", default=7, help="Number of main points")
@click.option("--save/--no-save", default=True, help="Save to database")
def script(title, pillar, minutes, points, save):
    """Generate a full video script from a title."""
    from youtube_automation.modules.script_generator import ScriptGenerator

    with console.status("Generating script..."):
        gen = ScriptGenerator()
        result = gen.generate(title=title, pillar=pillar, target_minutes=minutes, num_points=points)

    console.print(
        Panel(f"[bold]{result.title}[/bold]", title="Generated Script", border_style="red")
    )
    console.print(f'\n[bold]Hook:[/bold] "{result.hook}"')
    console.print(f"\n[bold]Voiceover Direction:[/bold] {result.voiceover_direction}")
    console.print(f"\n[bold]Tags:[/bold] {', '.join(result.seo_tags[:10])}")
    console.print("\n[bold]Script Preview:[/bold]")
    console.print(
        result.raw_narration[:1000] + "..."
        if len(result.raw_narration) > 1000
        else result.raw_narration
    )

    if save:
        db = get_db()
        try:
            video = Video(
                title=result.title,
                hook=result.hook,
                script=result.raw_narration,
                visual_notes=json.dumps(result.full_script),
                voiceover_direction=result.voiceover_direction,
                tags=",".join(result.seo_tags),
                pillar=ContentPillar(pillar)
                if pillar in [e.value for e in ContentPillar]
                else None,
                status=VideoStatus.SCRIPTED,
            )
            db.add(video)
            db.commit()
            db.refresh(video)
            console.print(f"\n[green]Saved as Video #{video.id}[/green]")
        finally:
            db.close()


@cli.command("generate-ideas")
@click.option("--count", default=10, help="Number of ideas to generate")
@click.option("--pillar", default=None, help="Content pillar filter")
@click.option("--save/--no-save", default=False, help="Save ideas as video entries")
def generate_ideas(count, pillar, save):
    """Generate video ideas using AI."""
    from youtube_automation.modules.script_generator import ScriptGenerator

    with console.status(f"Generating {count} video ideas..."):
        gen = ScriptGenerator()
        ideas = gen.generate_video_ideas(count=count, pillar=pillar)

    table = Table(title=f"Generated Video Ideas ({len(ideas)})")
    table.add_column("#", style="bold")
    table.add_column("Title", style="cyan")
    table.add_column("Hook", style="italic")
    table.add_column("Pillar")
    table.add_column("Viral", justify="center")

    for i, idea in enumerate(ideas, 1):
        table.add_row(
            str(i),
            idea.get("title", ""),
            idea.get("hook", "")[:80],
            idea.get("pillar", "-"),
            f"{idea.get('viral_score', '?')}/10",
        )

    console.print(table)

    if save:
        db = get_db()
        try:
            for idea in ideas:
                video = Video(
                    title=idea.get("title", "Untitled"),
                    hook=idea.get("hook", ""),
                    pillar=ContentPillar(idea.get("pillar", "dark_psychology"))
                    if idea.get("pillar") in [e.value for e in ContentPillar]
                    else None,
                    status=VideoStatus.IDEA,
                )
                db.add(video)
            db.commit()
            console.print(f"\n[green]Saved {len(ideas)} ideas to database[/green]")
        finally:
            db.close()


# ── Voiceover ────────────────────────────────────────────────────────────


@cli.command()
@click.argument("video_id", type=int)
@click.option("--preset", default="authoritative_male", help="Voice preset")
@click.option("--output", default=None, help="Output file path")
def voiceover(video_id, preset, output):
    """Generate voiceover for a video."""
    from youtube_automation.modules.file_organizer import FileOrganizer
    from youtube_automation.modules.voiceover import VoiceoverGenerator

    db = get_db()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            console.print(f"[red]Video #{video_id} not found[/red]")
            return
        if not video.script:
            console.print(f"[red]Video #{video_id} has no script[/red]")
            return

        if not output:
            organizer = FileOrganizer()
            dirs = organizer.create_video_project(video.id, video.title)
            output = str(Path(dirs["voiceover"]) / "voiceover.mp3")

        with console.status("Generating voiceover..."):
            with VoiceoverGenerator() as gen:
                result = gen.generate(text=video.script, output_path=output, preset=preset)

        video.voiceover_path = result.audio_path
        video.status = VideoStatus.VOICEOVER_DONE
        db.commit()

        console.print("[green]Voiceover generated![/green]")
        console.print(f"  File: {result.audio_path}")
        console.print(f"  Duration: ~{result.duration_seconds:.0f}s")
        console.print(f"  Characters: {result.char_count}")
        console.print(f"  Preset: {result.preset_name}")
    finally:
        db.close()


# ── Thumbnail ────────────────────────────────────────────────────────────


@cli.command()
@click.argument("video_id", type=int)
@click.option(
    "--template",
    default="bold_text",
    type=click.Choice(["bold_text", "numbered", "warning", "split", "question"]),
)
@click.option("--scheme", default="dark_dramatic", help="Color scheme")
@click.option("--output", default=None, help="Output file path")
def thumbnail(video_id, template, scheme, output):
    """Generate a thumbnail for a video."""
    from youtube_automation.modules.file_organizer import FileOrganizer
    from youtube_automation.modules.thumbnail import ThumbnailGenerator

    db = get_db()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            console.print(f"[red]Video #{video_id} not found[/red]")
            return

        if not output:
            organizer = FileOrganizer()
            dirs = organizer.create_video_project(video.id, video.title)
            output = str(Path(dirs["thumbnail"]) / "thumbnail.png")

        gen = ThumbnailGenerator()
        result = gen.generate(
            title_text=video.title,
            output_path=output,
            template=template,
            color_scheme=scheme,
        )

        video.thumbnail_path = result.path
        db.commit()

        console.print("[green]Thumbnail generated![/green]")
        console.print(f"  File: {result.path}")
        console.print(f"  Template: {result.template_name}")
        console.print(f"  Size: {result.dimensions[0]}x{result.dimensions[1]}")
    finally:
        db.close()


# ── SEO ──────────────────────────────────────────────────────────────────


@cli.command()
@click.argument("video_id", type=int)
def seo(video_id):
    """Optimize SEO metadata for a video."""
    from youtube_automation.modules.seo import SEOOptimizer

    db = get_db()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            console.print(f"[red]Video #{video_id} not found[/red]")
            return

        with console.status("Optimizing SEO..."):
            optimizer = SEOOptimizer()
            result = optimizer.optimize(title=video.title, script=video.script or "")

        video.seo_title = result.title
        video.description = result.description
        video.tags = ",".join(result.tags)
        db.commit()

        console.print(
            Panel(f"[bold]{result.title}[/bold]", title="SEO Optimized", border_style="green")
        )
        console.print(f"\n[bold]Tags:[/bold] {', '.join(result.tags[:15])}")
        console.print(f"\n[bold]Hashtags:[/bold] {' '.join(result.hashtags[:10])}")
        console.print("\n[bold]Description Preview:[/bold]")
        console.print(result.description[:500])
    finally:
        db.close()


# ── Full Pipeline ────────────────────────────────────────────────────────


@cli.command()
@click.argument("title")
@click.option("--pillar", default="dark_psychology", help="Content pillar")
@click.option("--skip-voiceover", is_flag=True, help="Skip voiceover generation")
def pipeline(title, pillar, skip_voiceover):
    """Run the full production pipeline for a video."""
    from youtube_automation.modules.file_organizer import FileOrganizer
    from youtube_automation.modules.script_generator import ScriptGenerator
    from youtube_automation.modules.thumbnail import ThumbnailGenerator
    from youtube_automation.modules.voiceover import VoiceoverGenerator

    console.print(Panel(f"[bold red]Full Pipeline[/bold red]\n{title}", border_style="red"))

    with Progress() as progress:
        task = progress.add_task("Running pipeline...", total=5)

        # Step 1: Script
        progress.update(task, description="Generating script...")
        gen = ScriptGenerator()
        script_result = gen.generate(title=title, pillar=pillar)
        progress.advance(task)

        # Step 2: Save to DB
        progress.update(task, description="Saving to database...")
        db = get_db()
        try:
            video = Video(
                title=script_result.title,
                hook=script_result.hook,
                script=script_result.raw_narration,
                visual_notes=json.dumps(script_result.full_script),
                voiceover_direction=script_result.voiceover_direction,
                tags=",".join(script_result.seo_tags),
                pillar=ContentPillar(pillar)
                if pillar in [e.value for e in ContentPillar]
                else None,
                status=VideoStatus.SCRIPTED,
            )
            db.add(video)
            db.commit()
            db.refresh(video)
            video_id = video.id
        finally:
            db.close()
        progress.advance(task)

        # Step 3: File structure
        progress.update(task, description="Creating project folders...")
        organizer = FileOrganizer()
        organizer.setup()
        dirs = organizer.create_video_project(video_id, script_result.title)

        # Save script file
        script_path = Path(dirs["script"]) / "script.md"
        script_path.write_text(
            f"# {script_result.title}\n\n"
            f"**Hook:** {script_result.hook}\n\n"
            f"**Voice:** {script_result.voiceover_direction}\n\n---\n\n"
            f"{script_result.raw_narration}\n"
        )
        progress.advance(task)

        # Step 4: Voiceover
        if not skip_voiceover and settings.elevenlabs_api_key:
            progress.update(task, description="Generating voiceover...")
            try:
                with VoiceoverGenerator() as vo_gen:
                    vo_result = vo_gen.generate(
                        text=script_result.raw_narration,
                        output_path=Path(dirs["voiceover"]) / "voiceover.mp3",
                    )
                db = get_db()
                try:
                    v = db.query(Video).filter(Video.id == video_id).first()
                    v.voiceover_path = vo_result.audio_path
                    v.status = VideoStatus.VOICEOVER_DONE
                    db.commit()
                finally:
                    db.close()
                console.print(f"  [green]Voiceover: {vo_result.audio_path}[/green]")
            except Exception as e:
                console.print(f"  [yellow]Voiceover skipped: {e}[/yellow]")
        else:
            console.print("  [yellow]Voiceover skipped (no API key or --skip-voiceover)[/yellow]")
        progress.advance(task)

        # Step 5: Thumbnail
        progress.update(task, description="Generating thumbnail...")
        thumb_gen = ThumbnailGenerator()
        thumb_result = thumb_gen.generate(
            title_text=script_result.title,
            output_path=Path(dirs["thumbnail"]) / "thumbnail.png",
        )
        db = get_db()
        try:
            v = db.query(Video).filter(Video.id == video_id).first()
            v.thumbnail_path = thumb_result.path
            db.commit()
        finally:
            db.close()
        progress.advance(task)

    console.print("\n[bold green]Pipeline complete![/bold green]")
    console.print(f"  Video ID: {video_id}")
    console.print(f"  Title: {script_result.title}")
    console.print(f"  Script: {script_path}")
    console.print(f"  Thumbnail: {thumb_result.path}")
    console.print(f"  Project: {Path(dirs['script']).parent}")


# ── List Videos ──────────────────────────────────────────────────────────


@cli.command("list")
@click.option("--status", default=None, help="Filter by status")
@click.option("--limit", default=20, help="Max results")
def list_videos(status, limit):
    """List all videos in the system."""
    db = get_db()
    try:
        query = db.query(Video)
        if status:
            query = query.filter(Video.status == status)
        videos = query.order_by(Video.created_at.desc()).limit(limit).all()

        table = Table(title=f"Videos ({len(videos)})")
        table.add_column("ID", style="bold")
        table.add_column("Title", style="cyan", max_width=50)
        table.add_column("Status")
        table.add_column("Pillar")
        table.add_column("Views", justify="right")
        table.add_column("CTR", justify="right")

        for v in videos:
            status_style = {
                "idea": "blue",
                "scripted": "yellow",
                "voiceover_done": "magenta",
                "published": "green",
                "scheduled": "cyan",
            }.get(v.status.value if v.status else "", "white")

            table.add_row(
                str(v.id),
                v.title,
                f"[{status_style}]{v.status.value if v.status else '-'}[/{status_style}]",
                v.pillar.value if v.pillar else "-",
                str(v.views),
                f"{v.ctr:.1f}%" if v.ctr else "-",
            )

        console.print(table)
    finally:
        db.close()


# ── Calendar ─────────────────────────────────────────────────────────────


@cli.command("calendar")
@click.option("--weeks", default=4, help="Number of weeks")
def calendar(weeks):
    """Generate and display content calendar."""
    from youtube_automation.modules.calendar import ContentScheduler

    scheduler = ContentScheduler()
    entries = scheduler.generate_calendar(weeks=weeks)

    table = Table(title=f"Content Calendar ({weeks} weeks, {len(entries)} entries)")
    table.add_column("Date")
    table.add_column("Day")
    table.add_column("Type")
    table.add_column("Platform")
    table.add_column("Title")

    for e in entries[:30]:  # Show first 30
        table.add_row(
            e.date.strftime("%Y-%m-%d %H:%M"),
            e.day_of_week,
            e.content_type,
            e.platform,
            e.title,
        )

    console.print(table)
    if len(entries) > 30:
        console.print(f"  ... and {len(entries) - 30} more entries")


# ── Analytics ────────────────────────────────────────────────────────────


@cli.command()
@click.option("--days", default=30, help="Report period in days")
def analytics(days):
    """Show analytics report."""
    from youtube_automation.modules.analytics import AnalyticsTracker

    tracker = AnalyticsTracker()
    report = tracker.get_performance_report(days)

    console.print(
        Panel(
            f"[bold]Videos:[/bold] {report.total_videos}  |  "
            f"[bold]Views:[/bold] {report.total_views:,}  |  "
            f"[bold]Avg CTR:[/bold] {report.avg_ctr:.1f}%  |  "
            f"[bold]Avg Retention:[/bold] {report.avg_retention:.1f}%  |  "
            f"[bold]Revenue:[/bold] ${report.total_revenue:.2f}",
            title=f"Analytics Report (Last {days} Days)",
            border_style="green",
        )
    )

    if report.recommendations:
        console.print("\n[bold]Recommendations:[/bold]")
        for rec in report.recommendations:
            console.print(f"  → {rec}")


# ── Web Dashboard ────────────────────────────────────────────────────────


@cli.command()
@click.option("--host", default=None, help="Host address")
@click.option("--port", default=None, type=int, help="Port number")
def serve(host, port):
    """Start the web dashboard."""
    import uvicorn

    h = host or settings.dashboard_host
    p = port or settings.dashboard_port

    console.print(
        Panel(
            f"[bold red]YouTube Automation Dashboard[/bold red]\nRunning at http://{h}:{p}",
            border_style="red",
        )
    )

    uvicorn.run(
        "youtube_automation.app:app",
        host=h,
        port=p,
        reload=settings.debug,
    )


if __name__ == "__main__":
    cli()
