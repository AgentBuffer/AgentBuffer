# Cognition Agent Architecture

> **Status:** Draft — awaiting approval before implementation.
>
> **Branch:** `architecture/cognition-agent-plan`
>
> **Author:** Devin (automated)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Sub-Task 1 — Pipeline Audit & Tool Interface Design](#2-sub-task-1--pipeline-audit--tool-interface-design)
   - [2.1 Design System Pipeline Audit](#21-design-system-pipeline-audit)
   - [2.2 Carousel Generator Pipeline Audit](#22-carousel-generator-pipeline-audit)
   - [2.3 Generative Video Pipeline Audit](#23-generative-video-pipeline-audit)
   - [2.4 Unified Tool Interface — OpenAI-Compatible Function-Calling Schemas](#24-unified-tool-interface--openai-compatible-function-calling-schemas)
3. [Sub-Task 2 — Cognition Agent Logic Blueprint](#3-sub-task-2--cognition-agent-logic-blueprint)
   - [3.1 Position in the Architecture](#31-position-in-the-architecture)
   - [3.2 Prompt Decomposition Strategy](#32-prompt-decomposition-strategy)
   - [3.3 Tool Selection & Execution Order](#33-tool-selection--execution-order)
   - [3.4 Error Handling & Recovery](#34-error-handling--recovery)
   - [3.5 State Machine](#35-state-machine)
4. [Sub-Task 3 — Refactoring Strategy](#4-sub-task-3--refactoring-strategy)
   - [4.1 Guiding Principles](#41-guiding-principles)
   - [4.2 Files to Create](#42-files-to-create)
   - [4.3 Files to Modify](#43-files-to-modify)
   - [4.4 Files Unchanged](#44-files-unchanged)
   - [4.5 Step-by-Step Implementation Order](#45-step-by-step-implementation-order)

---

## 1. Executive Summary

The AgentBuffer system currently has three creative execution pipelines that operate as standalone modules called directly by the Head Agent or via uAgents Chat Protocol messages. Each pipeline has its own input format, calling convention, and error model.

This document proposes a **Cognition Agent** — a new orchestration layer that sits between the Main Agent (Head Agent) and the execution pipelines. The Cognition Agent:

1. Receives high-level prompts from the Main Agent (e.g., "Create a cross-platform campaign for this new shoe")
2. Decomposes them into discrete tool invocations using LLM-based reasoning
3. Executes tools in the correct order (respecting dependencies and parallelism)
4. Handles errors, retries, and fallbacks
5. Aggregates results and returns a unified response

The three pipelines are wrapped as **Tools** with standardized JSON schemas conforming to the OpenAI function-calling format, so the Cognition Agent can reason about which tools to call, what arguments to pass, and how to interpret results.

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER (via ASI:One)                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │ Chat Protocol
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                 MAIN AGENT (Head Agent)                          │
│   Intake → BrandKit extraction → Marketing Analysis             │
│   Strategist → Critic → approval gate                           │
│                                                                 │
│   Now delegates creative execution to Cognition Agent ──────┐   │
└─────────────────────────────────────────────────────────────┼───┘
                                                              │
                            ▼                                 │
┌─────────────────────────────────────────────────────────────┼───┐
│                 COGNITION AGENT (NEW)                        │   │
│                                                             │   │
│   Receives: ApprovedSlate + BrandKit + execution directive  │   │
│                                                             │   │
│   1. LLM reasons over available tools                       │   │
│   2. Builds execution plan (ordered DAG of tool calls)      │   │
│   3. Executes tools, handles errors/retries                 │   │
│   4. Aggregates results → returns to Main Agent             │   │
│                                                             │   │
│   ┌────────────┐  ┌────────────────┐  ┌────────────────┐   │   │
│   │ Design     │  │ Carousel       │  │ Video          │   │   │
│   │ Tool       │  │ Tool           │  │ Tool           │   │   │
│   └────────────┘  └────────────────┘  └────────────────┘   │   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Sub-Task 1 — Pipeline Audit & Tool Interface Design

### 2.1 Design System Pipeline Audit

**Location:** `services/design_director/` + `services/design_specialists/`

**Current entry point:** `design_director.main.handle_request(envelope: AgentEnvelope) → AgentEnvelope`

**Internal flow:**
1. Receives an `AgentEnvelope` with `envelope_type="design_request"`, extracts `DesignRequest` from payload
2. Auto-classifies `task_type` from free-text description if not provided (`planner.classify_task()`)
3. Builds a `DesignPlan` — an ordered list of `PlanStep` objects mapping to specialist agents
4. Iterates steps sequentially; for each step looks up the specialist via `registry.get_specialist(step.agent)` and calls `specialist.execute(step, task_id)`
5. Retries each failed step once
6. Returns an `AgentEnvelope(design_complete)` with all `SpecialistResult` objects

**Registered specialists:**
- `layout` → `LayoutSpecialist` — renders marketing headers, infographics as PNGs via Pillow

**Input model — `DesignRequest`:**
| Field | Type | Required | Description |
|---|---|---|---|
| `task_description` | `str` | Yes | Free-text description of desired asset |
| `task_type` | `DesignTaskType` enum | Yes (auto-classified if omitted at API level) | `logo_variation`, `marketing_header`, `infographic`, `social_rebrand` |
| `brand_kit` | `BrandKit` | Yes | Full brand identity object |
| `platform` | `Platform \| None` | No | Target platform for dimension selection |
| `inputs` | `dict` | No | Additional params: `headline`, `body`, `cta`, `background_image` |

**Output model — `SpecialistResult`:**
| Field | Type | Description |
|---|---|---|
| `task_id` | `str` | Unique task identifier (e.g., `dtask-abc123`) |
| `step_id` | `str` | Step within the plan |
| `agent` | `str` | Which specialist ran |
| `success` | `bool` | Whether execution succeeded |
| `output_paths` | `list[str]` | File paths to generated assets (PNGs) |
| `error` | `str \| None` | Error message on failure |

**Key observations:**
- Currently wrapped in `AgentEnvelope` — the Cognition Agent should call the pipeline directly, bypassing the envelope layer
- Platform dimensions are codified in `brand_presets.py`: LinkedIn 1200×628, X 1200×675, Instagram 1080×1080
- The registry is designed for extension (future `logo_maker` specialist)

---

### 2.2 Carousel Generator Pipeline Audit

**Location:** `services/carousel_creator/`

**Current entry point:** `carousel_creator.agent.process_approved_slate(slate: ApprovedSlate, brand: BrandKit, output_root: Path | None) → list[CarouselResult]`

**Internal flow:**
1. Receives `ApprovedSlate` + `BrandKit`
2. Filters slots to only approved + carousel-appropriate platforms (`INSTAGRAM`, `LINKEDIN`)
3. For each qualifying slot:
   a. Paginates the caption into a slide sequence via `pagination.paginate_content()` (hook → body → CTA, 5–10 slides)
   b. Renders each slide as a 1080×1350 PNG via `renderer.render_slide()`
   c. Saves to `output/<slot_id>/` directory
4. Returns `CarouselResult` per slot

**Input models:**
- `ApprovedSlate` — contains a `Slate` (with `ContentSlot[]`) and `CriticVerdict[]`
- `BrandKit` — brand identity for styling

**Output model — `CarouselResult`:**
| Field | Type | Description |
|---|---|---|
| `slot_id` | `str` | Content slot identifier |
| `platform` | `Platform` | Target platform |
| `slide_paths` | `list[str]` | File paths to rendered PNG slides |
| `output_dir` | `str` | Directory containing all slides |
| `status` | `str` | `"success"` or `"error"` |
| `error` | `str \| None` | Error message on failure |

**Key observations:**
- Takes an `ApprovedSlate` (post-critic), but for the Cognition Agent tool interface we should also support a simpler "single-slot" mode: pass caption + image_prompt + brand directly
- Pagination logic is deterministic (no LLM/API calls) — fast and reliable
- Rendering is synchronous, CPU-bound (Pillow) — typically < 5 seconds for a full carousel

---

### 2.3 Generative Video Pipeline Audit

**Location:** `services/video_creator/`

**Current entry point:** `video_creator.agent.process_approved_slate(slate: ApprovedSlate, brand: BrandKit, veo_client: VeoClient | None) → list[VideoResult]` (async)

**Internal flow:**
1. Receives `ApprovedSlate` + `BrandKit`
2. For each approved slot:
   a. Fetches `TrendContext` for the slot's platform (`trends.get_trends()` — currently mock data)
   b. Adapts the slot's caption + image_prompt into a platform-optimized Veo prompt (`trends.adapt_prompt_for_platform()`)
   c. Submits to Google Veo API via `VeoClient.generate_video()` (async)
   d. Polls with exponential backoff (10s → 120s max delay, 600s timeout)
   e. Auto-retries up to 3 times on transient errors
   f. Downloads .mp4 to `output/videos/`
3. Returns `VideoResult` per slot

**Input models:**
- `ApprovedSlate` + `BrandKit` (same as carousel)
- Internally constructs `VideoRequest` — the Veo-ready payload

**Output model — `VideoResult`:**
| Field | Type | Description |
|---|---|---|
| `slot_id` | `str` | Content slot identifier |
| `video_url` | `str \| None` | Remote GCS URI of generated video |
| `local_path` | `str \| None` | Local file path to downloaded .mp4 |
| `platform` | `Platform` | Target platform |
| `duration_seconds` | `int \| None` | Video length (default 8s) |
| `status` | `str` | `"success"`, `"error"`, or `"timeout"` |
| `error` | `str \| None` | Error description |

**Key observations:**
- This is the only pipeline with external API dependency (Google GenAI / Veo)
- Requires `GOOGLE_API_KEY` environment variable
- Long-running: a single video can take 2–10 minutes
- Already has robust error handling and retry logic built in
- Aspect ratios are platform-specific: TikTok/Instagram = 9:16, YouTube/LinkedIn/X = 16:9
- Trend data is mock — designed for swap-in of live trend APIs

---

### 2.4 Unified Tool Interface — OpenAI-Compatible Function-Calling Schemas

The Cognition Agent uses LLM function-calling to decide which tools to invoke. Each tool is defined as an OpenAI-compatible function schema so the LLM can:
1. See the available tools and their descriptions
2. Choose which tool(s) to call given a prompt
3. Generate the correct arguments

#### 2.4.1 Shared Types

```json
{
  "BrandKit": {
    "type": "object",
    "required": ["brand_id", "org_id", "name", "tagline", "voice_description", "target_audience", "color_palette", "sample_captions", "industry"],
    "properties": {
      "brand_id":          { "type": "string" },
      "org_id":            { "type": "string" },
      "name":              { "type": "string", "description": "Brand or company name" },
      "tagline":           { "type": "string", "description": "Short brand tagline" },
      "voice_description": { "type": "string", "description": "Brand voice/tone description" },
      "target_audience":   { "type": "string", "description": "Target audience" },
      "color_palette":     { "type": "array", "items": { "type": "string" }, "description": "Hex colors, e.g. ['#1A1A2E', '#E94560']" },
      "logo_url":          { "type": "string", "nullable": true, "description": "Path to logo file (optional)" },
      "sample_captions":   { "type": "array", "items": { "type": "string" }, "description": "Example captions" },
      "industry":          { "type": "string", "description": "Business industry" }
    }
  },
  "Platform": {
    "type": "string",
    "enum": ["linkedin", "x", "instagram", "tiktok", "youtube"]
  }
}
```

#### 2.4.2 Tool: `generate_design_asset`

```json
{
  "name": "generate_design_asset",
  "description": "Generate marketing design assets (headers, infographics, logo variations, social rebrands) using the autonomous design system. Renders high-quality PNG images with brand colors, typography, logo placement, and platform-specific dimensions. Best for static visual assets.",
  "parameters": {
    "type": "object",
    "required": ["task_description", "brand_kit"],
    "properties": {
      "task_description": {
        "type": "string",
        "description": "Free-text description of the desired design asset. The system auto-classifies the task type (logo_variation, marketing_header, infographic, social_rebrand) from keywords."
      },
      "task_type": {
        "type": "string",
        "enum": ["logo_variation", "marketing_header", "infographic", "social_rebrand"],
        "description": "Explicit design task type. If omitted, auto-classified from task_description."
      },
      "brand_kit": { "$ref": "#/definitions/BrandKit" },
      "platform": {
        "$ref": "#/definitions/Platform",
        "description": "Target platform for dimension sizing. Defaults to linkedin (1200x628)."
      },
      "headline": {
        "type": "string",
        "description": "Headline text for the asset."
      },
      "body": {
        "type": "string",
        "description": "Body text for the asset."
      },
      "cta": {
        "type": "string",
        "description": "Call-to-action button text."
      },
      "background_image": {
        "type": "string",
        "description": "Path to background image file (optional)."
      }
    }
  }
}
```

**Returns:**
```json
{
  "type": "object",
  "properties": {
    "task_id":      { "type": "string" },
    "success":      { "type": "boolean" },
    "output_paths": { "type": "array", "items": { "type": "string" } },
    "error":        { "type": "string", "nullable": true }
  }
}
```

#### 2.4.3 Tool: `generate_carousel`

```json
{
  "name": "generate_carousel",
  "description": "Generate a multi-slide carousel image set (5-10 slides) for Instagram or LinkedIn. Converts marketing copy into a visual narrative: hook slide, body slides with key messages, and a call-to-action closing slide. Each slide is 1080x1350 PNG with brand styling.",
  "parameters": {
    "type": "object",
    "required": ["caption", "brand_kit", "platform"],
    "properties": {
      "caption": {
        "type": "string",
        "description": "Full marketing caption/copy to paginate across slides."
      },
      "image_prompt": {
        "type": "string",
        "description": "Visual direction or image prompt for speaker-notes context."
      },
      "brand_kit": { "$ref": "#/definitions/BrandKit" },
      "platform": {
        "type": "string",
        "enum": ["instagram", "linkedin"],
        "description": "Target platform. Carousels are optimized for Instagram and LinkedIn."
      },
      "slot_id": {
        "type": "string",
        "description": "Unique identifier for this content slot. Auto-generated if omitted."
      },
      "min_slides": {
        "type": "integer",
        "default": 5,
        "minimum": 2,
        "maximum": 10,
        "description": "Minimum number of slides."
      },
      "max_slides": {
        "type": "integer",
        "default": 10,
        "minimum": 3,
        "maximum": 15,
        "description": "Maximum number of slides."
      }
    }
  }
}
```

**Returns:**
```json
{
  "type": "object",
  "properties": {
    "slot_id":     { "type": "string" },
    "platform":    { "type": "string" },
    "slide_count": { "type": "integer" },
    "slide_paths": { "type": "array", "items": { "type": "string" } },
    "output_dir":  { "type": "string" },
    "status":      { "type": "string", "enum": ["success", "error"] },
    "error":       { "type": "string", "nullable": true }
  }
}
```

#### 2.4.4 Tool: `generate_video`

```json
{
  "name": "generate_video",
  "description": "Generate a platform-optimized marketing video using Google Veo. Adapts the prompt for platform-specific trends, hooks, and style. Produces MP4 video files. Supports TikTok (9:16), Instagram Reels (9:16), YouTube (16:9), LinkedIn (16:9), and X (16:9). This tool is async and may take 2-10 minutes per video.",
  "parameters": {
    "type": "object",
    "required": ["caption", "image_prompt", "brand_kit", "platform"],
    "properties": {
      "caption": {
        "type": "string",
        "description": "Marketing message or caption to convey in the video."
      },
      "image_prompt": {
        "type": "string",
        "description": "Visual concept description for video generation."
      },
      "brand_kit": { "$ref": "#/definitions/BrandKit" },
      "platform": {
        "$ref": "#/definitions/Platform",
        "description": "Target platform — determines aspect ratio, hook style, and trend adaptation."
      },
      "slot_id": {
        "type": "string",
        "description": "Unique slot identifier. Auto-generated if omitted."
      },
      "duration_seconds": {
        "type": "integer",
        "default": 8,
        "minimum": 4,
        "maximum": 30,
        "description": "Target video duration in seconds."
      }
    }
  }
}
```

**Returns:**
```json
{
  "type": "object",
  "properties": {
    "slot_id":          { "type": "string" },
    "video_url":        { "type": "string", "nullable": true },
    "local_path":       { "type": "string", "nullable": true },
    "platform":         { "type": "string" },
    "duration_seconds": { "type": "integer", "nullable": true },
    "status":           { "type": "string", "enum": ["success", "error", "timeout"] },
    "error":            { "type": "string", "nullable": true }
  }
}
```

#### 2.4.5 How the Cognition Agent Distinguishes Between Tools

The LLM uses these **selection heuristics** (encoded in tool descriptions and reinforced by system prompt):

| Signal in Prompt | Tool Selected | Rationale |
|---|---|---|
| "carousel", "slideshow", "slides", "Instagram carousel", "swipe" | `generate_carousel` | Multi-image format |
| "video", "reel", "TikTok", "clip", "motion", "animation" | `generate_video` | Motion content |
| "header", "banner", "logo", "infographic", "cover image", "thumbnail" | `generate_design_asset` | Static design asset |
| "campaign" (multi-platform) | Multiple tools | One per platform, type inferred from platform norms |
| Platform = Instagram | `generate_carousel` + `generate_video` | Instagram supports both — default to carousel unless "reel" or "video" is mentioned |
| Platform = TikTok | `generate_video` | TikTok is video-first |
| Platform = LinkedIn | `generate_design_asset` or `generate_carousel` | LinkedIn favors professional imagery and carousels |

The system prompt for the Cognition Agent's LLM will include explicit routing rules reinforcing these heuristics.

---

## 3. Sub-Task 2 — Cognition Agent Logic Blueprint

### 3.1 Position in the Architecture

```
User → Main Agent → [Intake, Analysis, Strategize, Critique, Approval] → Cognition Agent → [Tools] → Main Agent → Publisher → User
```

The Cognition Agent enters the pipeline **after the approval gate** and **before publishing**. The Main Agent hands off an `ApprovedSlate` + `BrandKit` + optional high-level directive (e.g., "Focus on video for TikTok, carousels for Instagram"). The Cognition Agent decides which tools to run for each approved slot and returns the generated assets.

Alternatively, the Cognition Agent can also be invoked **standalone** with a free-form prompt (e.g., from the MCP server or a direct API call) — it will use LLM reasoning to decompose the request into tool calls.

### 3.2 Prompt Decomposition Strategy

The Cognition Agent uses a **two-phase decomposition**:

**Phase 1 — Planning (LLM call)**

Given a high-level prompt or `ApprovedSlate`, the LLM generates an **execution plan**: an ordered list of tool calls with arguments. The LLM sees:
- The available tool schemas (Section 2.4)
- The brand kit
- The approved content slots (if coming from the pipeline)
- Platform-specific best practices (from system prompt)

Example input to LLM:
```
You are the Cognition Agent for AgentBuffer. You have these tools available:
[tool schemas]

The Main Agent has approved the following content slots for execution:
- Slot slot-001: Instagram, caption "5 AI Marketing Tips...", image_prompt "..."
- Slot slot-002: TikTok, caption "Watch this AI transform...", image_prompt "..."
- Slot slot-003: LinkedIn, caption "Our Q3 results...", image_prompt "..."

BrandKit: { ... }

Generate an execution plan. For each slot, decide which tool(s) to call and with what arguments.
Return the plan as a JSON array of tool calls.
```

Example LLM output (execution plan):
```json
[
  {
    "step": 1,
    "tool": "generate_carousel",
    "slot_id": "slot-001",
    "reason": "Instagram content → carousel format for maximum engagement",
    "args": { "caption": "...", "brand_kit": {...}, "platform": "instagram" }
  },
  {
    "step": 2,
    "tool": "generate_video",
    "slot_id": "slot-002",
    "reason": "TikTok content → video format (platform is video-first)",
    "args": { "caption": "...", "image_prompt": "...", "brand_kit": {...}, "platform": "tiktok" }
  },
  {
    "step": 3,
    "tool": "generate_design_asset",
    "slot_id": "slot-003",
    "reason": "LinkedIn content → professional header/infographic",
    "args": { "task_description": "...", "brand_kit": {...}, "platform": "linkedin", "headline": "..." }
  }
]
```

**Phase 2 — Execution**

The Cognition Agent iterates over the plan and executes each tool call. Independent calls (different slots) can run in parallel; dependent calls (e.g., a rebrand that needs a logo before a header) run sequentially.

### 3.3 Tool Selection & Execution Order

**Decision tree** (deterministic fallback if LLM planning is unavailable):

```
For each approved ContentSlot:
│
├── platform == TIKTOK?
│   └── generate_video(9:16)
│
├── platform == YOUTUBE?
│   └── generate_video(16:9)
│
├── platform == INSTAGRAM?
│   ├── slot mentions "reel" or "video"?
│   │   └── generate_video(9:16)
│   └── else
│       └── generate_carousel(1080x1350)
│
├── platform == LINKEDIN?
│   ├── slot has long-form caption (>200 chars)?
│   │   └── generate_carousel
│   └── else
│       └── generate_design_asset(marketing_header, 1200x628)
│
└── platform == X?
    └── generate_design_asset(marketing_header, 1200x675)
```

**Execution ordering rules:**
1. All tool calls for different slots are **independent** → execute in parallel (async)
2. If a slot requires multiple tools (e.g., `social_rebrand` = logo + header), execute **sequentially** per the `DesignPlan` dependency DAG
3. Video generation is long-running → start first, then run carousels/design in parallel while waiting

### 3.4 Error Handling & Recovery

```
┌──────────────────────────────────────────────────────────────────┐
│                    Error Handling Flowchart                       │
│                                                                  │
│  Tool returns status="error" or status="timeout"                 │
│  │                                                               │
│  ├── Attempt ≤ max_retries (default 2)?                          │
│  │   ├── YES → Retry same tool with same args                    │
│  │   │         (video tool has internal 3x retry too)            │
│  │   └── NO  → Go to fallback                                   │
│  │                                                               │
│  ├── Fallback available?                                         │
│  │   ├── Video timeout → try generate_design_asset as static     │
│  │   │                   fallback + log degradation              │
│  │   ├── Design error  → retry with simplified inputs            │
│  │   │                   (drop background_image, reduce text)    │
│  │   ├── Carousel error → retry with min_slides=3               │
│  │   └── No fallback   → mark slot as "failed"                  │
│  │                                                               │
│  └── Report results                                              │
│      ├── Success: include output_paths/video_url in response     │
│      ├── Partial: report which slots succeeded and which failed  │
│      └── Total failure: return error summary to Main Agent       │
└──────────────────────────────────────────────────────────────────┘
```

**Error categories and responses:**

| Error | Category | Action |
|---|---|---|
| `SpecialistResult.success == False` | Design pipeline failure | Retry 1x, then mark failed |
| `CarouselResult.status == "error"` | Carousel rendering failure | Retry with `min_slides=3`, then mark failed |
| `VideoResult.status == "error"` | Veo API error (auth, quota, content policy) | Retry 1x (inner 3x already happened), then fallback to static design |
| `VideoResult.status == "timeout"` | Veo polling timeout (>600s) | Fallback to static design, log warning |
| LLM planning failure | Cognition Agent internal | Fall back to deterministic decision tree (Section 3.3) |
| Invalid BrandKit | Input validation | Return immediate error — do not attempt any tools |

### 3.5 State Machine

The Cognition Agent operates as a lightweight state machine:

```
IDLE → PLANNING → EXECUTING → AGGREGATING → COMPLETE
                      │
                      ├── (per-tool states)
                      │   PENDING → RUNNING → SUCCESS
                      │                    → RETRYING → SUCCESS
                      │                              → FALLBACK → SUCCESS
                      │                                        → FAILED
                      │
                      └── When all tools reach terminal state → AGGREGATING
```

**State storage** (in-memory dict, keyed by `execution_id`):

```python
{
    "execution_id": "exec-abc123",
    "state": "executing",
    "brand_kit": { ... },
    "plan": [ ... ],  # list of planned tool calls
    "results": {
        "slot-001": { "tool": "generate_carousel", "state": "success", "result": {...} },
        "slot-002": { "tool": "generate_video", "state": "running", "attempt": 1 },
        "slot-003": { "tool": "generate_design_asset", "state": "pending" }
    },
    "created_at": "2025-04-25T18:00:00Z",
    "completed_at": null
}
```

---

## 4. Sub-Task 3 — Refactoring Strategy

### 4.1 Guiding Principles

1. **No breaking changes** — all existing services, tests, and the uAgents pipeline continue to work unchanged
2. **Composition over modification** — the Cognition Agent composes existing pipeline functions; it does not modify their internals
3. **New code in `src/`** — the Cognition Agent and tool wrappers live in `src/agents/`, cleanly separated from `services/`
4. **Shared models** — reuse existing Pydantic models from `services/shared/models.py`; add new models only for the Cognition Agent's own types

### 4.2 Files to Create

| File | Purpose |
|---|---|
| `src/agents/__init__.py` | Package init |
| `src/agents/cognition_agent.py` | Core Cognition Agent class — planning, execution, aggregation |
| `src/agents/tools/__init__.py` | Tools package init |
| `src/agents/tools/base.py` | `BaseTool` abstract class — unified interface for all tools |
| `src/agents/tools/design_tool.py` | Wraps `design_director.main.handle_request()` |
| `src/agents/tools/carousel_tool.py` | Wraps `carousel_creator.agent.process_approved_slate()` and adds single-slot convenience mode |
| `src/agents/tools/video_tool.py` | Wraps `video_creator.agent.process_approved_slate()` and adds single-slot convenience mode |
| `src/agents/tool_schemas.py` | JSON function-calling schemas for all three tools (Section 2.4) |
| `src/agents/planner.py` | LLM-based planning logic (prompt construction, plan parsing) |
| `src/agents/models.py` | Cognition Agent-specific Pydantic models (`ExecutionPlan`, `ToolCall`, `ExecutionState`, `CognitionResult`) |
| `tests/test_cognition_agent.py` | Unit tests for the Cognition Agent's decision-making logic |
| `tests/test_tool_wrappers.py` | Unit tests for each tool wrapper |
| `docs/cognition_architecture.md` | This document |

### 4.3 Files to Modify

| File | Change | Why |
|---|---|---|
| `services/design_director/registry.py` | Add auto-registration of `LayoutSpecialist` at import time | Currently specialists must be manually registered; the tool wrapper needs them registered to work |
| `services/design_specialists/__init__.py` | Import and register `LayoutSpecialist` | Enables `from services.design_specialists import LayoutSpecialist` to auto-register |
| `pyproject.toml` | Add `src` to package paths if needed | Ensure `src.agents` is importable |
| `.github/workflows/ci.yml` | Add `test-cognition` job | Run the new tests in CI |

### 4.4 Files Unchanged

All core pipeline code remains untouched:

- `services/design_director/planner.py` — no changes
- `services/design_director/main.py` — no changes
- `services/design_specialists/layout_specialist.py` — no changes
- `services/design_specialists/common/*` — no changes
- `services/carousel_creator/pagination.py` — no changes
- `services/carousel_creator/renderer.py` — no changes
- `services/carousel_creator/agent.py` — no changes
- `services/video_creator/veo_client.py` — no changes
- `services/video_creator/trends.py` — no changes
- `services/video_creator/agent.py` — no changes
- `services/video_creator/config.py` — no changes
- `services/shared/models.py` — no changes (new models go in `src/agents/models.py`)
- `services/head_agent/*` — no changes (integration deferred to post-approval phase)
- `src/mcp_server/*` — no changes

### 4.5 Step-by-Step Implementation Order

**Step 1: Tool Interface Layer** (no external dependencies)
1. Create `src/agents/tools/base.py` — define `BaseTool` abstract class with `name`, `description`, `parameters_schema`, and `execute(**kwargs) → dict` interface
2. Create `src/agents/models.py` — define `ToolCall`, `ExecutionPlan`, `ToolResult`, `CognitionResult`
3. Create `src/agents/tool_schemas.py` — the JSON schemas from Section 2.4

**Step 2: Tool Wrappers** (thin adapters over existing pipelines)
4. Create `src/agents/tools/design_tool.py` — imports from `services/design_director/`, registers specialists, adapts I/O to `BaseTool` interface
5. Create `src/agents/tools/carousel_tool.py` — imports from `services/carousel_creator/`, adds single-slot convenience mode
6. Create `src/agents/tools/video_tool.py` — imports from `services/video_creator/`, adds single-slot async wrapper
7. Update `services/design_specialists/__init__.py` to auto-register `LayoutSpecialist`

**Step 3: Cognition Agent Core**
8. Create `src/agents/planner.py` — LLM planning logic + deterministic fallback
9. Create `src/agents/cognition_agent.py` — the `CognitionAgent` class:
   - `__init__()` — registers available tools, loads schemas
   - `plan(prompt, brand_kit, slots?) → ExecutionPlan`
   - `execute(plan) → CognitionResult` (async, parallel tool execution)
   - Deterministic fallback decision tree
   - Error handling and retry logic

**Step 4: Tests**
10. Write `tests/test_cognition_agent.py`:
    - Test that `plan()` correctly selects tools based on platform/content type
    - Test deterministic fallback decision tree
    - Test error handling (mock tools returning errors)
    - Test parallel execution ordering
11. Write `tests/test_tool_wrappers.py`:
    - Test each tool wrapper with mock inputs
    - Verify output schema compliance

**Step 5: CI Integration**
12. Add `test-cognition` job to `.github/workflows/ci.yml`

**Step 6: Head Agent Integration** (post-approval — NOT in this PR)
13. Add Cognition Agent dispatch between approval gate and publisher in `head_agent/agent.py`
14. Wire MCP `generate_social_campaign` to use Cognition Agent for tool selection

---

## Appendix A: Comparison — Current vs. Proposed Architecture

| Aspect | Current | Proposed |
|---|---|---|
| Tool selection | Hard-coded in Head Agent (video for all slots) | LLM-reasoned + deterministic fallback |
| Tool interface | Different function signatures per pipeline | Unified `BaseTool.execute(**kwargs) → dict` |
| Error handling | Per-pipeline, no cross-pipeline fallback | Centralized retry/fallback in Cognition Agent |
| Parallelism | Sequential slot processing | Parallel execution of independent slots |
| Extensibility | Adding a tool requires Head Agent changes | Register new `BaseTool` subclass — auto-discovered |
| Observability | Scattered logging | Centralized execution state with per-slot tracking |

## Appendix B: Environment Variables

| Variable | Required By | Default | Description |
|---|---|---|---|
| `GOOGLE_API_KEY` | Video Tool | (none) | Google GenAI API key for Veo |
| `ASI_ONE_API_KEY` | Cognition Agent (LLM planning) | (none) | ASI:One LLM API key |
| `ASI_ONE_BASE_URL` | Cognition Agent | `https://api.asi1.ai/v1` | LLM endpoint |
| `ASI_ONE_MODEL` | Cognition Agent | `asi1` | Model name |
| `VIDEO_OUTPUT_DIR` | Video Tool | `output/videos` | Video output directory |
| `VEO_MODEL` | Video Tool | `veo-3.0-generate-preview` | Veo model version |
