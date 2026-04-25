# AgentBuffer — Design Doc

> **Buffer for autonomous brand agents.** You hire AI agents, not write posts.

## The idea, in one paragraph
A user onboards their brand once (Q&A + PDFs + past videos + linked socials). The app spawns a small team of AI agents *tied to that brand* that wake up on a schedule, generate on-brand image/video/carousel content, run it past a Critic agent that **must reject** weak work, then auto-publish. One brand → its own agents → posts go out while you sleep.

## The agent topology (this is the whole product)
```
                         ┌──────────────────────────┐
                         │        ASI:One            │
                         │  User chats here to       │
                         │  trigger marketing flows  │
                         └─────────────┬────────────┘
                                       │ Chat Protocol
                                       ▼
                    ┌──────────────────────────────────┐
                    │     HEAD AGENT (Orchestrator)     │
                    │  "Marketing Director"             │
                    │                                   │
                    │  • Parses business description    │
                    │  • Generates marketing analysis   │
                    │  • Dispatches sub-agents          │
                    │  • Streams progress to user       │
                    └──┬────────┬────────┬─────┬───────┘
                       │        │        │     │
              ┌────────┘   ┌────┘   ┌────┘     └──────┐
              ▼            ▼        ▼                  ▼
     ┌──────────────┐ ┌─────────┐ ┌───────────┐ ┌──────────┐
     │  STRATEGIST  │ │ CRITIC  │ │  VIDEO    │ │PUBLISHER │
     │              │ │         │ │  CREATOR  │ │          │
     │ Plans weekly │ │ 5-axis  │ │ Veo API   │ │ Ayrshare │
     │ content slate│ │ scoring │ │ per-plat  │ │ multi-   │
     │ using LLM    │ │ rejects │ │ trends    │ │ platform │
     │              │ │ weak    │ │           │ │          │
     └──────────────┘ └─────────┘ └───────────┘ └──────────┘
```
All agents registered on Agentverse with Chat Protocol. Discoverable via ASI:One.

## Pipeline flow
1. User chats with Head Agent via ASI:One
2. Head Agent extracts BrandKit from free-form text (LLM)
3. Head Agent generates MarketingAnalysis (LLM)
4. Head Agent dispatches to Strategist → returns 7-day Slate
5. Head Agent dispatches to Critic → scores & rejects weak slots
6. Head Agent dispatches to Video Creator → generates platform videos (Veo)
7. Head Agent dispatches to Publisher → schedules posts (Ayrshare)
8. Head Agent compiles final report and sends to user

Intermediate status updates streamed to user at each stage.
State managed via ctx.storage with session_id for async actor-model handoffs.
