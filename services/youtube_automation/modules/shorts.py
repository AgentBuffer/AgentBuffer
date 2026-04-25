"""Shorts extraction and repurposing system."""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from youtube_automation.config import settings


@dataclass
class ShortClip:
    title: str
    clip_type: str  # hook, best_point, twist, quote, listicle
    start_time: float
    end_time: float
    output_path: str
    hook: str
    duration: float


class ShortsExtractor:
    """Extract and format short-form clips from long-form videos."""

    CLIP_TYPES = {
        "hook": {"max_duration": 60, "description": "First 30-60 seconds - drives curiosity"},
        "best_point": {"max_duration": 90, "description": "Strongest single point"},
        "twist": {"max_duration": 60, "description": "Pattern interrupt + revelation"},
        "quote": {"max_duration": 30, "description": "Single powerful statement"},
        "listicle": {"max_duration": 60, "description": "Rapid-fire 3 points"},
    }

    def extract_clip(
        self,
        video_path: str | Path,
        output_path: str | Path,
        start_time: float,
        end_time: float,
        vertical: bool = True,
    ) -> str:
        """Extract a clip from a video using FFmpeg."""
        video_path = Path(video_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        duration = end_time - start_time

        if vertical:
            # Convert 16:9 to 9:16 with center crop
            filter_str = (
                "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,"
                "scale=1080:1920:flags=lanczos"
            )
        else:
            filter_str = "scale=1920:1080:flags=lanczos"

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),
            "-i", str(video_path),
            "-t", str(duration),
            "-vf", filter_str,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            str(output_path),
        ]

        subprocess.run(cmd, capture_output=True, check=True)
        return str(output_path)

    def add_captions(
        self,
        video_path: str | Path,
        output_path: str | Path,
        subtitle_file: str | Path | None = None,
        style: str = "bold_center",
    ) -> str:
        """Add captions/subtitles to a short-form video.

        If no subtitle file provided, uses auto-detection (requires whisper).
        """
        video_path = Path(video_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if subtitle_file and Path(subtitle_file).exists():
            srt_path = str(subtitle_file)
        else:
            # Generate subtitles using whisper (if available)
            srt_path = str(video_path.with_suffix(".srt"))
            self._generate_subtitles(video_path, srt_path)

        # Caption styles
        styles = {
            "bold_center": (
                "Fontsize=24,FontName=DejaVu Sans,Bold=1,"
                "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
                "Outline=3,Alignment=2,MarginV=80"
            ),
            "highlight": (
                "Fontsize=22,FontName=DejaVu Sans,Bold=1,"
                "PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,"
                "Outline=3,Alignment=2,MarginV=80"
            ),
        }

        style_str = styles.get(style, styles["bold_center"])

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", f"subtitles={srt_path}:force_style='{style_str}'",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "copy",
            str(output_path),
        ]

        subprocess.run(cmd, capture_output=True, check=True)
        return str(output_path)

    def _generate_subtitles(self, video_path: Path, output_srt: str):
        """Generate SRT subtitles (stub - integrate with Whisper or similar)."""
        # This creates a placeholder SRT file
        # In production, integrate with OpenAI Whisper or AssemblyAI
        srt_content = (
            "1\n"
            "00:00:00,000 --> 00:00:05,000\n"
            "[Auto-generated captions]\n"
            "[Integrate Whisper for production use]\n"
        )
        Path(output_srt).write_text(srt_content)

    def batch_extract(
        self,
        video_path: str | Path,
        clips: list[dict],
        output_dir: str | Path,
    ) -> list[ShortClip]:
        """Extract multiple clips from a single video.

        Each clip dict should have: title, clip_type, start_time, end_time, hook
        """
        output_dir = Path(output_dir)
        results = []

        for i, clip in enumerate(clips):
            filename = f"{clip['clip_type']}_{i + 1:02d}.mp4"
            output_path = output_dir / filename

            self.extract_clip(
                video_path=video_path,
                output_path=output_path,
                start_time=clip["start_time"],
                end_time=clip["end_time"],
            )

            results.append(ShortClip(
                title=clip["title"],
                clip_type=clip["clip_type"],
                start_time=clip["start_time"],
                end_time=clip["end_time"],
                output_path=str(output_path),
                hook=clip.get("hook", ""),
                duration=clip["end_time"] - clip["start_time"],
            ))

        return results

    def plan_clips(self, script: dict, video_duration: float) -> list[dict]:
        """Auto-plan clip extraction points from a script structure."""
        clips = []

        # Hook clip (first 30-60 seconds)
        clips.append({
            "title": "Hook clip",
            "clip_type": "hook",
            "start_time": 0,
            "end_time": min(60, video_duration * 0.1),
            "hook": "",
        })

        # Find points in script and select the best one
        points = script.get("points", [])
        if points:
            # Best point (pick the middle one as it's usually strongest)
            best_idx = len(points) // 2
            point = points[best_idx]
            # Estimate timestamp based on position
            point_start = (best_idx / len(points)) * video_duration * 0.7 + video_duration * 0.1
            clips.append({
                "title": f"Best point: {point.get('title', '')}",
                "clip_type": "best_point",
                "start_time": point_start,
                "end_time": min(point_start + 75, video_duration),
                "hook": point.get("narration", "")[:100],
            })

        # Twist clip (near the end)
        twist_start = video_duration * 0.75
        clips.append({
            "title": "Twist/Revelation",
            "clip_type": "twist",
            "start_time": twist_start,
            "end_time": min(twist_start + 45, video_duration),
            "hook": "",
        })

        return clips

    def get_posting_schedule(self) -> list[dict]:
        """Return the optimal weekly posting schedule for shorts."""
        return [
            {"day": "Monday", "platform": "tiktok", "time": "19:00", "type": "hook"},
            {"day": "Monday", "platform": "youtube_shorts", "time": "12:00", "type": "best_point"},
            {"day": "Tuesday", "platform": "instagram_reels", "time": "18:00", "type": "quote"},
            {"day": "Tuesday", "platform": "tiktok", "time": "21:00", "type": "twist"},
            {"day": "Wednesday", "platform": "youtube_shorts", "time": "15:00", "type": "listicle"},
            {"day": "Wednesday", "platform": "tiktok", "time": "19:00", "type": "best_point"},
            {"day": "Thursday", "platform": "instagram_reels", "time": "12:00", "type": "hook"},
            {"day": "Thursday", "platform": "tiktok", "time": "20:00", "type": "hook"},
            {"day": "Friday", "platform": "youtube_shorts", "time": "17:00", "type": "quote"},
            {"day": "Friday", "platform": "tiktok", "time": "19:00", "type": "best_point"},
            {"day": "Saturday", "platform": "all", "time": "14:00", "type": "trending"},
            {"day": "Sunday", "platform": "all", "time": "16:00", "type": "repost_best"},
        ]
