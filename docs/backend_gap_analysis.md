# Backend Gap Analysis

> **Branch:** `chore/backend-gap-analysis`
> **Date:** 2026-04-25
> **Author:** Devin (automated audit)

---

## 1  Executive Summary

The Next.js frontend (`apps/web/`) defines **five gateway API calls** and **three Supabase direct calls**, plus several UI interactions that expect backend features that do not yet exist. The FastAPI gateway (`gateway/main.py`) is a **single-line placeholder** with zero endpoints. All frontend data currently comes from hardcoded mock objects or Supabase client-side calls.

This document catalogues every gap, groups them by priority, defines the exact endpoint contracts, and maps each to the internal agent or pipeline that must power it.

---

## 2  Frontend Network Audit

### 2.1  Gateway API Calls (`apps/web/lib/gateway.ts`)

| # | Function | Method | URL | Status |
|---|----------|--------|-----|--------|
| 1 | `fetchBrand()` | `GET` | `/api/brands` | **MISSING** — returns mock `BrandKit` |
| 2 | `fetchSlots()` | `GET` | `/api/slots` | **MISSING** — returns mock `ContentSlot[]` |
| 3 | `fetchMessages()` | `GET` | `/api/messages` | **MISSING** — returns mock `AgentEnvelope[]` |
| 4 | `rankSlots()` | `POST` | `/api/rank-slots` | **MISSING** — returns mock `RankedSlot[]` |
| 5 | `triggerPublish()` | `POST` | `/api/trigger-publish` | **MISSING** — returns mock `PublishResult[]` |

### 2.2  Supabase Direct Calls (Server Actions)

| # | Action file | Table | Operation | Status |
|---|-------------|-------|-----------|--------|
| 1 | `actions/brands.ts` | `brands` | `INSERT` | Works via Supabase (DB table exists) |
| 2 | `actions/slots.ts` | `content_slots` | `SELECT *` | Works via Supabase (DB table exists) |
| 3 | `actions/publish.ts` | `content_slots` | `UPDATE status` | Works via Supabase (DB table exists) |

### 2.3  UI Features With No Backend Trigger

| # | Feature | Component | What's Missing |
|---|---------|-----------|----------------|
| 1 | **Brand Kit AI Extraction** | `onboarding-wizard.tsx:48-65` | Hardcoded `setTimeout` — no call to any extraction API |
| 2 | **PDF Upload & Parsing** | `upload-assets-step.tsx` | Files collected client-side but never sent anywhere |
| 3 | **Social Profile Scraping** | `connect-socials-step.tsx` | URLs collected but never processed |
| 4 | **Regenerate Rejected Slot** | `slot-detail.tsx:122` | Button rendered but has no `onClick` handler/API |
| 5 | **Side-by-Side Comparison** | `side-by-side.tsx` | Component exists but is never mounted (no regeneration flow) |
| 6 | **Performance Analytics** | (not yet in UI) | `PerformanceHarvester` agent exists but no API surfaces data |
| 7 | **Campaign Management** | (not yet in UI) | MCP server has campaigns but no frontend page |

### 2.4  Frontend Data Structures Expected

All TypeScript types are in `apps/web/lib/types/models.ts`:

- `BrandKit` — 10 fields (brand_id, org_id, name, tagline, voice_description, target_audience, color_palette, logo_url, sample_captions, industry)
- `ContentSlot` — 11 fields including optional critic_scores, critic_average, critic_summary
- `Slate` — wraps slots with slate_id, brand_id, org_id, generation_context
- `CriticScore` — axis, score, reasoning
- `CriticVerdict` — slot_id, scores, average, approved, summary
- `PublishResult` — slot_id, platform, success, permalink, error, idempotency_key
- `AgentEnvelope` — id, from_agent, to_agent, envelope_type, payload, signature, created_at
- `RankedSlot` — slot_id, rank, reasoning

---

## 3  Backend Current State

### 3.1  Gateway (`gateway/main.py`)

```python
"""FastAPI gateway — placeholder. Read-only API that forwards user JWT."""
```

**Zero endpoints. Zero routes. Zero middleware.**

### 3.2  Agent Services (uAgents-based, not HTTP)

| Service | Entry Point | Protocol | Invocation |
|---------|-------------|----------|------------|
| Head Agent | `services/head_agent/agent.py` | Chat Protocol (uAgents) | ASI:One → ChatMessage |
| Strategist | `services/strategist/agent.py` | Chat Protocol + inline `generate_slate()` | Head Agent dispatches |
| Critic | `services/critic/agent.py` | Chat Protocol + inline `critique_slate()` | Head Agent dispatches |
| Publisher | `services/publisher/agent.py` | Chat Protocol + inline `publish_slots()` | Head Agent dispatches |
| Video Creator | `services/video_creator/agent.py` | Chat Protocol + `process_approved_slate()` | Head Agent dispatches |
| Carousel Creator | `services/carousel_creator/agent.py` | Inline `process_approved_slate()` | Head Agent dispatches |
| Design Director | `services/design_director/main.py` | Envelope-based `handle_request()` | Direct function call |
| Perf Harvester | `services/performance_harvester/agent.py` | Scheduled (uAgents Bureau) | Cron-like `harvest()` |

### 3.3  MCP Server (`src/mcp_server/`)

Has two tools (`generate_social_campaign`, `get_campaign_status`) but:
- Uses an **in-memory store** (not Supabase)
- `trigger_parent_agent()` is a stub — it updates the store but doesn't call the Head Agent
- Not connected to any frontend routes

### 3.4  Database Schema (Supabase)

Tables: `organizations`, `brands`, `content_slots`, `agent_messages`, `dead_letters`

Missing tables for: `campaigns`, `performance_records`, `design_assets`, `pdf_uploads`

---

## 4  Gap Inventory — Grouped by Priority

### P0 — Broken Core Workflows (Frontend calls → 404)

These are endpoints the frontend already calls. Without them, no real data flows.

---

#### P0-1: `GET /api/brands`

**Frontend caller:** `fetchBrand()` in `gateway.ts:237-245`

**Purpose:** Return the authenticated user's brand kit.

**Endpoint spec:**
```
GET /api/brands
Authorization: Bearer <supabase_jwt>

Response 200:
[
  {
    "brand_id": "uuid",
    "org_id": "uuid",
    "name": "string",
    "tagline": "string",
    "voice_description": "string",
    "target_audience": "string",
    "color_palette": ["#hex", ...],
    "logo_url": "string | null",
    "sample_captions": ["string", ...],
    "industry": "string"
  }
]
```

**Backend work:**
- Parse JWT → extract `org_id` from `app_metadata`
- Query Supabase: `SELECT brand_kit FROM brands WHERE org_id = $1`
- Return array of brand_kit JSONB values

**Agent connection:** None (pure DB read)

---

#### P0-2: `GET /api/slots`

**Frontend caller:** `fetchSlots()` in `gateway.ts:247-254`

**Purpose:** Return all content slots for the user's org, enriched with critic scores.

**Endpoint spec:**
```
GET /api/slots
Authorization: Bearer <supabase_jwt>

Response 200:
[
  {
    "slot_id": "uuid",
    "slot_number": 1,
    "caption": "string",
    "image_prompt": "string",
    "platform": "linkedin | x | instagram | tiktok | youtube",
    "scheduled_for": "ISO-8601",
    "image_url": "string | null",
    "status": "draft | proposed | rejected | approved | published | failed",
    "critic_scores": [{"axis": "string", "score": 0.0, "reasoning": "string"}, ...],
    "critic_average": 4.2,
    "critic_summary": "string"
  }
]
```

**Backend work:**
- Parse JWT → extract `org_id`
- Query: `SELECT * FROM content_slots WHERE org_id = $1 ORDER BY slot_number`
- Merge `critic_scores` JSONB column into each slot response
- Compute `critic_average` from scores if not stored

**Agent connection:** None (pure DB read)

---

#### P0-3: `GET /api/messages`

**Frontend caller:** `fetchMessages()` in `gateway.ts:256-263` — **polled every 3 seconds**

**Purpose:** Return agent-to-agent communication envelopes for the live feed.

**Endpoint spec:**
```
GET /api/messages
Authorization: Bearer <supabase_jwt>
Query params: ?limit=50 (optional, default 50)

Response 200:
[
  {
    "id": "uuid",
    "from_agent": "strategist | critic | publisher | video_creator",
    "to_agent": "string",
    "envelope_type": "string",
    "payload": {},
    "signature": "string",
    "created_at": "ISO-8601"
  }
]
```

**Backend work:**
- Parse JWT → extract `org_id`
- Query: `SELECT * FROM agent_messages WHERE org_id = $1 ORDER BY created_at DESC LIMIT $2`

**Agent connection:** None (pure DB read). Agents write to this table after each operation.

---

#### P0-4: `POST /api/rank-slots`

**Frontend caller:** `rankSlots()` in `gateway.ts:265-282`

**Purpose:** Use ASI:One LLM to rank approved slots by predicted performance.

**Endpoint spec:**
```
POST /api/rank-slots
Authorization: Bearer <supabase_jwt>
Content-Type: application/json

Request:
{
  "slot_ids": ["uuid", ...]
}

Response 200:
[
  {
    "slot_id": "uuid",
    "rank": 1,
    "reasoning": "string"
  }
]
```

**Backend work:**
- Parse JWT → extract `org_id`
- Fetch slots from DB by IDs (verify org ownership)
- Call ASI:One (OpenAI-compatible) with slot data + brand context
- Parse LLM response into `RankedSlot[]`
- Return ranked list

**Agent connection:** New — calls ASI:One API directly (similar to Strategist's client setup)

---

#### P0-5: `POST /api/trigger-publish`

**Frontend caller:** `triggerPublish()` in `gateway.ts:284-305`

**Purpose:** Publish selected approved slots to their target platforms.

**Endpoint spec:**
```
POST /api/trigger-publish
Authorization: Bearer <supabase_jwt>
Content-Type: application/json

Request:
{
  "slot_ids": ["uuid", ...]
}

Response 200:
[
  {
    "slot_id": "uuid",
    "platform": "linkedin | x | instagram",
    "success": true,
    "permalink": "string | null",
    "error": "string | null",
    "idempotency_key": "string"
  }
]
```

**Backend work:**
- Parse JWT → extract `org_id`
- Fetch slots from DB (verify org + status = "approved")
- Call `publish_slots()` from `services/publisher/agent.py`
- Update `content_slots.status` → "published" or "failed"
- Insert `publish_result` JSONB into each slot row
- Write an `agent_messages` row (envelope_type = "publish_result")
- Return results

**Agent connection:** `services/publisher/agent.py` → `publish_slots()` (inline mode) → Ayrshare API

---

### P1 — Missing Data Displays & Workflows

These features are partially wired in the UI but have no backend to power them.

---

#### P1-1: `POST /api/brands/extract`

**Frontend gap:** `onboarding-wizard.tsx:48-65` — "Extract Brand Kit with AI" is a `setTimeout` stub

**Purpose:** Accept brand basics + uploaded PDFs + social URLs, run LLM extraction, return a complete BrandKit.

**Endpoint spec:**
```
POST /api/brands/extract
Authorization: Bearer <supabase_jwt>
Content-Type: multipart/form-data

Fields:
  name: string
  industry: string
  tagline: string
  target_audience: string
  voice_description: string
  pdfs: File[]              (0..N PDF files)
  video_urls: string        (comma-separated)
  linkedin_url: string
  x_url: string
  instagram_url: string

Response 200:
{
  "brand_id": "uuid",
  "org_id": "uuid",
  "name": "string",
  "tagline": "string",
  "voice_description": "string",
  "target_audience": "string",
  "color_palette": ["#hex", ...],
  "logo_url": "string | null",
  "sample_captions": ["string", ...],
  "industry": "string"
}
```

**Backend work:**
- Accept multipart upload
- Parse PDFs → extract text (PyPDF2 or pdfplumber)
- Optionally scrape social profile URLs for bio/recent posts
- Call `extract_brand_kit()` from `services/head_agent/analysis.py` with combined context
- Insert brand into Supabase `brands` table
- Return the extracted BrandKit

**Agent connection:** `services/head_agent/analysis.py` → `extract_brand_kit()` → ASI:One LLM

---

#### P1-2: `POST /api/slots/{slot_id}/regenerate`

**Frontend gap:** `slot-detail.tsx:122` — "Regenerate Slot" button exists but does nothing

**Purpose:** Regenerate a rejected slot using Critic feedback.

**Endpoint spec:**
```
POST /api/slots/{slot_id}/regenerate
Authorization: Bearer <supabase_jwt>

Response 200:
{
  "slot_id": "uuid",
  "slot_number": 1,
  "caption": "string",
  "image_prompt": "string",
  "platform": "string",
  "scheduled_for": "ISO-8601",
  "image_url": null,
  "status": "proposed",
  "critic_scores": [...],
  "critic_average": 4.1,
  "critic_summary": "string"
}
```

**Backend work:**
- Fetch original slot + its critic verdict from DB
- Fetch the parent brand's BrandKit
- Call Strategist's `generate_slate()` in single-slot mode with critic feedback context
- Re-run Critic's `critique_slate()` on the new slot
- Update the slot row in DB (new caption, image_prompt, critic_scores, status)
- Write `agent_messages` rows for the regeneration flow
- Return updated slot

**Agent connection:** `services/strategist/agent.py` → `generate_slate()` then `services/critic/agent.py` → `critique_slate()`

---

#### P1-3: `POST /api/campaigns/generate`

**Frontend gap:** No campaign page in UI yet, but MCP server already defines `generate_social_campaign`

**Purpose:** Trigger the full Head Agent pipeline from the web UI (not just via MCP/ASI:One).

**Endpoint spec:**
```
POST /api/campaigns/generate
Authorization: Bearer <supabase_jwt>
Content-Type: application/json

Request:
{
  "brand_id": "uuid",
  "product_description": "string",
  "target_platform": "linkedin | x | instagram | tiktok | youtube",
  "content_type": "video | carousel | image | auto",
  "num_posts": 7
}

Response 202:
{
  "campaign_id": "string",
  "status": "queued",
  "message": "string"
}
```

**Backend work:**
- Validate brand ownership
- Create a `campaigns` row in Supabase (new table needed)
- Dispatch to Head Agent pipeline (or call `trigger_parent_agent()` from MCP tools)
- Return campaign_id for polling

**Agent connection:** `services/head_agent/agent.py` — full pipeline (intake → analysis → strategize → critique → publish → report)

**New DB table required:**
```sql
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id) NOT NULL,
    brand_id UUID REFERENCES brands(id) NOT NULL,
    campaign_id TEXT UNIQUE NOT NULL,
    status TEXT DEFAULT 'queued',
    stages JSONB DEFAULT '[]',
    result_summary TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

#### P1-4: `GET /api/campaigns/{campaign_id}/status`

**Purpose:** Poll campaign progress from the web UI.

**Endpoint spec:**
```
GET /api/campaigns/{campaign_id}/status
Authorization: Bearer <supabase_jwt>

Response 200:
{
  "campaign_id": "string",
  "overall_status": "queued | running | completed | failed",
  "stages": [
    {"stage": "intake", "status": "completed", "detail": "..."},
    {"stage": "analysis", "status": "running", "detail": "..."},
    ...
  ],
  "result_summary": "string"
}
```

**Agent connection:** Reads from `campaigns` table (stages updated by Head Agent via callbacks)

---

### P2 — Missing Supporting Features

---

#### P2-1: `GET /api/performance/{brand_id}`

**Purpose:** Surface performance analytics from the PerformanceHarvester.

**Endpoint spec:**
```
GET /api/performance/{brand_id}
Authorization: Bearer <supabase_jwt>

Response 200:
{
  "brand_id": "uuid",
  "top_formats": [{"format": "video", "avg_engagement": 4.2}, ...],
  "best_times": {"linkedin": "09:00", "x": "12:00"},
  "avoid_patterns": ["generic CTAs", ...],
  "records": [
    {
      "post_id": "string",
      "platform": "string",
      "published_at": "ISO-8601",
      "likes": 0,
      "shares": 0,
      "comments": 0,
      "reach": 0,
      "engagement_rate": 0.0
    }
  ]
}
```

**Backend work:**
- Run `build_performance_summary()` from `services/performance_harvester/summary.py`
- Query persisted `PerformanceRecord` data

**New DB table required:**
```sql
CREATE TABLE performance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id UUID REFERENCES brands(id) NOT NULL,
    post_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL,
    content_type TEXT,
    likes INT DEFAULT 0,
    shares INT DEFAULT 0,
    comments INT DEFAULT 0,
    reach INT DEFAULT 0,
    engagement_rate FLOAT DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(brand_id, post_id)
);
```

**Agent connection:** `services/performance_harvester/agent.py` → `harvest()` + `summary.py` → `build_performance_summary()`

---

#### P2-2: `POST /api/assets/generate`

**Purpose:** Trigger carousel or video generation for specific approved slots.

**Endpoint spec:**
```
POST /api/assets/generate
Authorization: Bearer <supabase_jwt>
Content-Type: application/json

Request:
{
  "slot_ids": ["uuid", ...],
  "asset_type": "carousel | video | auto"
}

Response 202:
{
  "job_id": "string",
  "status": "queued",
  "slots_queued": 3
}
```

**Backend work:**
- Fetch approved slots
- Route to `services/carousel_creator/agent.py` → `process_approved_slate()` or `services/video_creator/agent.py` → `process_approved_slate()` depending on `asset_type`
- Update `content_slots.image_url` with generated asset paths/URLs
- Return job tracking ID

**Agent connection:** Carousel Creator + Video Creator pipelines

---

#### P2-3: `POST /api/designs/request`

**Purpose:** Trigger the Design Director for brand asset generation (logos, headers, infographics).

**Endpoint spec:**
```
POST /api/designs/request
Authorization: Bearer <supabase_jwt>
Content-Type: application/json

Request:
{
  "task_description": "string",
  "task_type": "logo_variation | marketing_header | infographic | social_rebrand",
  "brand_id": "uuid",
  "platform": "linkedin | x | instagram | null",
  "inputs": {}
}

Response 202:
{
  "task_id": "string",
  "plan": {
    "steps": [{"step_id": "string", "agent": "string", "action": "string"}],
    "execution_order": "sequential"
  }
}
```

**Agent connection:** `services/design_director/main.py` → `handle_request()`

---

#### P2-4: `GET /api/dead-letters`

**Purpose:** Surface failed publish attempts for retry/debugging.

**Endpoint spec:**
```
GET /api/dead-letters
Authorization: Bearer <supabase_jwt>
Query params: ?resolved=false

Response 200:
[
  {
    "id": "uuid",
    "slot_id": "uuid",
    "error_message": "string",
    "error_code": "string",
    "retry_count": 0,
    "resolved": false,
    "created_at": "ISO-8601"
  }
]
```

**Agent connection:** None (pure DB read). Data written by Publisher on failures.

---

## 5  Database Schema Changes Required

### New Tables

| Table | Priority | Purpose |
|-------|----------|---------|
| `campaigns` | P1 | Track campaign pipeline runs from web UI |
| `performance_records` | P2 | Store post-level analytics from Ayrshare |

### Existing Table Modifications

| Table | Change | Priority |
|-------|--------|----------|
| `content_slots` | Add `video_url TEXT` column | P2 |
| `content_slots` | Add `carousel_urls TEXT[]` column | P2 |
| `agent_messages` | Add `carousel_creator`, `design_director`, `performance_harvester` to `from_agent` CHECK | P1 |
| `brands` | Add `source_pdf_urls TEXT[]` for stored uploads | P1 |

### New Migration: `00003_campaigns_and_assets.sql`

```sql
-- Campaign tracking
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id) NOT NULL,
    brand_id UUID REFERENCES brands(id) NOT NULL,
    campaign_id TEXT UNIQUE NOT NULL,
    status TEXT DEFAULT 'queued'
        CHECK (status IN ('queued', 'running', 'completed', 'failed')),
    stages JSONB DEFAULT '[]',
    result_summary TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Performance analytics
CREATE TABLE performance_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id UUID REFERENCES brands(id) NOT NULL,
    post_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL,
    content_type TEXT,
    likes INT DEFAULT 0,
    shares INT DEFAULT 0,
    comments INT DEFAULT 0,
    reach INT DEFAULT 0,
    engagement_rate FLOAT DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(brand_id, post_id)
);

-- Asset columns on content_slots
ALTER TABLE content_slots ADD COLUMN video_url TEXT;
ALTER TABLE content_slots ADD COLUMN carousel_urls TEXT[];

-- Expand agent_messages from_agent CHECK
ALTER TABLE agent_messages DROP CONSTRAINT agent_messages_from_agent_check;
ALTER TABLE agent_messages ADD CONSTRAINT agent_messages_from_agent_check
    CHECK (from_agent IN (
        'strategist', 'critic', 'publisher', 'video_creator',
        'carousel_creator', 'design_director', 'performance_harvester'
    ));

-- RLS + indexes
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_records ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_isolation" ON campaigns
    FOR ALL USING (org_id = (auth.jwt() -> 'app_metadata' ->> 'org_id')::uuid);
CREATE POLICY "brand_isolation" ON performance_records
    FOR ALL USING (brand_id IN (SELECT id FROM brands WHERE org_id = (auth.jwt() -> 'app_metadata' ->> 'org_id')::uuid));
CREATE INDEX idx_campaigns_org ON campaigns(org_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_perf_records_brand ON performance_records(brand_id);
CREATE INDEX idx_perf_records_published ON performance_records(published_at);
```

---

## 6  File Change Map

### Files to Create

| File | Purpose |
|------|---------|
| `gateway/routes/__init__.py` | Route package init |
| `gateway/routes/brands.py` | Brand CRUD endpoints |
| `gateway/routes/slots.py` | Content slot endpoints |
| `gateway/routes/messages.py` | Agent message feed endpoint |
| `gateway/routes/ranking.py` | ASI:One slot ranking endpoint |
| `gateway/routes/publish.py` | Publish trigger endpoint |
| `gateway/routes/campaigns.py` | Campaign management endpoints |
| `gateway/routes/performance.py` | Analytics endpoint |
| `gateway/routes/assets.py` | Asset generation endpoints |
| `gateway/routes/designs.py` | Design Director endpoint |
| `gateway/routes/dead_letters.py` | Dead letter queue endpoint |
| `gateway/auth.py` | JWT verification middleware (Supabase JWTs) |
| `gateway/db.py` | Supabase client helper (PostgREST or raw SQL) |
| `supabase/migrations/00003_campaigns_and_assets.sql` | New tables + column alterations |

### Files to Modify

| File | Change |
|------|--------|
| `gateway/main.py` | Replace placeholder with full FastAPI app, mount all route routers |
| `apps/web/lib/gateway.ts` | Remove mock data, ensure all calls go through gateway |
| `apps/web/components/onboarding/onboarding-wizard.tsx` | Wire `handleExtract()` to `POST /api/brands/extract` |
| `apps/web/components/calendar/slot-detail.tsx` | Wire "Regenerate Slot" button to `POST /api/slots/{id}/regenerate` |

### Files to Deprecate

| File | Reason |
|------|--------|
| Mock data block in `gateway.ts` (lines 19-233) | Replaced by real API calls |
| `src/mcp_server/campaign_store.py` (in-memory store) | Replace with Supabase-backed persistence |

---

## 7  Implementation Order

| Phase | Endpoints | Dependency |
|-------|-----------|------------|
| **Phase 1** | Gateway scaffold + auth middleware + DB helper | None |
| **Phase 2** | P0-1 (`/api/brands`), P0-2 (`/api/slots`), P0-3 (`/api/messages`) | Phase 1 |
| **Phase 3** | P0-4 (`/api/rank-slots`), P0-5 (`/api/trigger-publish`) | Phase 2 + ASI:One/Publisher agent |
| **Phase 4** | P1-1 (`/api/brands/extract`), P1-2 (`/api/slots/{id}/regenerate`) | Phase 2 + Strategist/Critic agents |
| **Phase 5** | P1-3, P1-4 (campaigns) | Phase 3 + Head Agent pipeline |
| **Phase 6** | P2-1 (performance), P2-2 (assets), P2-3 (designs), P2-4 (dead-letters) | Phase 5 + Harvester/Video/Carousel/Design agents |

Each phase can be developed and merged independently. Phase 2 alone unblocks the frontend from mock mode.
