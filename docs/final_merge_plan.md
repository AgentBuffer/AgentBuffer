# Final Integration Merge Plan — `release/v1-final-integration`

**Date:** 2026-04-25
**Base branch:** `main` (commit `ed0e2d9`)
**Target branch:** `release/v1-final-integration`

---

## Branch Inventory

| # | Branch | Category | Description |
|---|--------|----------|-------------|
| 1 | `architecture/cognition-agent-plan` | Backend / Architecture | Cognition Agent PoC — planner, tool wrappers, 25 tests |
| 2 | `chore/backend-gap-analysis` | Backend / Architecture | Gap analysis doc + stubbed gateway routes (publish, ranking, slots, campaigns) |
| 3 | `devin/1777141260-image-creator-service` | Backend / Pipeline | Image Creator service (Google Imagen API), prompt adapter, publisher tweaks |
| 4 | `devin/1777152757-migrate-off-ayrshare` | Backend / Pipeline | Replace Ayrshare with direct platform APIs (Twitter, Meta, LinkedIn) |
| 5 | `devin/1777136906-brandkit-editor` | Backend + Frontend | BrandKit editor — brandkit_commands, brandkit_store, shared models update |
| 6 | `devin/1777138553-content-calendar` | Frontend / UX | Content calendar — week grid, platform filter, head agent commands |
| 7 | `chore/ux-web-planning` | Frontend / UX | Keyboard-centric FSM keybind system for agent streaming UI (Web TUI) |

> **Note:** `release/staging-integration` is a previous integration attempt and will NOT be merged — we are re-integrating from scratch for a clean history.

---

## Merge Sequence

### Phase 1 — Backend & Architecture (branches 1–4)

These branches establish the core agent framework, API routes, and pipeline services. They must land first so that frontend branches can bind to finalized backend schemas.

1. **`architecture/cognition-agent-plan`** — Foundation: agent planner + tool abstractions
2. **`chore/backend-gap-analysis`** — Gateway route stubs that depend on shared models
3. **`devin/1777141260-image-creator-service`** — New image_creator service + publisher changes + shared model updates
4. **`devin/1777152757-migrate-off-ayrshare`** — Publisher rewrite (touches same files as #3, potential conflicts in `publisher/agent.py` and `shared/models.py`)

### Phase 2 — Frontend & UX (branches 5–7)

5. **`devin/1777136906-brandkit-editor`** — BrandKit editing (touches `shared/models.py`, `strategist/agent.py`)
6. **`devin/1777138553-content-calendar`** — Calendar UI + gateway + head_agent commands
7. **`chore/ux-web-planning`** — **LAST** — Keyboard FSM keybinds for agent streaming UI. This is merged last because it layers keyboard event listeners on top of the finalized UI components. **CRITICAL: Do NOT combine individual keybinds — each keyboard binding must remain a separate, distinct handler.**

---

## Anticipated Conflict Zones

| Files | Branches | Strategy |
|-------|----------|----------|
| `services/publisher/agent.py` | #3 (image-creator) vs #4 (migrate-off-ayrshare) | Adopt #4's direct-API rewrite; port #3's image upload logic into the new publisher |
| `services/shared/models.py` | #3, #4, #5 | Merge all model additions — keep all new fields from every branch |
| `gateway/main.py` | #2, #6, #7 | Accumulate all route registrations — no removals |
| `services/head_agent/agent.py` | #5, #6, #7 | Preserve all new command handlers; keybind listeners (#7) must NOT be combined |
| `README.md` | Multiple | Accept latest main README; append any new docs references |
| `uv.lock` | #3 | Regenerate after final merge via `uv sync` |

---

## Conflict Resolution Log

### Merge #1 — `architecture/cognition-agent-plan`
- **Clean merge** — no conflicts.

### Merge #2 — `chore/backend-gap-analysis`
- **Clean merge** — no conflicts.

### Merge #3 — `devin/1777141260-image-creator-service`
- **README.md**: Accepted image-creator branch version (includes Imagen pipeline docs).
- **services/shared/models.py**: Kept `PerformanceRecord` + `BrandPerformanceSummary` from main alongside new `TrendContext`/`VideoRequest`/`ImageResult` models.
- **services/head_agent/agent.py**: Kept approval gate flow from main. Added `IMAGE_CREATOR_ADDRESS` import, `[IMAGE_REPLY:]` handler, and `_dispatch_image_generation` call before the approval gate in both critic paths.
- **uv.lock**: Accepted image-creator lock.

### Merge #4 — `devin/1777152757-migrate-off-ayrshare`
- **README.md**: Accepted migrate-off-ayrshare version.
- **services/publisher/agent.py**: Adopted direct platform API approach (`get_adapter` + `_publish_slot`), removed `_publish_via_ayrshare` and `AYRSHARE_API_KEY`. Preserved `_upload_to_storage` (needed by image-creator for Supabase Storage uploads) and Supabase env vars.

### Merge #5 — `devin/1777136906-brandkit-editor`
- **services/head_agent/agent.py** (imports): Kept both `IMAGE_CREATOR_ADDRESS` and `PUBLISHER_ADDRESS`.
- **services/head_agent/agent.py** (pipeline flow): Brandkit-editor simplified the pipeline by removing approval gate, image dispatch, and publishing. Restored all of these from the integration branch while accepting brandkit command routing, `_try_brandkit_command`, and `load_brandkit` integration.
- **services/shared/models.py**: Kept `PerformanceRecord` + `BrandPerformanceSummary` (brandkit-editor had removed them).
- **Report footer**: Kept full pipeline chain reference (direct platform APIs).

### Merge #6 — `devin/1777138553-content-calendar`
- **gateway/main.py**: Kept full route-based gateway with all 10 mounted routers from integration. Added calendar endpoint (`/brands/{brand_id}/calendar`), `_monday_of` helper, and `USE_APPROVAL_QUEUE` env var from content-calendar.
- **services/head_agent/agent.py**: Kept `regenerate slate` command from integration. Added `show calendar` and `add post` commands from content-calendar. Preserved approval gate flow for existing sessions.

### Merge #7 — `chore/ux-web-planning`
- **Clean merge** — no conflicts. All 14 keybind definitions preserved as separate, distinct handlers (NOT combined). Files added: 19 new files under `apps/web/components/keybinds/`, `apps/web/lib/keybinds/`, and `docs/`.

### Post-Merge Fixes
- Added missing `import re` in `head_agent/agent.py`.
- Added missing `_remove_from_active_approvals` function.
- Fixed 3 E501 line-length violations.
- Ran `ruff format` on 3 files.
- Renumbered duplicate `00003_*` migrations to `00003`, `00004`, `00005`.

---
