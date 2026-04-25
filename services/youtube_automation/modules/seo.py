"""SEO optimization module for YouTube content."""

import json
from dataclasses import dataclass

from openai import OpenAI

from youtube_automation.config import settings


@dataclass
class SEOResult:
    title: str
    description: str
    tags: list[str]
    hashtags: list[str]
    timestamps: list[dict]


DESCRIPTION_TEMPLATE = """{hook_line}
Subscribe for weekly psychology breakdowns: {{channel_link}}

{body_description}

{timestamps_section}

Related Videos:
{related_videos}

📚 Sources & Further Reading:
{sources}

{affiliate_section}

#psychology #darkpsychology #manipulation #bodylanguage #selfimprovement #humanpsychology

DISCLAIMER: This video is for educational purposes only.
If you are experiencing manipulation or emotional abuse,
please seek professional help."""


class SEOOptimizer:
    """Optimize video metadata for YouTube search and discovery."""

    def __init__(self, api_key: str | None = None):
        self.client = OpenAI(api_key=api_key or settings.openai_api_key)

    def optimize(
        self,
        title: str,
        script: str,
        points: list[str] | None = None,
    ) -> SEOResult:
        """Generate full SEO-optimized metadata for a video."""
        response = self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a YouTube SEO expert. Generate optimized metadata for "
                        "dark psychology / human behavior videos. Focus on high-search-volume "
                        "keywords, curiosity-driven descriptions, and comprehensive tag coverage. "
                        "Output valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Optimize SEO for this video:\n\n"
                        f"Title: {title}\n\n"
                        f"Script excerpt: {script[:1500]}\n\n"
                        f"Points covered: {json.dumps(points or [])}\n\n"
                        f"Generate JSON:\n"
                        f'{{"title_variants": ["title1", "title2", "title3"],'
                        f'"description": "full YouTube description with timestamps",'
                        f'"tags": ["tag1", "tag2", ...],'
                        f'"hashtags": ["#tag1", "#tag2", ...],'
                        f'"timestamps": [{{"time": "0:00", "label": "..."}}]}}'
                    ),
                },
            ],
            temperature=0.5,
            response_format={"type": "json_object"},
        )

        data = json.loads(response.choices[0].message.content)

        return SEOResult(
            title=data.get("title_variants", [title])[0],
            description=data.get("description", ""),
            tags=data.get("tags", []),
            hashtags=data.get("hashtags", []),
            timestamps=data.get("timestamps", []),
        )

    def generate_description(
        self,
        title: str,
        points: list[str],
        timestamps: list[dict] | None = None,
        affiliate_links: list[dict] | None = None,
        related_videos: list[dict] | None = None,
    ) -> str:
        """Generate a formatted YouTube description."""
        # Timestamps section
        ts_section = ""
        if timestamps:
            ts_lines = [f"{t['time']} — {t['label']}" for t in timestamps]
            ts_section = "⏱ Timestamps:\n" + "\n".join(ts_lines)

        # Points summary
        points_text = "\n".join(f"✦ {p}" for p in points)

        # Related videos
        related_text = ""
        if related_videos:
            related_text = "\n".join(
                f"► {v['title']}: {v.get('url', '[link]')}" for v in related_videos
            )

        # Affiliates
        affiliate_text = ""
        if affiliate_links:
            affiliate_text = "📖 Books & Resources (affiliate links):\n" + "\n".join(
                f"- {a['name']}: {a['url']}" for a in affiliate_links
            )

        description = f"""{title}
Subscribe for weekly psychology breakdowns 🧠

In this video, you'll learn:
{points_text}

{ts_section}

{f"Related Videos:{chr(10)}{related_text}" if related_text else ""}

{affiliate_text}

#psychology #darkpsychology #manipulation #bodylanguage #selfimprovement

DISCLAIMER: This video is for educational purposes only."""

        return description.strip()

    def generate_tags(self, title: str, description: str, max_tags: int = 30) -> list[str]:
        """Generate optimized tags for a video."""
        response = self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Generate YouTube tags. Include: primary keywords (5-7), "
                        "secondary keywords (8-12), long-tail keywords (5-8). "
                        "Focus on search volume and relevance. Output valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Title: {title}\nDescription: {description[:500]}\n\n"
                        f"Generate {max_tags} tags as JSON: "
                        f'{{"tags": ["tag1", "tag2", ...]}}'
                    ),
                },
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        data = json.loads(response.choices[0].message.content)
        return data.get("tags", [])[:max_tags]

    def analyze_title_ctr(self, titles: list[str]) -> list[dict]:
        """Score titles for predicted CTR potential."""
        response = self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You analyze YouTube titles for click-through-rate potential. "
                        "Score each title 1-10 and explain why. Consider: curiosity gap, "
                        "emotional trigger, specificity, number usage, power words. "
                        "Output valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Score these titles:\n"
                        + "\n".join(f"{i + 1}. {t}" for i, t in enumerate(titles))
                        + '\n\nOutput: {"scores": [{"title": "...", "score": 8, '
                        '"reason": "...", "improvement": "suggested improvement"}]}'
                    ),
                },
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        data = json.loads(response.choices[0].message.content)
        return data.get("scores", [])
