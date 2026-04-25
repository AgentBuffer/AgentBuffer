# Hard-to-Activate Web Keybind Matrix — HHKB 60% Layout

> Complete keybind specification for the AgentBuffer keyboard-centric agent
> streaming interface, designed around the Happy Hacking Keyboard 60% layout.

---

## 1. Overview

AgentBuffer's web dashboard is operated primarily via keyboard chords. This
document defines every operational keybind, maps each chord to the UI states
where it is active, documents visual feedback, and audits every chord against
browser and OS reserved shortcuts.

All chords are designed for the HHKB Professional 60% keyboard layout, where
Control occupies the Caps Lock position on the home row and arrow keys live
behind an Fn layer.

---

## 2. HHKB Layout Context

The Happy Hacking Keyboard (HHKB) is a 60% layout with several ergonomic
characteristics that directly influence keybind design:

```
┌─────────────────────────────────────────────────────────────┐
│ Esc  1  2  3  4  5  6  7  8  9  0  -  =  \  `             │
│  Tab   Q  W  E  R  T  Y  U  I  O  P  [  ]  Backspace      │
│  Ctrl   A  S  D  F  G  H  J  K  L  ;  '  Enter            │
│   Shift   Z  X  C  V  B  N  M  ,  .  /  Shift   Fn        │
│        Alt  Meta          Space         Meta  Alt          │
└─────────────────────────────────────────────────────────────┘
```

Key characteristics:

- **Control is at Caps Lock position** — Left pinky rests naturally on Control.
  `Ctrl+<key>` chords are the most ergonomic modifier combination, especially
  with home-row keys (A, S, D, F, H, J, K, L).
- **No dedicated function row** — F1–F12 require `Fn+number`. Function keys are
  avoided for operational binds.
- **No dedicated arrow keys** — Arrows require `Fn+[;'/` (or similar). Vim-style
  `J`/`K` navigation is strongly preferred over arrow keys.
- **Compact right side** — No numpad, no Insert/Delete cluster. Keybinds avoid
  keys that don't exist on the HHKB without an Fn layer.

---

## 3. Design Principles

### 3.1 Multi-Modifier Requirement

All operational keybinds use **two or more modifier keys** (e.g., `Ctrl+Shift`)
to prevent accidental activation. Single-key presses and single-modifier chords
(`Ctrl+<key>` alone) are never operational keybinds — they must pass through to
text inputs and browser defaults.

> **Exception:** `Ctrl+J` / `Ctrl+K` for list navigation in
> `AWAITING_USER_DECISION` state are single-modifier, but they are only active
> when no text input is focused, making accidental activation impossible.

### 3.2 Browser-Reserved Shortcuts — Avoid List

The following shortcuts are **never** used as operational keybinds because they
are reserved by browsers or operating systems:

| Shortcut              | Browser / OS Function                     |
|-----------------------|-------------------------------------------|
| `Ctrl+W`              | Close tab                                 |
| `Ctrl+T`              | New tab                                   |
| `Ctrl+R`              | Reload page                               |
| `Ctrl+L`              | Focus address bar                         |
| `Ctrl+N`              | New window                                |
| `Ctrl+Q`              | Quit browser (macOS / Linux)              |
| `Ctrl+Tab`            | Next tab                                  |
| `Ctrl+Shift+T`        | Reopen closed tab                         |
| `Ctrl+Shift+I`        | DevTools                                  |
| `Ctrl+Shift+J`        | DevTools Console                          |
| `Ctrl+F`              | Find on page                              |
| `Ctrl+G`              | Find next                                 |
| `Ctrl+H`              | History (Chrome) / Replace (editors)      |
| `Ctrl+P`              | Print                                     |
| `Ctrl+S`              | Save page                                 |
| `Ctrl+D`              | Bookmark                                  |
| `Ctrl+U`              | View source                               |
| `Ctrl+Shift+Delete`   | Clear browsing data                       |
| `Ctrl+Shift+B`        | Toggle bookmarks bar                      |
| `Ctrl+Shift+M`        | Toggle user profiles (Chrome)             |

### 3.3 Home-Row Preference

Operational keys are chosen from the home row or immediately adjacent rows
(H, J, K, L, A, S, Y, N) to minimize finger travel on the HHKB. Keys requiring
a stretch to the number row or bottom row are reserved for less frequent
actions.

### 3.4 Single-Key Pass-Through Rule

Single-key presses are **never** intercepted by the global keydown handler. They
always pass through to the browser and any focused text input. This ensures that
typing in textareas, search bars, and the browser address bar works normally
regardless of the FSM state.

---

## 4. Keybind Matrix

### 4.1 AGENT_STREAMING State Chords

| Chord            | Action           | Active In State(s) | Visual Feedback                                                                                              | Conflict Check Notes                                    |
|------------------|------------------|---------------------|--------------------------------------------------------------------------------------------------------------|---------------------------------------------------------|
| `Ctrl+Shift+H`  | Halt & Pivot     | `AGENT_STREAMING`   | Streaming output freezes. Pulsing amber border appears around output area. Inline steering input slides in below the last streamed token. | Not a standard browser shortcut. Safe on all platforms. |
| `Ctrl+Shift+A`  | Approve / Accept | `AGENT_STREAMING`   | Green checkmark flash on the current thought block. A "confirmed" badge appears on the output section.       | Not a standard browser shortcut. Safe on all platforms. |
| `Ctrl+Shift+K`  | Kill Process     | `AGENT_STREAMING`   | **First press:** Red pulsing border on streaming area + "Press again to confirm" toast. **Second press (within 2 s):** Red pulse, then "terminated" badge. | Firefox: `Ctrl+Shift+K` opens Web Console. Mitigated by `preventDefault()` in `AGENT_STREAMING` state. See Section 6. |

### 4.2 AWAITING_USER_DECISION State Chords

| Chord               | Action                | Active In State(s)        | Visual Feedback                                                                                   | Conflict Check Notes                                                |
|----------------------|-----------------------|---------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------|
| `Ctrl+Shift+Y`      | Confirm / Yes         | `AWAITING_USER_DECISION`  | Selected "Yes" card pulses green, Decision Dock slides out.                                       | Not a standard browser shortcut. Safe on all platforms.             |
| `Ctrl+Shift+N`      | Deny / No             | `AWAITING_USER_DECISION`  | Selected "No" card pulses red, Decision Dock slides out.                                          | Not a standard browser shortcut. `Ctrl+N` (new window) uses single modifier — no conflict. |
| `Ctrl+J`             | Navigate selection ↓  | `AWAITING_USER_DECISION`  | Highlight moves down the option list. Active card gets a focus ring.                              | Chrome: `Ctrl+J` opens Downloads. Mitigated: `preventDefault()` only when Decision Dock is focused. |
| `Ctrl+K`             | Navigate selection ↑  | `AWAITING_USER_DECISION`  | Highlight moves up the option list. Active card gets a focus ring.                                | Chrome: `Ctrl+K` focuses address bar. Mitigated: `preventDefault()` only in `AWAITING_USER_DECISION`. |
| `Ctrl+Shift+Enter`  | Submit selected option | `AWAITING_USER_DECISION`  | Selected card confirms with a green flash, Decision Dock slides out.                              | Not a standard browser shortcut. Safe on all platforms.             |

### 4.3 Global Chords

| Chord            | Action              | Active In State(s)            | Visual Feedback                                                                                         | Conflict Check Notes                                                |
|------------------|----------------------|-------------------------------|---------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------|
| `Ctrl+K`         | Command Palette      | `IDLE`, `REVIEWING`           | Centered overlay with text input and filtered results list. Background dims.                            | Chrome: `Ctrl+K` focuses address bar. Mitigated: only intercepted in `IDLE` / `REVIEWING`, not during streaming or typing. |
| `Ctrl+Shift+P`   | Pipeline Switcher    | `IDLE`, `REVIEWING`, `AGENT_STREAMING` (read-only) | Horizontal tab bar slides down from top. Shows pipeline name + status badge + last run timestamp. | Firefox: `Ctrl+Shift+P` opens Private Window. Mitigated by `preventDefault()` in active states. Chrome/Safari: not reserved. |
| `Ctrl+Shift+/`   | Keybind Cheat Sheet  | All states                    | Overlay listing all keybinds grouped by state. Dismissable with `Escape`.                               | Not a standard browser shortcut. Safe on all platforms.             |

### 4.4 COMPOSING State Chords

| Chord               | Action              | Active In State(s) | Visual Feedback                                                                         | Conflict Check Notes                                    |
|----------------------|----------------------|---------------------|-----------------------------------------------------------------------------------------|---------------------------------------------------------|
| `Ctrl+Enter`         | Submit prompt        | `COMPOSING`         | Prompt textarea pulses blue, text is sent, textarea is disabled, transition to streaming. | Standard submit pattern. No conflicts.                  |
| `Ctrl+Shift+Escape`  | Cancel composition   | `COMPOSING`         | Textarea border flashes gray, focus released, return to IDLE.                            | Not a standard browser shortcut. Safe on all platforms. |

### 4.5 AGENT_PAUSED State Chords

| Chord               | Action                  | Active In State(s) | Visual Feedback                                                                           | Conflict Check Notes                                    |
|----------------------|--------------------------|---------------------|-------------------------------------------------------------------------------------------|---------------------------------------------------------|
| `Ctrl+Enter`         | Submit steering input    | `AGENT_PAUSED`      | Overlay input pulses blue, steering text is sent to agent, overlay slides out.             | Standard submit pattern. No conflicts.                  |
| `Ctrl+Shift+Escape`  | Dismiss steering overlay | `AGENT_PAUSED`      | Overlay slides out, amber border clears, agent resumes without steering.                   | Not a standard browser shortcut. Safe on all platforms. |

### 4.6 REVIEWING State Chords

| Chord            | Action                 | Active In State(s) | Visual Feedback                                                                             | Conflict Check Notes                                    |
|------------------|-------------------------|---------------------|---------------------------------------------------------------------------------------------|----------------------------------------------------------|
| `Ctrl+Shift+L`   | Agent Layer Toggle      | `REVIEWING`, `AGENT_STREAMING` | Main content splits vertically: formatted output (left) + raw agent log (right).   | Not a standard browser shortcut. Safe on all platforms.  |
| `Ctrl+Shift+;`   | Inline Annotation Mode  | `REVIEWING`         | Output text becomes selectable. Selected span gets a highlight and anchored input appears.  | Not a standard browser shortcut. Safe on all platforms.  |

---

## 5. Double-Tap Safety Pattern

The Kill Process action (`Ctrl+Shift+K`) uses a double-tap confirmation pattern
to prevent accidental termination of an active agent run.

### Flow

```
                    Ctrl+Shift+K
                         │
                         ▼
               ┌───────────────────┐
               │  Is killArmed?    │
               └───────┬───────────┘
                  no    │    yes
            ┌───────────┴──────────┐
            ▼                      ▼
  ┌──────────────────┐   ┌──────────────────┐
  │  ARM the kill    │   │  EXECUTE kill     │
  │  killArmed=true  │   │  Terminate agent  │
  │  Start 2s timer  │   │  → IDLE state     │
  │  Show toast +    │   │  Clear armed flag │
  │  red pulsing     │   │  Remove toast     │
  └──────────────────┘   └──────────────────┘
            │
            │  (2 seconds elapse without second press)
            ▼
  ┌──────────────────┐
  │  DISARM silently │
  │  killArmed=false │
  │  Remove toast +  │
  │  red pulsing     │
  └──────────────────┘
```

### Visual States

| Phase           | Border            | Toast Message                  | Duration |
|-----------------|-------------------|--------------------------------|----------|
| Armed           | Red pulsing       | "Press Ctrl+Shift+K again to confirm kill" | Up to 2 s |
| Confirmed       | Solid red flash   | "Agent run terminated"         | 1.5 s    |
| Disarmed        | Return to normal  | (toast removed)                | Instant  |

### Rationale

A modal confirmation dialog would break the keyboard-first flow and require
mouse interaction. The double-tap pattern keeps the user's hands on the keyboard
and provides a fast, deliberate confirmation mechanism without the risk of a
single accidental keypress terminating an in-progress run.

---

## 6. Conflict Audit

This section audits every operational chord against Chrome, Firefox, Safari, and
common OS-level shortcuts.

| Chord               | Chrome         | Firefox           | Safari         | macOS (Cmd equiv.) | Mitigation                                                                  |
|----------------------|----------------|-------------------|----------------|---------------------|-----------------------------------------------------------------------------|
| `Ctrl+Shift+H`      | No conflict    | No conflict       | No conflict    | No conflict         | Safe on all platforms.                                                      |
| `Ctrl+Shift+A`      | No conflict    | No conflict       | No conflict    | No conflict         | Safe on all platforms.                                                      |
| `Ctrl+Shift+K`      | No conflict    | **Web Console**   | No conflict    | No conflict         | `preventDefault()` called only in `AGENT_STREAMING` state. In all other states the event passes through, preserving Firefox's default behavior. |
| `Ctrl+Shift+Y`      | No conflict    | No conflict       | No conflict    | No conflict         | Safe on all platforms.                                                      |
| `Ctrl+Shift+N`      | Incognito      | Private Window    | Private Window | New Incognito       | **Not a conflict.** `Ctrl+Shift+N` is only intercepted in `AWAITING_USER_DECISION` state where the Decision Dock has focus. Browser extensions typically do not override this. Note: this chord *does* prevent opening a private window while the Decision Dock is active, which is acceptable. |
| `Ctrl+J`             | Downloads      | Downloads         | No conflict    | No conflict         | Only intercepted in `AWAITING_USER_DECISION`. In all other states, browser default is preserved. |
| `Ctrl+K`             | Address bar    | Address bar       | No conflict    | Spotlight-like       | Intercepted in `IDLE`, `REVIEWING`, and `AWAITING_USER_DECISION`. In `COMPOSING` and `AGENT_STREAMING`, passes through. Users who need the address bar can click it or use `Ctrl+L`. |
| `Ctrl+Shift+P`      | No conflict    | **Private Window** | No conflict   | No conflict         | `preventDefault()` in active states. Firefox users lose the Private Window shortcut while the app is focused in those states. Acceptable trade-off for pipeline switching. |
| `Ctrl+Shift+/`      | No conflict    | No conflict       | No conflict    | No conflict         | Safe on all platforms.                                                      |
| `Ctrl+Enter`         | No conflict    | No conflict       | No conflict    | No conflict         | Standard submit pattern. Universally safe.                                  |
| `Ctrl+Shift+Escape`  | Chrome Task Mgr | No conflict      | No conflict    | No conflict         | Chrome's Task Manager requires `Shift+Escape` (without `Ctrl`). `Ctrl+Shift+Escape` opens the OS task manager on Windows/Linux — but this is an OS-level shortcut that fires *before* the browser receives the event, so it cannot be intercepted by web apps and does not conflict. On macOS, `Cmd+Option+Escape` is Force Quit — different chord entirely. Safe. |
| `Ctrl+Shift+L`      | No conflict    | No conflict       | No conflict    | No conflict         | Safe on all platforms.                                                      |
| `Ctrl+Shift+;`      | No conflict    | No conflict       | No conflict    | No conflict         | Safe on all platforms.                                                      |
| `Ctrl+Shift+Enter`  | No conflict    | No conflict       | No conflict    | No conflict         | Safe on all platforms.                                                      |

### Platform-Specific Notes

- **Firefox users** — `Ctrl+Shift+K` (Web Console) and `Ctrl+Shift+P` (Private
  Window) are overridden only in specific FSM states. Users can still access
  these Firefox features when the app is in `IDLE` or `REVIEWING` states.
- **Chrome users** — `Ctrl+K` (address bar focus) is overridden in `IDLE` and
  `REVIEWING` for Command Palette. `Ctrl+L` remains available as an alternative
  for focusing the address bar.
- **macOS** — On macOS, `Ctrl` maps to the physical Control key, not Command.
  All chords in this document use the Control key. The `Cmd` equivalents (used
  by macOS for browser shortcuts) are unaffected.

---

## 7. Summary

```
State                    Active Chords
─────────────────────    ─────────────────────────────────────────
IDLE                     Ctrl+K, Ctrl+Shift+P, Ctrl+Shift+/
COMPOSING                Ctrl+Enter, Ctrl+Shift+Escape, Ctrl+Shift+/
AGENT_STREAMING          Ctrl+Shift+H, Ctrl+Shift+A, Ctrl+Shift+K,
                         Ctrl+Shift+P (read-only), Ctrl+Shift+L,
                         Ctrl+Shift+/
AGENT_PAUSED             Ctrl+Enter, Ctrl+Shift+Escape, Ctrl+Shift+/
AWAITING_USER_DECISION   Ctrl+Shift+Y, Ctrl+Shift+N, Ctrl+J, Ctrl+K,
                         Ctrl+Shift+Enter, Ctrl+Shift+/
REVIEWING                Ctrl+K, Ctrl+Shift+P, Ctrl+Shift+L,
                         Ctrl+Shift+;, Ctrl+Shift+/
```
