# AgentBuffer

> Buffer for autonomous brand agents. You hire AI agents, not write posts.

## Architecture

```
apps/web         Next.js 15 + Vercel + server actions + Supabase Auth
services/        strategist · critic · publisher  (Python uAgents on Fly)
gateway          read-only FastAPI, forwards user JWT
supabase/        Postgres + Storage + RLS on org_id
codegen/         Pydantic → TS via datamodel-code-generator
```

## Quick Start

### Prerequisites

- Node.js 20+
- pnpm 9+
- Python 3.12+
- uv

### Setup

```bash
# Install web dependencies
pnpm install

# Install Python dependencies
uv sync

# Copy environment variables
cp .env.example .env.local

# Run the web app
cd apps/web && pnpm dev
```

## Stack

| Layer | Choice |
|---|---|
| Web | Next.js 15 (App Router) + server actions on Vercel |
| Auth | Supabase Auth + Auth Hook |
| DB | Supabase Postgres + Storage + RLS via Auth Hook |
| Agent runtime | Python 3.12 uAgents on Fly.io |
| Agents | `services/strategist`, `services/critic`, `services/publisher` |
| Web-agents | read-only FastAPI gateway, forwards user JWT only |
| Types | Pydantic → TS via `datamodel-code-generator` in CI |
| Media | Nano Banana 2 (Gemini), Veo 3.1, Cloudinary |
| Publishing | Ayrshare → LinkedIn + X, IG "queued for review" |
| Repo | Monorepo with pnpm + uv |

## Team

Built at LA Hacks 2026.
