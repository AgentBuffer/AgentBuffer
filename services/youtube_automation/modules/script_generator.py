"""AI-powered script generator for YouTube videos."""

import json
from dataclasses import dataclass

from openai import OpenAI

from youtube_automation.config import settings

SCRIPT_SYSTEM_PROMPT = """\
You are an expert YouTube scriptwriter specializing in dark psychology,
human behavior, and self-improvement content for faceless channels.
You write scripts optimized for maximum retention with these rules:

1. HOOK (0:00-0:03): Bold claim, shocking stat, or provocative question
2. CONTEXT (0:03-0:30): Why this matters to the viewer RIGHT NOW
3. PREVIEW (0:30-1:00): "By the end of this video, you'll know exactly..."
4. BODY (1:00-7:00): Numbered list with pattern interrupts every 60-90s
5. TWIST/REVELATION (7:00-8:00): Unexpected insight or reframe
6. CTA (8:00-8:30): Subscribe prompt tied to video value
7. LOOP ENDING (8:30-9:00): Tease related content to drive next click

Pattern Interrupt Phrases (use every 90 seconds):
- "But here's where it gets really dark..."
- "Now, pay very close attention to this next one..."
- "Most people miss this completely..."

Write in a conversational, authoritative tone. Include specific research
citations (psychologist names, study details). Each point should have a
clear explanation + real-world example.

ALWAYS output valid JSON."""

SCRIPT_TEMPLATE = """Generate a complete YouTube video script for the following topic:

TITLE: {title}
CONTENT PILLAR: {pillar}
TARGET LENGTH: {target_minutes} minutes
NUMBER OF MAIN POINTS: {num_points}

Output JSON with this exact structure:
{{
    "title": "optimized title for CTR",
    "hook": "the 0:00-0:03 hook line",
    "script": {{
        "hook": {{
            "timestamp": "0:00-0:03",
            "narration": "...",
            "visuals": "..."
        }},
        "context": {{
            "timestamp": "0:03-0:30",
            "narration": "...",
            "visuals": "..."
        }},
        "preview": {{
            "timestamp": "0:30-1:00",
            "narration": "...",
            "visuals": "..."
        }},
        "points": [
            {{
                "number": 1,
                "title": "point title",
                "timestamp": "1:00-2:15",
                "narration": "full narration text...",
                "visuals": "detailed visual suggestions...",
                "pattern_interrupt": "transition line to next point"
            }}
        ],
        "twist": {{
            "timestamp": "...",
            "narration": "...",
            "visuals": "..."
        }},
        "cta": {{
            "timestamp": "...",
            "narration": "...",
            "visuals": "..."
        }},
        "loop": {{
            "timestamp": "...",
            "narration": "...",
            "next_video_tease": "..."
        }}
    }},
    "voiceover_direction": "voice style and pacing notes",
    "seo_tags": ["tag1", "tag2", "..."],
    "description": "YouTube description with timestamps"
}}"""


@dataclass
class GeneratedScript:
    title: str
    hook: str
    full_script: dict
    voiceover_direction: str
    seo_tags: list[str]
    description: str
    raw_narration: str


class ScriptGenerator:
    """Generate video scripts using OpenAI."""

    def __init__(self, api_key: str | None = None):
        self.client = OpenAI(api_key=api_key or settings.openai_api_key)

    def generate(
        self,
        title: str,
        pillar: str = "dark_psychology",
        target_minutes: int = 10,
        num_points: int = 7,
    ) -> GeneratedScript:
        """Generate a full video script from a title/topic."""
        prompt = SCRIPT_TEMPLATE.format(
            title=title,
            pillar=pillar,
            target_minutes=target_minutes,
            num_points=num_points,
        )

        response = self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SCRIPT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=4000,
            response_format={"type": "json_object"},
        )

        data = json.loads(response.choices[0].message.content)
        narration = self._extract_narration(data)

        return GeneratedScript(
            title=data.get("title", title),
            hook=data.get("hook", ""),
            full_script=data.get("script", {}),
            voiceover_direction=data.get("voiceover_direction", ""),
            seo_tags=data.get("seo_tags", []),
            description=data.get("description", ""),
            raw_narration=narration,
        )

    def generate_titles(self, topic: str, count: int = 10) -> list[str]:
        """Generate CTR-optimized title variants for a topic."""
        response = self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You generate viral YouTube titles for dark psychology and human behavior "
                        "content. Titles must be curiosity-driven, use numbers when possible, and "
                        "create an information gap. Output valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Generate {count} YouTube title variants for this topic: {topic}\n\n"
                        f'Output JSON: {{"titles": ["title1", "title2", ...]}}'
                    ),
                },
            ],
            temperature=0.9,
            response_format={"type": "json_object"},
        )

        data = json.loads(response.choices[0].message.content)
        return data.get("titles", [])

    def generate_video_ideas(self, count: int = 30, pillar: str | None = None) -> list[dict]:
        """Generate video ideas with hooks."""
        pillar_text = f" focused on {pillar}" if pillar else ""
        response = self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You generate viral video ideas for a dark psychology / human behavior "
                        "YouTube channel. Each idea must have a title, hook, and content outline. "
                        "Output valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Generate {count} video ideas{pillar_text} for a faceless dark psychology "
                        f"YouTube channel.\n\nOutput JSON:\n"
                        f'{{"ideas": [{{"title": "...", "hook": "...", "pillar": "...", '
                        f'"outline": "brief 2-3 sentence outline", '
                        f'"viral_score": 1-10}}]}}'
                    ),
                },
            ],
            temperature=0.9,
            max_tokens=4000,
            response_format={"type": "json_object"},
        )

        data = json.loads(response.choices[0].message.content)
        return data.get("ideas", [])

    def rewrite_hook_for_shorts(self, original_hook: str) -> list[str]:
        """Rewrite a long-form hook for short-form platforms."""
        response = self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You rewrite YouTube hooks for TikTok/Shorts format. Use these formulas:\n"
                        "1. POV format: 'POV: [scenario]'\n"
                        "2. Time constraint: '[Topic] explained in 60 seconds'\n"
                        "3. Challenge: 'Only emotionally intelligent people understand this'\n"
                        "4. Direct address: 'You're doing this right now'\n"
                        "5. Controversy: 'Unpopular opinion: [bold claim]'\n"
                        "Output valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f'Rewrite this hook for short-form: "{original_hook}"\n\n'
                        f'Output JSON: {{"hooks": ["hook1", "hook2", "hook3", "hook4", "hook5"]}}'
                    ),
                },
            ],
            temperature=0.9,
            response_format={"type": "json_object"},
        )

        data = json.loads(response.choices[0].message.content)
        return data.get("hooks", [])

    def _extract_narration(self, script_data: dict) -> str:
        """Extract all narration text into a single string for voiceover."""
        parts = []
        script = script_data.get("script", {})

        for section in ["hook", "context", "preview"]:
            if section in script:
                parts.append(script[section].get("narration", ""))

        for point in script.get("points", []):
            parts.append(point.get("narration", ""))
            if point.get("pattern_interrupt"):
                parts.append(point["pattern_interrupt"])

        for section in ["twist", "cta", "loop"]:
            if section in script:
                parts.append(script[section].get("narration", ""))

        return "\n\n".join(p for p in parts if p)
