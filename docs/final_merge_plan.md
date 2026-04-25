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

_(Updated during merging — see below)_

---
