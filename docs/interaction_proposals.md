# Interaction Proposals — Keyboard-First Web Paradigms

> Novel interaction patterns for the AgentBuffer web dashboard, designed for
> power users on 60% keyboards. Every proposal prioritizes keyboard-first
> operation, deliberate activation, and visual clarity during agent streaming.

---

## 1. Overview

This document proposes concrete interaction designs for the AgentBuffer
dashboard. Each proposal specifies the activation chord, the visual rendering,
the user experience, the FSM states where it is active, and how it integrates
with the state machine defined in `docs/ux_state_machine.md` and the keybind
matrix in `docs/keybind_matrix.md`.

---

## 2. Rapid Q&A Decision Mechanics

When the agent pauses to ask the user a question, the UI transitions from
`AGENT_STREAMING` to `AWAITING_USER_DECISION`. This section defines the full
interaction flow for that state.

### 2.1 Visual Layout — The Decision Dock

The Decision Dock is **not** a traditional modal dialog. It is an inline,
focus-locked panel that slides up from the bottom of the streaming output area,
similar to a command palette but contextual to the agent's question.

```
┌──────────────────────────────────────────────────────────┐
│  Streaming Output Area                                   │
│                                                          │
│  Agent: "I've drafted two caption variants. Which        │
│  direction do you prefer?"                               │
│                                                          │
│  ... (last streamed token) ...                           │
│                                                          │
├──────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────┐  │
│  │  DECISION DOCK                    [aria-modal]     │  │
│  │                                                    │  │
│  │  "Which caption direction do you prefer?"          │  │
│  │                                                    │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │ ▸ Option A: Playful, emoji-heavy, Gen-Z     │  │  │
│  │  │   voice with trending slang                  │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │   Option B: Professional, benefit-focused,   │  │  │
│  │  │   clear CTA with brand consistency           │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  │                                                    │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │  Or type a free-form answer...               │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  │                                                    │  │
│  │  Ctrl+J/K navigate · Ctrl+Shift+Enter confirm     │  │
│  │  Ctrl+Shift+Y yes · Ctrl+Shift+N no               │  │
│  │  Ctrl+Shift+Escape dismiss                         │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

#### Components

1. **Question Text** — The agent's question, rendered large and readable at the
   top of the dock. Uses the same typography as the streaming output for visual
   continuity.

2. **Option Cards** — Selectable cards representing the agent's proposed
   options. Each card has:
   - A selection indicator (`▸` for the highlighted card)
   - The option text
   - A focus ring when highlighted via `Ctrl+J` / `Ctrl+K`
   - `role="option"` and `aria-selected` for accessibility

3. **Free-Form Input** — A text input below the option cards for free-form
   answers (visible only when the question type allows it). Auto-focuses when
   the user starts typing (any alphanumeric key while no card navigation is in
   progress).

4. **Keybind Hint Bar** — A compact bar at the bottom showing all available
   chords in the current state. Updates dynamically based on whether a card or
   the text input is focused.

### 2.2 Selection Mechanics

#### Yes/No Questions

For binary questions, the dock renders two cards ("Yes" / "No") and accepts
direct chords:

- `Ctrl+Shift+Y` — Selects "Yes" and immediately submits.
- `Ctrl+Shift+N` — Selects "No" and immediately submits.
- `Ctrl+J` / `Ctrl+K` + `Ctrl+Shift+Enter` also works for consistency.

#### List Selection

For multi-option questions:

- `Ctrl+J` — Move highlight down the option list (vim-style).
- `Ctrl+K` — Move highlight up the option list (vim-style).
- `Ctrl+Shift+Enter` — Confirm the highlighted option and submit.
- Selection wraps around (last item → first item on `Ctrl+J`).

#### Free-Form Input

When the question type allows free-form answers:

- The text input is present but not initially focused (card navigation is the
  default).
- Typing any alphanumeric key shifts focus to the text input.
- `Ctrl+Enter` submits the free-form answer.
- `Escape` returns focus from the text input back to card navigation (safe
  because this is within the Decision Dock, not a focus-trap escape).

### 2.3 Safety

- **No accidental dismissal** — The Decision Dock cannot be dismissed by
  `Escape` alone. `Ctrl+Shift+Escape` is required to dismiss without answering.
- **Dismiss transitions to `AGENT_PAUSED`** — Dismissing the dock does **not**
  return to `IDLE`. The agent remains paused, allowing the user to re-engage or
  steer. This prevents accidental loss of an in-progress run.
- **No auto-selection** — If the user navigates cards but doesn't press
  `Ctrl+Shift+Enter`, nothing is submitted. Card highlight is purely visual.

### 2.4 Timeout Behavior

If the user does not respond within a configurable timeout (default: 60
seconds):

1. **30 seconds** — The dock's border transitions from neutral to amber with a
   gentle pulse. A small "Waiting for your input..." label appears.
2. **60 seconds** — The pulse intensifies and the label changes to "Agent is
   still waiting...". An optional audio cue (subtle chime, configurable off)
   plays.
3. **No auto-dismiss** — The dock never auto-dismisses or auto-selects. The
   agent remains paused indefinitely until the user acts.
4. **No escalation** — The timeout is purely visual. It does not change the FSM
   state or trigger any agent behavior.

> **Design philosophy:** Urgency is communicated visually, never through forced
> action. The user is always in control of when to respond.

---

## 3. Novel Keybind Interactions

### 3.1 Global Command Palette — `Ctrl+K`

A VS Code / Linear-style command palette for rapid navigation and action
execution.

#### Chord & States

- **Chord:** `Ctrl+K`
- **Active in:** `IDLE`, `REVIEWING`
- **Dismissed by:** `Escape` (safe — non-destructive context, no focus trap)

#### Visual Rendering

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│          ┌──────────────────────────────────┐            │
│          │  ▸ Search actions...             │            │
│          ├──────────────────────────────────┤            │
│          │    Start new agent run           │            │
│          │    View past runs                │            │
│          │  ▸ Switch pipeline → Video       │            │
│          │    Switch pipeline → Carousel    │            │
│          │    Switch pipeline → Design      │            │
│          │    Open settings                 │            │
│          │    Jump to agent output #12      │            │
│          ├──────────────────────────────────┤            │
│          │  Ctrl+J/K navigate · Enter sel.  │            │
│          └──────────────────────────────────┘            │
│                                                          │
│          (background dimmed, not inert)                   │
└──────────────────────────────────────────────────────────┘
```

#### User Experience

1. User presses `Ctrl+K` in `IDLE` or `REVIEWING`.
2. A centered overlay appears with a text input auto-focused.
3. The user types to fuzzy-search available actions.
4. Results filter in real-time (client-side fuzzy matching).
5. `Ctrl+J` / `Ctrl+K` navigate the results list (vim-style).
6. `Enter` executes the selected action.
7. `Escape` dismisses the palette without executing anything.

#### Actions Registry

The palette searches over a flat list of registered actions:

| Action                    | Category    | Description                            |
|---------------------------|-------------|----------------------------------------|
| Start new agent run       | Agent       | Opens the prompt input (→ COMPOSING)   |
| View past runs            | Navigation  | Opens the run history panel             |
| Switch pipeline → Video   | Pipeline    | Activates the Video pipeline           |
| Switch pipeline → Carousel | Pipeline   | Activates the Carousel pipeline        |
| Switch pipeline → Design  | Pipeline    | Activates the Design pipeline          |
| Open settings             | Navigation  | Opens the settings page                |
| Jump to output #N         | Navigation  | Scrolls to a specific agent output     |
| Show keybind cheat sheet  | Help        | Opens the `Ctrl+Shift+/` overlay       |

### 3.2 Pipeline Switcher — `Ctrl+Shift+P`

A horizontal tab-bar overlay for switching between the Video, Carousel, and
Design pipelines.

#### Chord & States

- **Chord:** `Ctrl+Shift+P`
- **Active in:** `IDLE`, `REVIEWING`, `AGENT_STREAMING` (read-only peek)
- **Direct jump:** `Ctrl+1` / `Ctrl+2` / `Ctrl+3` (only when switcher is open)

#### Visual Rendering

```
┌──────────────────────────────────────────────────────────┐
│  ┌────────────────────────────────────────────────────┐  │
│  │  PIPELINE SWITCHER                                 │  │
│  │                                                    │  │
│  │  [1] Video         [2] Carousel      [3] Design   │  │
│  │   ● active           ○ idle           ⚠ error     │  │
│  │   Last: 2m ago       Last: 1h ago     Last: 5m    │  │
│  │                                                    │  │
│  │  Ctrl+1/2/3 jump · Escape dismiss                  │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  (main content visible below)                            │
└──────────────────────────────────────────────────────────┘
```

#### User Experience

1. User presses `Ctrl+Shift+P`.
2. A horizontal tab bar slides down from the top of the viewport.
3. Each pipeline tab shows:
   - Pipeline name
   - Status badge: `●` active (green), `○` idle (gray), `⚠` error (red)
   - Last run timestamp (relative, e.g., "2m ago")
4. `Ctrl+1`, `Ctrl+2`, `Ctrl+3` directly select a pipeline.
5. `Escape` dismisses without switching.

#### Read-Only Mode in AGENT_STREAMING

When triggered during `AGENT_STREAMING`, the switcher opens in **read-only
peek** mode:

- Pipeline tabs are visible but not selectable (grayed out, no focus ring).
- Status badges and timestamps are still shown.
- A label reads "Peek only — switch after run completes".
- `Escape` dismisses. `Ctrl+1/2/3` are no-ops.

> **Rationale:** Switching pipelines during an active stream would disrupt the
> agent run. Peek mode lets the user check on other pipelines without
> interrupting the current one.

### 3.3 Agent Layer Toggle — `Ctrl+Shift+L`

Toggles an "X-ray" split-pane view showing raw agent communication alongside
polished output.

#### Chord & States

- **Chord:** `Ctrl+Shift+L`
- **Active in:** `AGENT_STREAMING`, `REVIEWING`
- **Toggle:** Press again to return to single-pane view.

#### Visual Rendering

```
┌────────────────────────────┬─────────────────────────────┐
│  Formatted Output          │  Raw Agent Log              │
│                            │                             │
│  "Here's your weekly       │  {                          │
│  content slate for the     │    "envelope_type":         │
│  spring campaign..."       │      "approved_slate",      │
│                            │    "from_agent":            │
│  ┌──────────────────────┐  │      "strategist",          │
│  │  Content Slot #1     │  │    "to_agent":              │
│  │  Platform: Instagram │  │      "video_creator",       │
│  │  Caption: "Spring    │  │    "payload": {             │
│  │  into savings..."    │  │      "slots": [...]         │
│  └──────────────────────┘  │    }                        │
│                            │  }                          │
│  ┌──────────────────────┐  │                             │
│  │  Content Slot #2     │  │  ← token 147 streaming     │
│  │  Platform: TikTok    │  │                             │
│  └──────────────────────┘  │  [strategist → critic]      │
│                            │  [critic → video_creator]   │
├────────────────────────────┴─────────────────────────────┤
│  Ctrl+Shift+L to close X-ray · Ctrl+Shift+/ for help    │
└──────────────────────────────────────────────────────────┘
```

#### User Experience

1. User presses `Ctrl+Shift+L` during streaming or review.
2. The main content area splits vertically (50/50 by default).
3. **Left pane** — Formatted, polished output (same as the normal view).
4. **Right pane** — Raw agent communication log:
   - `AgentEnvelope` JSON objects, syntax-highlighted
   - Token-by-token streaming indicator (during `AGENT_STREAMING`)
   - Inter-agent message routing: `[from_agent → to_agent]` labels
   - Timestamps on each envelope
5. During `AGENT_STREAMING`, both panes scroll in sync as new content arrives.
6. Press `Ctrl+Shift+L` again to collapse back to single-pane view.

#### Use Cases

- **Debugging** — When the agent produces unexpected output, the raw log shows
  exactly which envelopes were exchanged and in what order.
- **Understanding agent reasoning** — The raw log reveals intermediate thoughts,
  critic rejections, and retry loops that the formatted view abstracts away.
- **Power-user transparency** — Advanced users who want full visibility into the
  multi-agent pipeline can leave X-ray mode on permanently.

### 3.4 Inline Annotation Mode — `Ctrl+Shift+;`

Allows the user to select spans of agent output and attach notes or corrections
that feed back into the next agent run.

#### Chord & States

- **Chord:** `Ctrl+Shift+;`
- **Active in:** `REVIEWING`
- **Exit:** `Ctrl+Shift+;` again (toggle) or `Escape` (non-destructive)

#### Visual Rendering

```
┌──────────────────────────────────────────────────────────┐
│  ANNOTATION MODE ACTIVE                          [exit]  │
│                                                          │
│  Agent output:                                           │
│                                                          │
│  "Here's your weekly content slate for the spring        │
│  campaign. I've ░░░░░░░░░░░░░░░░░░░░░░░░ to maximize    │
│  engagement with     ┌──────────────────────────┐        │
│  your Gen-Z          │ 📝 "This tone is too     │        │
│  audience on         │ formal for TikTok —      │        │
│  TikTok and          │ use more slang"          │        │
│  Instagram."         │                          │        │
│                      │ Ctrl+Enter save          │        │
│                      └──────────────────────────┘        │
│                                                          │
│  Annotations: 1 saved · 0 pending                        │
│  Ctrl+Shift+; exit · Ctrl+Enter save · Escape cancel     │
└──────────────────────────────────────────────────────────┘

  ░░░ = highlighted / selected span
```

#### User Experience

1. User presses `Ctrl+Shift+;` in `REVIEWING` state.
2. The output area enters annotation mode:
   - A top bar reads "ANNOTATION MODE ACTIVE" with an exit indicator.
   - Output text becomes selectable (click-and-drag or Shift+arrow).
3. User selects a span of text.
4. A small inline input anchors to the selection, floating just below the
   highlighted span.
5. User types a note or correction in the inline input.
6. `Ctrl+Enter` saves the annotation. The highlight persists with a subtle
   background color and a small annotation icon.
7. `Escape` cancels the current annotation without saving (safe — only discards
   the in-progress note, does not exit annotation mode).
8. `Ctrl+Shift+;` again exits annotation mode entirely.

#### Annotation Storage & Feedback Loop

- Saved annotations are stored as structured objects:
  ```json
  {
    "run_id": "run-abc123",
    "span_start": 142,
    "span_end": 189,
    "original_text": "optimized the posting schedule",
    "annotation": "This tone is too formal for TikTok — use more slang",
    "created_at": "2025-01-15T10:30:00Z"
  }
  ```
- Annotations are displayed as subtle highlights in the output when viewing past
  runs.
- When starting a new agent run, saved annotations from the previous run are
  automatically included in the agent context as correction signals, enabling
  the agent to learn from user feedback within a session.

---

## 4. 60% Keyboard Philosophy Summary

Every interaction in this document was designed with the HHKB 60% layout as the
primary input device. The design choices reflect three core ergonomic principles:

### 4.1 Control on Home Row

The HHKB places Control at the Caps Lock position — directly under the left
pinky on the home row. This makes `Ctrl+Shift+<key>` chords natural two-finger
stretches rather than awkward three-key contortions:

- **Left pinky** holds `Ctrl` (home row, no movement).
- **Left ring finger** holds `Shift` (one row down, minimal stretch).
- **Right hand** presses the action key on the home row (`H`, `J`, `K`, `L`,
  `A`, `Y`, `N`).

This is why every critical operational chord (`Ctrl+Shift+H` for Halt,
`Ctrl+Shift+K` for Kill, `Ctrl+Shift+A` for Approve) uses home-row keys that
the right hand can reach without looking.

### 4.2 Vim-Style Navigation

The HHKB has no dedicated arrow keys — they live behind an Fn layer that
requires a pinky stretch to the bottom-right corner. Vim-style `J`/`K`
navigation is native to HHKB users:

- `Ctrl+J` (down) and `Ctrl+K` (up) for list navigation in the Decision Dock
  and Command Palette.
- No reliance on `Page Up` / `Page Down` / `Home` / `End` which don't exist on
  the HHKB without Fn.

### 4.3 All Critical Actions Within Reach

Every frequently-used chord can be executed without the fingers leaving the home
row area:

```
Left hand (modifiers):          Right hand (action keys):
┌───────┐                       ┌─────────────────────────┐
│ Ctrl  │ (pinky, home row)     │  H — Halt & Pivot       │
│ Shift │ (ring, one row down)  │  J — Navigate down      │
│ Alt   │ (thumb, bottom row)   │  K — Navigate up / Kill │
└───────┘                       │  L — Layer Toggle       │
                                │  A — Approve            │
                                │  Y — Yes / Confirm      │
                                │  N — No / Deny          │
                                │  ; — Annotation Mode    │
                                │  / — Cheat Sheet        │
                                │  P — Pipeline Switcher  │
                                └─────────────────────────┘
```

> **The result:** A user with an HHKB can operate the entire AgentBuffer
> dashboard — composing prompts, steering mid-stream, answering questions,
> switching pipelines, annotating output — without their fingers ever leaving
> the home row. This is the keyboard-first web paradigm.
