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

*(Updated as merges proceed)*

### Step 1: `architecture/cognition-agent-plan`
- Status: Pending
- Conflicts: —

### Step 2: `chore/backend-gap-analysis`
- Status: Pending
- Conflicts: —

### Step 3: `devin/1777136906-brandkit-editor`
- Status: Pending
- Conflicts: —

### Step 4: `devin/1777141260-image-creator-service`
- Status: Pending
- Conflicts: —

### Step 5: `devin/1777138553-content-calendar`
- Status: Pending
- Conflicts: —

---

## Post-Merge Validation Checklist

- [ ] `pytest` — all test suites pass
- [ ] `ruff check` — no lint violations
- [ ] `ruff format --check` — formatting clean
- [ ] `pnpm lint && pnpm typecheck` — web app clean
- [ ] Main Agent → Cognition Agent routing works (mock test)
