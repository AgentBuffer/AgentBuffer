# AgentBuffer — 1-Page Design Doc

> **Buffer for autonomous brand agents.** You hire AI agents, not write posts.

## The idea, in one paragraph
A user onboards their brand once (Q&A + PDFs + past videos + linked socials). The app spawns a small team of AI agents *tied to that brand* that wake up on a schedule, generate on-brand image/video/carousel content, run it past a Critic agent that **must reject** weak work, then auto-publish. One brand → its own agents → posts go out while you sleep.

## The agent topology (this is the whole product)
```
   ┌───────────┐   proposes   ┌──────────┐  approved   ┌──────────┐
   │STRATEGIST │ ───────────▶ │  CRITIC  │ ──────────▶ │PUBLISHER │
   │ (plans    │              │ (rejects │             │ (posts   │
   │  weekly   │ ◀─── try ────│  ≥1 per  │             │  via     │
   │  slate)   │     again    │  demo)   │             │  Ayrshare│
   └───────────┘              └──────────┘             └────┬─────┘
                                                            ▼
                                                  LinkedIn · X · IG-queued
```
3 Python uAgents on Fly + Agentverse. Every handoff writes a signed envelope to an `agent_messages` ledger we render live.
