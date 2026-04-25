"""File organization system — auto-creates the production folder structure."""

from pathlib import Path

from youtube_automation.config import settings

FOLDER_STRUCTURE = {
    "01_Scripts": ["Drafts", "Ready_for_Production", "Published"],
    "02_Voiceovers": ["Raw_Generations", "Final_Versions"],
    "03_Visuals": [
        "Stock_Footage_Library/People_Conversations",
        "Stock_Footage_Library/Body_Language",
        "Stock_Footage_Library/Brain_Science",
        "Stock_Footage_Library/Dark_Moody",
        "Stock_Footage_Library/Business_Office",
        "Stock_Footage_Library/Relationships",
        "Stock_Footage_Library/Abstract_Concepts",
        "Stock_Footage_Library/Nature_Cinematic",
        "AI_Generated_Images",
        "Thumbnails/Templates",
        "Thumbnails/Final",
        "Animations",
    ],
    "04_Projects": ["CapCut_Templates", "Exports"],
    "05_Shorts": ["TikTok", "YouTube_Shorts", "Instagram_Reels", "Templates"],
    "06_Music_SFX": [
        "Background_Music/Ambient_Tension",
        "Background_Music/Cinematic_Minimal",
        "Background_Music/Dark_Electronic",
        "Sound_Effects/Transitions",
        "Sound_Effects/Impacts",
        "Sound_Effects/Tension",
        "Sound_Effects/UI_Sounds",
    ],
    "07_Branding": ["Logos", "Color_Palette", "Fonts", "Intro_Animation", "End_Screen_Template"],
    "08_Analytics": ["Monthly_Reports"],
    "09_Business": ["Affiliate_Links", "Sponsor_Kit", "Digital_Products", "Email_Sequences"],
}


class FileOrganizer:
    """Create and manage the production file system."""

    def __init__(self, base_dir: str | Path | None = None):
        self.base_dir = Path(base_dir) if base_dir else Path(settings.content_dir)

    def setup(self) -> list[str]:
        """Create the entire folder structure. Returns list of created directories."""
        created = []

        for category, subfolders in FOLDER_STRUCTURE.items():
            category_path = self.base_dir / category
            category_path.mkdir(parents=True, exist_ok=True)
            created.append(str(category_path))

            for subfolder in subfolders:
                sub_path = category_path / subfolder
                sub_path.mkdir(parents=True, exist_ok=True)
                created.append(str(sub_path))

        # Create template files
        self._create_templates()

        return created

    def create_video_project(self, video_number: int, title: str) -> dict:
        """Create a project folder for a specific video."""
        safe_title = "".join(c if c.isalnum() or c in " _-" else "" for c in title)
        safe_title = safe_title.replace(" ", "_")[:50]
        folder_name = f"Video_{video_number:03d}_{safe_title}"

        project_dir = self.base_dir / "04_Projects" / folder_name

        subdirs = {
            "script": project_dir / "script",
            "voiceover": project_dir / "voiceover",
            "visuals": project_dir / "visuals",
            "thumbnail": project_dir / "thumbnail",
            "shorts": project_dir / "shorts",
            "export": project_dir / "export",
        }

        for d in subdirs.values():
            d.mkdir(parents=True, exist_ok=True)

        return {name: str(path) for name, path in subdirs.items()}

    def get_project_path(self, video_number: int) -> Path | None:
        """Find project folder for a video number."""
        projects_dir = self.base_dir / "04_Projects"
        prefix = f"Video_{video_number:03d}_"

        for d in projects_dir.iterdir():
            if d.is_dir() and d.name.startswith(prefix):
                return d

        return None

    def _create_templates(self):
        """Create template files for scripts, trackers, etc."""
        # Script template
        script_template = self.base_dir / "01_Scripts" / "Script_Template.md"
        if not script_template.exists():
            script_template.write_text(
                "# VIDEO TITLE: _______________\n"
                "# TARGET LENGTH: ___ minutes\n"
                "# PILLAR: (Dark Psych / Body Language / Cognitive Bias / "
                "Relationships / Social Skills)\n\n"
                "## [HOOK — 0:00–0:03]\n"
                '> "___"\n'
                "**VISUALS**: ___\n\n"
                "## [CONTEXT — 0:03–0:30]\n"
                '> "___"\n'
                "**VISUALS**: ___\n\n"
                "## [PREVIEW — 0:30–0:50]\n"
                '> "By the end of this video..."\n'
                "**VISUALS**: ___\n\n"
                "## [POINT #1 — TITLE: ___]\n"
                '> "___"\n'
                "**VISUALS**: ___\n\n"
                "## [PATTERN INTERRUPT]\n"
                '> "But here\'s where it gets interesting..."\n\n'
                "## [CTA]\n"
                '> "If this opened your eyes, subscribe..."\n\n'
                "## [LOOP]\n"
                '> "But the most [adjective] part is..."\n'
                "→ Links to: [NEXT VIDEO TITLE]\n"
            )

        # Analytics tracker template
        tracker = self.base_dir / "08_Analytics" / "Performance_Tracker.csv"
        if not tracker.exists():
            tracker.write_text(
                "Video #,Title,Published Date,Views (7d),Views (30d),CTR %,"
                "Avg Retention %,Likes,Comments,Subs Gained,Revenue ($)\n"
            )

        # Revenue tracker
        revenue = self.base_dir / "09_Business" / "Revenue_Tracker.csv"
        if not revenue.exists():
            revenue.write_text(
                "Month,Ad Revenue,Affiliate Revenue,Product Revenue,"
                "Sponsor Revenue,Total,Notes\n"
            )

    def get_stats(self) -> dict:
        """Get file system statistics."""
        total_files = 0
        total_size = 0
        category_stats = {}

        for category_dir in self.base_dir.iterdir():
            if category_dir.is_dir():
                files = list(category_dir.rglob("*"))
                file_count = sum(1 for f in files if f.is_file())
                size = sum(f.stat().st_size for f in files if f.is_file())
                total_files += file_count
                total_size += size
                category_stats[category_dir.name] = {
                    "files": file_count,
                    "size_mb": round(size / (1024 * 1024), 2),
                }

        return {
            "total_files": total_files,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "categories": category_stats,
        }
