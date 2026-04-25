# Veo Video Pipeline — Design Document

## Overview

The Video Creator agent extends the existing `Strategist → Critic → Publisher` pipeline with automated video generation via Google's Veo API. After the Critic approves a content slate, the Video Creator intercepts approved slots, analyzes current platform trends, adapts each slot's content into platform-optimized video prompts, and generates `.mp4` files ready for publishing.

## Updated Agent Topology

```
                                                     ┌──────────────┐
                                                ┌───▶│VIDEO CREATOR │
   ┌───────────┐  proposes  ┌──────────┐  approved   │ (generates   │
   │STRATEGIST │ ──────────▶│  CRITIC  │ ────────┤   │  via Veo)    │
   │ (plans    │            │ (rejects │         │   └──────┬───────┘
   │  weekly   │◀─── try ───│  ≥1 per  │         │          │ .mp4 files
   │  slate)   │    again   │  demo)   │         │          ▼
   └───────────┘            └──────────┘         │   ┌──────────────┐
                                                 └──▶│  PUBLISHER   │
                                                     │ (posts via   │
                                                     │  direct APIs)│
                                                     └──────┬───────┘
                                                            ▼
                                              YouTube · TikTok · Instagram
```

## Data Flow

### 1. Trigger: ApprovedSlate from Critic

The Critic agent outputs an `ApprovedSlate` containing:
- `Slate.slots[]` — each `ContentSlot` with `caption`, `image_prompt`, `platform`, `scheduled_for`
- `Slate.brand_id` / `Slate.org_id` — links to `BrandKit` (voice, audience, colors, industry)
- `CriticVerdict[]` — only `approved == True` slots proceed

### 2. Video Creator receives the ApprovedSlate

The Video Creator agent:
1. Filters for approved slots
2. Loads the `BrandKit` for the slate's `brand_id`
3. For each approved slot, calls the **Trend Adaptation Engine**

### 3. Trend Adaptation Engine

For each `(ContentSlot, BrandKit)` pair:
1. Fetches current trends for the slot's target platform via `get_trends(platform)`
2. Calls `adapt_prompt_for_platform(slot, brand, trends)` which returns a `VideoRequest`

Platform-specific prompt strategies:

| Platform   | Aspect Ratio | Style                                                        |
|------------|-------------|--------------------------------------------------------------|
| TikTok     | 9:16        | Fast visual hook in first 2s, trending audio cues, vertical  |
| YouTube    | 16:9        | Narrative-driven, brand intro, longer story arc, horizontal  |
| Instagram  | 9:16        | Reels-optimized, aesthetic focus, trending audio, vertical   |

### 4. Veo API Call

For each `VideoRequest`:
1. Submit prompt + aspect ratio + audio cue to Veo via `google-genai` SDK
2. Poll asynchronously with exponential backoff (10s → 120s, 10min timeout)
3. Download `.mp4` to `output/videos/{platform}_{slot_id}_{timestamp}.mp4`
4. Return `VideoResult` with local path, status, and metadata

### 5. Handoff to Publisher

The Video Creator wraps all `VideoResult`s in an `AgentEnvelope` and sends to the Publisher, which uploads to each platform via its native API.

## New Pydantic Models (added to `services/shared/models.py`)

```python
class TrendContext(BaseModel):
    platform: Platform
    trending_topics: list[str]
    style_hints: list[str]
    hook_type: str
    trending_audio_cues: list[str]

class VideoRequest(BaseModel):
    slot_id: str
    prompt: str
    aspect_ratio: str            # "9:16" or "16:9"
    platform: Platform
    audio_cue: str | None = None
    brand_context: str
    duration_seconds: int = 8

class VideoResult(BaseModel):
    slot_id: str
    video_url: str | None = None
    local_path: str | None = None
    platform: Platform
    duration_seconds: int | None = None
    status: str                  # "success", "error", "timeout"
    error: str | None = None
```

## File Structure

```
services/video_creator/
├── __init__.py
├── agent.py          # Sub-agent entry point, receives ApprovedSlate
├── trends.py         # Trend adaptation engine with mock data
├── veo_client.py     # Veo API wrapper (auth, submit, poll, download)
├── config.py         # Centralized settings
├── pyproject.toml    # Dependencies
└── tests/
    ├── __init__.py
    ├── test_trends.py      # Unit tests for trend formatting
    └── test_veo_client.py  # Mock tests for Veo API integration
```

## Error Handling

- **Veo API timeout**: Returns `VideoResult(status="timeout")`, does not crash parent
- **Veo API error (4xx/5xx)**: Returns `VideoResult(status="error", error=...)`, logged
- **Rate limiting**: Exponential backoff with jitter, retries up to 3 times
- **Invalid slot data**: Skipped with warning, other slots still processed
- All errors are encapsulated in `VideoResult` — the parent pipeline never crashes
