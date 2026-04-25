# Staging Integration Plan

**Branch:** `release/staging-integration`  
**Base:** `main`  
**Date:** 2026-04-25  

---

## Branch Inventory

| # | Branch | Description | Key Files Touched |
|---|--------|-------------|-------------------|
| 1 | `architecture/cognition-agent-plan` | Cognition Agent PoC — tool wrappers, planner, architecture docs, 25 tests | `src/agents/`, `tests/`, `docs/cognition_architecture.md` (all new) |
| 2 | `chore/backend-gap-analysis` | Gateway route expansion — auth, db, campaign/brand/slot/publish routes, migration | `gateway/main.py`, `gateway/routes/`, `gateway/auth.py`, `gateway/db.py`, `supabase/migrations/` |
| 3 | `devin/1777136906-brandkit-editor` | BrandKit editor — refactored head_agent, strategist, critic; new brandkit_store | `services/head_agent/agent.py`, `services/shared/models.py`, `services/strategist/agent.py`, `services/critic/agent.py` |
| 4 | `devin/1777141260-image-creator-service` | Image Creator service — Google Imagen API integration, prompt adapter, tests | `services/image_creator/` (new), `services/head_agent/agent.py`, `services/shared/models.py`, `services/publisher/agent.py` |
| 5 | `devin/1777138553-content-calendar` | Content calendar UI — week grid, platform filter, head_agent calendar commands | `apps/web/`, `gateway/main.py`, `services/head_agent/agent.py`, `services/head_agent/config.py` |

---

## Merge Sequence

### Rationale
1. **Foundational architecture first** — new directories with zero overlap
2. **Infrastructure/gateway expansion** — backend plumbing before feature branches
3. **Core service refactoring** — models & head_agent restructuring  
4. **Standalone pipelines** — image creator builds on top of updated models
5. **Frontend/backend glue** — calendar UI ties gateway + head_agent together

### Order

| Step | Branch | Risk | Expected Conflicts |
|------|--------|------|--------------------|
| 1 | `architecture/cognition-agent-plan` | 🟢 Low | None — entirely new `src/agents/` and `tests/` dirs |
| 2 | `chore/backend-gap-analysis` | 🟢 Low | None — gateway routes are additive; `gateway/main.py` minor overlap |
| 3 | `devin/1777136906-brandkit-editor` | 🟡 Medium | `services/head_agent/agent.py` heavy refactor; `services/shared/models.py` |
| 4 | `devin/1777141260-image-creator-service` | 🟡 Medium | `services/head_agent/agent.py`, `services/shared/models.py` (vs. brandkit changes), `services/head_agent/config.py` |
| 5 | `devin/1777138553-content-calendar` | 🔴 High | `gateway/main.py` (vs. gap-analysis), `services/head_agent/agent.py` (vs. brandkit+image), `services/head_agent/config.py` |

---

## Conflict Resolution Log

### Step 1: `architecture/cognition-agent-plan`
- **Status:** Merged — clean, no conflicts
- **Tests:** 119 passed

### Step 2: `chore/backend-gap-analysis`
- **Status:** Merged — clean, no conflicts
- **Tests:** 119 passed

### Step 3: `devin/1777136906-brandkit-editor`
- **Status:** Merged — clean, no conflicts
- **Tests:** 119 passed

### Step 4: `devin/1777141260-image-creator-service`
- **Status:** Merged — 2 conflicts resolved
- **Conflicts:**
  - `README.md` (6 conflict regions): Combined detailed DeepWiki-style README (HEAD) with Image Creator additions. Added Image Creator to architecture diagram, agent roster, stage details, project structure, tech stack, and environment variables section.
  - `uv.lock`: Regenerated lockfile via `uv lock` after taking theirs.
- **Post-merge fix:** Resolved 2 E501 line-length violations in `services/head_agent/agent.py` (long string literals in image request/reply handlers).
- **Tests:** 142 passed (23 new image_creator tests)

### Step 5: `devin/1777138553-content-calendar`
- **Status:** Merged — 2 conflicts resolved + missing functions restored
- **Conflicts:**
  - `gateway/main.py`: Combined comprehensive route-based gateway (from gap-analysis) with calendar endpoint (from content-calendar). Added `os`, `datetime`, `Query` imports; added `_monday_of()` helper and `/brands/{brand_id}/calendar` endpoint alongside all existing route routers.
  - `services/head_agent/agent.py`: Merged BrandKit edit commands (brandkit-editor) with calendar/add-post commands (content-calendar) and approval flow. The brandkit-editor branch had refactored the head_agent and removed the approval flow, which the content-calendar branch depended on.
- **Post-merge fix:** Restored 5 missing approval flow functions (`_handle_approval_reply`, `_parse_approval_text`, `_match_slot_id`, `_process_approval_decisions`, `_finalize_approved_slots`) and added missing `import re`.
- **Tests:** 142 passed

---

## Post-Merge Validation Checklist

- [x] `pytest` — 142 tests pass (video, carousel, design, image_creator, cognition agent)
- [x] `ruff check` — no lint violations
- [x] `ruff format` — formatted conflict-resolved files
- [x] `pnpm lint` — web app clean (2 pre-existing warnings only)
- [x] `pnpm typecheck` — web app clean
- [ ] Main Agent → Cognition Agent routing works (mock test)
