# Carousel Pipeline — Design Document

## Overview

The Carousel Creator agent extends the existing `Strategist → Critic → Publisher` pipeline with automated carousel/slideshow generation. After the Critic approves a content slate, the Carousel Creator intercepts approved Instagram and LinkedIn slots, paginates each slot's marketing message into a multi-slide narrative, renders high-quality images using Pillow, and outputs a folder of sequentially-named PNGs ready for publishing.

## Updated Agent Topology

```
                                                     ┌────────────────┐
                                                ┌───▶│CAROUSEL CREATOR│
   ┌───────────┐  proposes  ┌──────────┐  approved   │ (paginates +   │
   │STRATEGIST │ ──────────▶│  CRITIC  │ ────────┤   │  renders imgs) │
   │ (plans    │            │ (rejects │         │   └──────┬─────────┘
   │  weekly   │◀─── try ───│  ≥1 per  │         │          │ .png slides
   │  slate)   │    again   │  demo)   │         │          ▼
   └───────────┘            └──────────┘         │   ┌──────────────┐
                                                 └──▶│  PUBLISHER   │
                                                     │ (posts via   │
                                                     │  direct APIs)│
                                                     └──────┬───────┘
                                                            ▼
                                                  LinkedIn · Instagram
```

## Data Flow

### 1. Trigger: ApprovedSlate from Critic

The Critic agent outputs an `ApprovedSlate` containing:
- `Slate.slots[]` — each `ContentSlot` with `caption`, `image_prompt`, `platform`, `scheduled_for`
- `Slate.brand_id` / `Slate.org_id` — links to `BrandKit` (voice, audience, colors, industry)
- `CriticVerdict[]` — only `approved == True` slots proceed

### 2. Carousel Creator receives the ApprovedSlate

The Carousel Creator agent:
1. Filters for approved slots targeting Instagram or LinkedIn
2. Loads the `BrandKit` for the slate's `brand_id`
3. For each approved slot, calls the **Narrative Pagination Engine**

### 3. Narrative Pagination Engine

For each `(ContentSlot, BrandKit)` pair:

1. Splits `caption` into sentences using regex on sentence boundaries (`.!?`)
2. Constructs the carousel narrative:

| Slide | Type | Source |
|-------|------|--------|
| 1 | **Hook** | First sentence of caption (or `brand.tagline` fallback) |
| 2…N-1 | **Body** | Remaining sentences, word-wrapped at ≤120 chars per slide |
| N | **CTA** | Last `brand.sample_captions` entry or default CTA |

3. Enforces constraints:
   - Minimum 5 slides (pads with brand tagline / sample captions)
   - Maximum 10 slides (trims body slides, preserves hook + CTA)
   - Never splits text mid-word

### 4. Slide Rendering

For each `SlideContent`:
1. Create a 1080×1350 canvas (4:5 aspect ratio, optimal for Instagram/LinkedIn)
2. Fill background with `brand.color_palette[0]` (primary brand color)
3. Draw accent bar (top 80px) with `brand.color_palette[1]` if available
4. Place brand logo (top-right, max 120×120) if `brand.logo_url` is set
5. Render headline (bold, ~48pt, white, centered, upper third)
6. Render body text (regular, ~32pt, white, centered, middle) with word-wrap
7. Draw slide number badge (bottom-left)
8. Save as PNG to `output/carousels/{slot_id}/{slot_id}_slide_NN.png`

### 5. Handoff to Publisher

The Carousel Creator wraps all `CarouselResult`s in an `AgentEnvelope` and sends to the Publisher, which uploads to each platform via its native API.

## New Pydantic Models (added to `services/shared/models.py`)

```python
class SlideContent(BaseModel):
    slide_number: int
    slide_type: str  # "hook", "body", "cta"
    headline: str
    body: str
    speaker_notes: str = ""

class CarouselResult(BaseModel):
    slot_id: str
    platform: Platform
    slide_paths: list[str]
    output_dir: str
    status: str  # "success", "error"
    error: str | None = None
```

## File Structure

```
services/carousel_creator/
├── __init__.py
├── agent.py              # Sub-agent entry point, receives ApprovedSlate
├── pagination.py         # Narrative pagination engine
├── renderer.py           # Pillow-based 1080x1350 image renderer
├── pyproject.toml        # Dependencies: Pillow, pydantic, agentbuffer-shared
└── tests/
    ├── __init__.py
    ├── test_pagination.py
    └── test_renderer.py

docs/
└── carousel_pipeline.md  # This document
```

## Testing Strategy

- **Pagination tests**: Verify slide count bounds (5–10), no mid-word splits, correct hook/CTA placement
- **Renderer tests**: Verify output dimensions (1080×1350), file creation, sequential naming, graceful handling of missing logo
- All tests use `pytest` with `tmp_path` fixture for filesystem isolation
