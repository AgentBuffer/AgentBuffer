"""Marketing analysis generator — uses ASI:One LLM to analyze a business."""

from __future__ import annotations

import json
import logging

from openai import OpenAI

from services.head_agent.config import ASI_ONE_API_KEY, ASI_ONE_BASE_URL, ASI_ONE_MODEL
from services.shared.models import BrandKit, MarketingAnalysis

logger = logging.getLogger(__name__)

ANALYSIS_SYSTEM_PROMPT = """\
You are a senior marketing strategist AI. Given a business description, you produce a structured \
marketing analysis. You MUST respond with valid JSON matching this exact schema:

{
  "brand_name": "string",
  "industry": "string",
  "competitive_positioning": "string — 2-3 sentences on market position",
  "key_differentiators": ["string", "string", "string"],
  "target_audience_insights": "string — detailed audience analysis",
  "recommended_platforms": ["linkedin", "x", "instagram", "tiktok", "youtube"],
  "content_themes": ["string", "string", "string", "string"],
  "tone_guidelines": "string — how content should sound",
  "weekly_cadence": "string — e.g. '7 posts/week, heavy on TikTok and Instagram'"
}

Only include platforms from: linkedin, x, instagram, tiktok, youtube.
Choose 2-4 platforms that best fit the brand.
Respond ONLY with the JSON object, no markdown fences or extra text.\
"""

BRAND_EXTRACTION_PROMPT = """\
You are a brand intake assistant. Given a user's free-form business description, \
extract structured \
brand information. Respond with valid JSON matching this schema:

{
  "brand_id": "brand-new",
  "org_id": "org-new",
  "name": "string — the brand/company name",
  "tagline": "string — a short tagline (infer one if not given)",
  "voice_description": "string — brand voice/tone",
  "target_audience": "string — who they sell to",
  "color_palette": [],
  "logo_url": null,
  "sample_captions": [],
  "industry": "string — their industry"
}

If the user didn't mention something, make a reasonable inference from context.
Respond ONLY with the JSON object, no markdown fences or extra text.\
"""


def _get_client() -> OpenAI:
    return OpenAI(base_url=ASI_ONE_BASE_URL, api_key=ASI_ONE_API_KEY)


def _clean_json_response(text: str) -> str:
    """Strip markdown fences and whitespace from LLM JSON responses."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        text = "\n".join(lines)
    return text.strip()


def extract_brand_kit(user_text: str) -> BrandKit:
    """Parse free-form business description into a BrandKit using LLM."""
    client = _get_client()
    resp = client.chat.completions.create(
        model=ASI_ONE_MODEL,
        messages=[
            {"role": "system", "content": BRAND_EXTRACTION_PROMPT},
            {"role": "user", "content": user_text},
        ],
        max_tokens=1024,
    )
    raw = resp.choices[0].message.content or "{}"
    data = json.loads(_clean_json_response(raw))
    return BrandKit(**data)


def generate_marketing_analysis(brand: BrandKit, user_text: str) -> MarketingAnalysis:
    """Generate a marketing analysis for the given brand."""
    client = _get_client()
    context = (
        f"Business description from user: {user_text}\n\n"
        f"Extracted brand info:\n"
        f"- Name: {brand.name}\n"
        f"- Industry: {brand.industry}\n"
        f"- Tagline: {brand.tagline}\n"
        f"- Voice: {brand.voice_description}\n"
        f"- Target Audience: {brand.target_audience}\n"
    )
    resp = client.chat.completions.create(
        model=ASI_ONE_MODEL,
        messages=[
            {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
            {"role": "user", "content": context},
        ],
        max_tokens=2048,
    )
    raw = resp.choices[0].message.content or "{}"
    data = json.loads(_clean_json_response(raw))
    return MarketingAnalysis(**data)
