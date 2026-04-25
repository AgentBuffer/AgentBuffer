# AgentBuffer

> **Buffer for autonomous brand agents.** You hire AI agents, not write posts.

AgentBuffer is a multi-agent marketing automation platform built on [Fetch.ai's Agentverse](https://agentverse.ai). A business describes itself in natural language via [ASI:One](https://asi1.ai), and a team of AI agents generates a complete marketing strategy, creates platform-optimized content, quality-checks every piece, and schedules publishing — all autonomously.

## Architecture

```
User (ASI:One) → Head Agent → Strategist → Critic → Video Creator → Publisher
                     ↑                        |
                     └── retry on rejection ──┘
```

**5 agents**, all registered on Agentverse with Chat Protocol:

| Agent | Role | Location |
|---|---|---|
| **Marketing Director** | Orchestrator — parses brand, generates analysis, dispatches sub-agents | `services/head_agent/` |
| **Strategist** | Generates 7-day content slates with platform-optimized captions | `services/strategist/` |
| **Critic** | 5-axis quality scoring, rejects weak content (must reject ≥1) | `services/critic/` |
| **Video Creator** | Platform-specific video generation via Google Veo | `services/video_creator/` |
| **Publisher** | Multi-platform publishing via direct platform APIs | `services/publisher/` |

## Quick Start

```bash
# 1. Install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install uagents uagents-core openai pydantic google-genai

# 2. Configure environment
cp .env.example .env
# Edit .env with your ASI:One API key

# 3. Run the Head Agent (inline mode — all agents in one process)
PYTHONPATH=. python services/head_agent/agent.py

# 4. Or run agents separately for distributed mode
PYTHONPATH=. python services/strategist/agent.py &
PYTHONPATH=. python services/critic/agent.py &
PYTHONPATH=. python services/head_agent/agent.py
```

## Project Structure

```
├── services/
│   ├── head_agent/       # Orchestrator agent (entry point)
│   ├── strategist/       # Content planning agent
│   ├── critic/           # Quality control agent
│   ├── video_creator/    # Video generation agent (Veo API)
│   ├── publisher/        # Social media publishing agent (Direct Platform APIs)
│   └── shared/           # Pydantic models shared across agents
├── apps/web/             # Next.js dashboard (bonus UI)
├── gateway/              # FastAPI gateway
└── supabase/             # Database schema
```

## Tech Stack

- **Agent Framework**: Fetch.ai uAgents + Agentverse Chat Protocol
- **LLM**: ASI:One (OpenAI-compatible API)
- **Video**: Google Veo API
- **Publishing**: Direct Platform APIs (X, Instagram, LinkedIn, TikTok, YouTube, Bluesky)
- **Frontend**: Next.js 15, React, Tailwind CSS
- **Database**: Supabase (PostgreSQL)

## Hackathon: Fetch.ai Agentverse Prize

This project demonstrates:
- Multi-agent orchestration with reasoning and tool execution
- All agents registered on Agentverse with mandatory Chat Protocol
- Discoverable and usable through ASI:One — no custom frontend required
- Real-world problem: automated marketing content pipeline for businesses
