"""Content slot endpoints — stubbed with mock data."""

from __future__ import annotations

from fastapi import APIRouter

from gateway.auth import OrgId

router = APIRouter(prefix="/api", tags=["slots"])

MOCK_SLOTS = [
    {
        "slot_id": "slot-001",
        "slot_number": 1,
        "caption": (
            "Every morning deserves a moment of ritual. Our single-origin "
            "Ethiopian pour-over brings you there."
        ),
        "image_prompt": (
            "Artisan coffee pour-over in warm morning light, steam rising, "
            "minimalist cafe aesthetic"
        ),
        "platform": "linkedin",
        "scheduled_for": "2026-04-28T09:00:00Z",
        "image_url": None,
        "status": "approved",
        "critic_scores": [
            {
                "axis": "Brand Voice Alignment",
                "score": 4.5,
                "reasoning": "Perfectly captures lumen's warm, artisan tone",
            },
            {
                "axis": "Visual Coherence",
                "score": 4.0,
                "reasoning": "Pour-over imagery aligns with brand aesthetic",
            },
            {
                "axis": "Platform Fit",
                "score": 4.2,
                "reasoning": "Professional tone suitable for LinkedIn",
            },
            {
                "axis": "Audience Relevance",
                "score": 4.3,
                "reasoning": "Appeals to specialty coffee enthusiasts",
            },
            {"axis": "Originality", "score": 4.0, "reasoning": "Ritual angle is fresh"},
        ],
        "critic_average": 4.2,
        "critic_summary": "Strong brand alignment with engaging ritual narrative.",
    },
    {
        "slot_id": "slot-002",
        "slot_number": 2,
        "caption": (
            "Behind the beans: Our roaster Marco shares why he chose a light "
            "roast for this week's blend. Thread below."
        ),
        "image_prompt": (
            "Coffee roaster working with beans in artisan roastery, warm industrial lighting"
        ),
        "platform": "x",
        "scheduled_for": "2026-04-28T12:00:00Z",
        "image_url": None,
        "status": "approved",
        "critic_scores": [
            {
                "axis": "Brand Voice Alignment",
                "score": 3.8,
                "reasoning": "Good behind-the-scenes approach",
            },
            {"axis": "Visual Coherence", "score": 3.9, "reasoning": "Roastery setting fits brand"},
            {"axis": "Platform Fit", "score": 4.0, "reasoning": "Thread format works well on X"},
            {"axis": "Audience Relevance", "score": 3.7, "reasoning": "Niche but engaged audience"},
            {
                "axis": "Originality",
                "score": 3.6,
                "reasoning": "Behind-the-scenes is common but executed well",
            },
        ],
        "critic_average": 3.8,
        "critic_summary": "Solid behind-the-scenes content with good platform fit.",
    },
    {
        "slot_id": "slot-003",
        "slot_number": 3,
        "caption": (
            "Start your day right with great coffee! Buy now and get 10% off! #coffee #morning"
        ),
        "image_prompt": "Generic coffee cup on white background with sale text overlay",
        "platform": "instagram",
        "scheduled_for": "2026-04-29T08:00:00Z",
        "image_url": None,
        "status": "rejected",
        "critic_scores": [
            {
                "axis": "Brand Voice Alignment",
                "score": 3.0,
                "reasoning": "Too salesy, doesn't match lumen's artisan positioning",
            },
            {
                "axis": "Visual Coherence",
                "score": 2.8,
                "reasoning": "Generic stock-photo feel contradicts brand aesthetic",
            },
            {"axis": "Platform Fit", "score": 3.5, "reasoning": "IG-appropriate but hashtag-heavy"},
            {
                "axis": "Audience Relevance",
                "score": 3.4,
                "reasoning": "Discount angle undercuts premium positioning",
            },
            {
                "axis": "Originality",
                "score": 3.3,
                "reasoning": "Very generic, could be any coffee brand",
            },
        ],
        "critic_average": 3.2,
        "critic_summary": (
            "Caption is too generic and salesy. Doesn't reflect lumen's artisan positioning."
        ),
    },
]


@router.get("/slots")
async def list_slots(org_id: OrgId) -> list[dict]:
    """Return all content slots for the authenticated org."""
    return MOCK_SLOTS


@router.post("/slots/{slot_id}/regenerate")
async def regenerate_slot(slot_id: str, org_id: OrgId) -> dict:
    """Regenerate a rejected slot with Critic feedback.

    Stub: returns the same slot with status changed to 'proposed' and bumped scores.
    Real implementation: call Strategist + Critic in sequence.
    """
    for slot in MOCK_SLOTS:
        if slot["slot_id"] == slot_id:
            regenerated = {**slot, "status": "proposed"}
            regenerated["critic_scores"] = [
                {**s, "score": min(s["score"] + 0.5, 5.0)} for s in slot["critic_scores"]
            ]
            regenerated["critic_average"] = round(
                sum(s["score"] for s in regenerated["critic_scores"])
                / len(regenerated["critic_scores"]),
                2,
            )
            regenerated["critic_summary"] = "Regenerated — improved version pending final review."
            return regenerated

    return {"error": f"Slot {slot_id} not found"}
