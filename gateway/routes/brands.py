"""Brand endpoints — stubbed with mock data."""

from __future__ import annotations

from fastapi import APIRouter

from gateway.auth import OrgId

router = APIRouter(prefix="/api", tags=["brands"])


MOCK_BRAND = {
    "brand_id": "brand-001",
    "org_id": "org-demo-001",
    "name": "lumen.coffee",
    "tagline": "Light up your morning",
    "voice_description": (
        "Warm, artisan, approachable. We speak like a knowledgeable "
        "barista who genuinely loves their craft."
    ),
    "target_audience": "Urban professionals aged 25-40 who appreciate specialty coffee",
    "color_palette": ["#2C1810", "#D4A574", "#F5F0EB", "#8B4513"],
    "logo_url": None,
    "sample_captions": [
        (
            "Every cup tells a story. Today's single-origin from "
            "Ethiopia has notes of blueberry and dark chocolate."
        ),
        (
            "Rise and grind (literally). Our new cold brew is "
            "steeped for 18 hours for maximum smoothness."
        ),
    ],
    "industry": "Coffee & Beverage",
}


@router.get("/brands")
async def list_brands(org_id: OrgId) -> list[dict]:
    """Return brands for the authenticated org."""
    return [MOCK_BRAND]


@router.post("/brands/extract")
async def extract_brand(org_id: OrgId) -> dict:
    """Extract a BrandKit from uploaded assets and social URLs.

    Stub: returns the mock brand immediately.
    Real implementation: accept multipart/form-data, parse PDFs,
    scrape social profiles, call extract_brand_kit().
    """
    return MOCK_BRAND
