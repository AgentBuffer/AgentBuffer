# Imagen Image Pipeline — Design Document

## Overview

The Image Creator agent extends the existing `Strategist → Critic → Publisher` pipeline with automated image generation via Google's Imagen API. After the Critic approves a content slate, the Image Creator generates platform-optimized images for each approved slot before handing off to the Publisher.

## Updated Agent Topology

```
                                                     ┌──────────────┐
                                                ┌───▶│IMAGE CREATOR │
   ┌───────────┐  proposes  ┌──────────┐  approved   │ (generates   │
   │STRATEGIST │ ──────────▶│  CRITIC  │ ────────┤   │  via Imagen) │
   │ (plans    │            │ (rejects │         │   └──────┬───────┘
   │  weekly   │◀─── try ───│  ≥1 per  │         │          │ .png files
   │  slate)   │    again   │  demo)   │         │          ▼
   └───────────┘            └──────────┘         │   ┌──────────────┐
                                                 ├──▶│VIDEO CREATOR │
                                                 │   │ (via Veo)    │
                                                 │   └──────┬───────┘
                                                 │          ▼
                                                 │   ┌──────────────┐
                                                 └──▶│  PUBLISHER   │
                                                     │ (posts via   │
                                                     │  Ayrshare)   │
                                                     └──────┬───────┘
                                                            ▼
                                              YouTube · TikTok · Instagram
                                              LinkedIn · X
```

## Data Flow

### 1. Trigger: ApprovedSlate from Critic

The Critic agent outputs an `ApprovedSlate` containing:
- `Slate.slots[]` — each `ContentSlot` with `caption`, `image_prompt`, `platform`, `scheduled_for`
- `Slate.brand_id` / `Slate.org_id` — links to `BrandKit` (voice, audience, colors, industry)
- `CriticVerdict[]` — only `approved == True` slots proceed

### 2. Image Creator receives the ApprovedSlate

The Image Creator agent:
1. Filters for approved slots
2. For each approved slot, calls the **Prompt Adapter**

### 3. Prompt Adapter

For each `(ContentSlot, BrandKit)` pair:
1. Determines the platform-specific aspect ratio
2. Builds a platform-optimized prompt via `adapt_prompt(slot, brand)`
3. Returns an `ImageRequest` with prompt, aspect ratio, brand context, and negative prompt

Platform-specific prompt strategies:

| Platform   | Aspect Ratio | Style                                                          |
|------------|-------------|----------------------------------------------------------------|
| Instagram  | 3:4         | Aesthetic, lifestyle photography, warm tones, editorial feel   |
| LinkedIn   | 16:9      | Professional, clean, data-driven, corporate visual style       |
| X          | 16:9        | Bold, high-contrast, attention-grabbing, vibrant colors        |
| TikTok     | 9:16        | Vibrant, vertical, trend-aware, energetic, youthful            |
| YouTube    | 16:9        | Cinematic, professional photography with depth                 |

### 4. Imagen API Call

For each `ImageRequest`:
1. Submit prompt + aspect ratio to Imagen via `google-genai` SDK (`models.generate_images`)
2. Imagen returns synchronously (no polling needed, unlike Veo)
3. Extract image bytes from response
4. Save to `output/images/{platform}_{slot_id}_{timestamp}.png`
5. Return `ImageResult` with local path and status
6. Retry up to `MAX_RETRIES` on transient failures

### 5. Handoff to Publisher

The Image Creator wraps all `ImageResult`s in an `AgentEnvelope` and sends to the Publisher. If images are saved locally, the Publisher uploads them to Supabase Storage via `_upload_to_storage()` to get public URLs before publishing to social platforms via Ayrshare.

### 6. Carousel Integration

When AI-generated images are available for a slot, the Carousel Creator's `render_slide()` function can use them as slide backgrounds (with a semi-transparent dark overlay for text readability), instead of the default solid-color background.

## New Pydantic Models (added to `services/shared/models.py`)

```python
class ImageRequest(BaseModel):
    slot_id: str
    prompt: str
    aspect_ratio: str
    platform: Platform
    style: str | None = None
    brand_context: str
    negative_prompt: str = ""

class ImageResult(BaseModel):
    slot_id: str
    image_url: str | None = None
    local_path: str | None = None
    platform: Platform
    status: str            # "success", "error"
    error: str | None = None
```

## File Structure

```
services/image_creator/
├── __init__.py
├── agent.py            # Sub-agent entry point, receives ApprovedSlate
├── prompt_adapter.py   # Platform-optimized prompt builder
├── imagen_client.py    # Imagen API wrapper (submit, extract, save)
├── config.py           # Centralized settings
├── pyproject.toml      # Dependencies
└── tests/
    ├── __init__.py
    ├── test_imagen_client.py   # Mock tests for Imagen API integration
    ├── test_prompt_adapter.py  # Unit tests for prompt formatting
    └── test_agent.py           # Integration tests for agent logic
```

## Error Handling

- **Imagen API error (4xx/5xx)**: Returns `ImageResult(status="error", error=...)`, logged
- **Transient failures**: Retries up to `MAX_RETRIES` with linear backoff
- **Invalid slot data**: Skipped with warning, other slots still processed
- **Missing image bytes**: Returns `ImageResult(status="error")`, does not crash parent
- All errors are encapsulated in `ImageResult` — the parent pipeline never crashes

## Environment Variables

```
GOOGLE_API_KEY=...                            # Already needed for Veo, reused for Imagen
IMAGEN_MODEL=imagen-4.0-generate-preview      # Imagen model version
IMAGEN_MAX_RETRIES=3                          # Max retry attempts
IMAGEN_RETRY_DELAY=5                          # Delay between retries (seconds)
IMAGE_OUTPUT_DIR=output/images                # Local output directory
IMAGE_CREATOR_SEED=agentbuffer-image-creator-seed-v1  # Agentverse seed
IMAGE_CREATOR_PORT=8006                       # Agent port
IMAGE_CREATOR_ADDRESS=                        # Agentverse address, or empty for inline mode
```
