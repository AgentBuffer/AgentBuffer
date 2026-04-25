# Changelog

All notable changes to the AgentBuffer platform are documented in this file.

## [1.0.0] — 2026-04-25

### Multi-Agent Architecture

- **Cognition Agent** — New autonomous planning layer (`src/agents/`) that orchestrates tool selection across video, carousel, and design pipelines. Includes a planner module, tool wrappers for each pipeline, and 25+ unit tests.
- **Head Agent pipeline extensions** — Added approval gate (human-in-the-loop), image generation dispatch, slate regeneration, calendar commands, and BrandKit editing to the orchestration pipeline.
- **Strategist & Critic agents** — Existing agents now feed through the full pipeline: Strategist -> Critic -> Image Generation -> Approval Gate -> Publisher.

### Content Pipelines

- **Image Creator Service** (`services/image_creator/`) — New Google Imagen API integration for automated AI image generation. Supports platform-specific aspect ratios (3:4 Instagram, 16:9 landscape, 9:16 stories). Includes prompt adapter, Imagen client, and full test suite.
- **Direct Platform Publishing** — Replaced Ayrshare dependency with native platform adapters (`services/publisher/adapters/`) for Twitter/X, Meta (Facebook/Instagram), and LinkedIn. Each adapter handles authentication and API calls directly.
- **Supabase Storage uploads** — Publisher now uploads local image assets to Supabase Storage before publishing, returning public URLs for platform distribution.

### Web Dashboard (Next.js)

- **Keyboard-Centric FSM Keybind System** (`apps/web/lib/keybinds/`) — Finite state machine for agent streaming UI with 14 distinct keyboard bindings. Includes command palette (`Ctrl+K`), decision dock, pipeline switcher, state badge, kill-confirm toast, and cheat sheet overlay. Each keybind is a separate, independent handler.
- **Content Calendar** (`apps/web/app/dashboard/calendar/`) — Week grid view with platform filtering, slot detail panels, side-by-side comparison, and manual post addition via the head agent.
- **BrandKit Editor** — Living brand identity editor with voice editing, color palette management, and audience targeting. Changes propagate to the Strategist for future content generation.

### Gateway API

- **10 new REST route modules** (`gateway/routes/`) — brands, slots, messages, ranking, publish, campaigns, performance, assets, designs, dead_letters. All stubbed with schema-correct mock data matching `docs/backend_gap_analysis.md`.
- **Calendar endpoint** — `GET /brands/{brand_id}/calendar?week_start=YYYY-MM-DD` returns posts for a 7-day window.
- **CORS middleware** — Configured for cross-origin requests from the Next.js frontend.

### Database Migrations

- `00003_campaigns_and_assets.sql` — Campaign tracking and asset management tables.
- `00004_add_image_creator_agent.sql` — Image creator agent registration.
- `00005_platform_connections.sql` — Direct platform OAuth connection storage (replacing Ayrshare).

### Documentation

- `docs/cognition_architecture.md` — Cognition Agent architecture, pipeline audit, tool schemas, and refactoring strategy.
- `docs/backend_gap_analysis.md` — Comprehensive backend gap analysis with API route specifications.
- `docs/final_merge_plan.md` — Integration merge plan with full conflict resolution log.
- `docs/ux_state_machine.md` — UX state machine specification for keyboard-centric agent streaming.
- `docs/keybind_matrix.md` — Complete keybind reference matrix across all UI states.
- `docs/interaction_proposals.md` — Interaction design proposals for agent streaming UI.
- `docs/imagen_pipeline.md` — Google Imagen pipeline integration documentation.

### Infrastructure

- Removed Ayrshare API dependency — no longer requires `AYRSHARE_API_KEY`.
- All Python lint (`ruff check` + `ruff format`) and web lint (`eslint` + TypeScript `tsc --noEmit`) pass clean.
- 84 tests passing across video, carousel, design, and publisher test suites.
