import type { KeybindDef, UIState } from "./types";

/**
 * Normalize a KeyboardEvent into a chord string like "Ctrl+Shift+H".
 * Modifier order is always: Ctrl, Shift, Alt, Meta — then the key.
 */
export function toChord(e: KeyboardEvent): string {
  const parts: string[] = [];
  if (e.ctrlKey || e.metaKey) parts.push("Ctrl");
  if (e.shiftKey) parts.push("Shift");
  if (e.altKey) parts.push("Alt");

  // Normalize the key — ignore modifier-only keys
  const key = e.key;
  if (["Control", "Shift", "Alt", "Meta"].includes(key)) return "";

  // Capitalize single letters
  const normalized =
    key.length === 1 ? key.toUpperCase() : key;
  parts.push(normalized);
  return parts.join("+");
}

/** All registered keybind definitions. */
export const KEYBIND_REGISTRY: KeybindDef[] = [
  // --- AGENT_STREAMING chords ---
  {
    chord: "Ctrl+Shift+H",
    action: "halt_and_pivot",
    description: "Halt & Pivot — pause generation, open steering input",
    activeInStates: ["AGENT_STREAMING"],
    handler: (dispatch) => dispatch({ type: "HALT_AND_PIVOT" }),
  },
  {
    chord: "Ctrl+Shift+A",
    action: "approve",
    description: "Approve — force-finalize current agent thought",
    activeInStates: ["AGENT_STREAMING"],
    handler: (dispatch) => dispatch({ type: "APPROVE" }),
  },
  {
    chord: "Ctrl+Shift+K",
    action: "kill_process",
    description: "Kill Process — terminate agent run (double-tap to confirm)",
    activeInStates: ["AGENT_STREAMING"],
    handler: (dispatch, ctx) => {
      if (ctx.killArmed) {
        dispatch({ type: "KILL_CONFIRM" });
      } else {
        dispatch({ type: "KILL_ARM" });
      }
    },
  },

  // --- AWAITING_USER_DECISION chords ---
  {
    chord: "Ctrl+Shift+Y",
    action: "confirm_yes",
    description: "Confirm / Yes",
    activeInStates: ["AWAITING_USER_DECISION"],
    handler: (dispatch) => dispatch({ type: "ANSWER_QUESTION", answer: "yes" }),
  },
  {
    chord: "Ctrl+Shift+N",
    action: "deny_no",
    description: "Deny / No",
    activeInStates: ["AWAITING_USER_DECISION"],
    handler: (dispatch) => dispatch({ type: "ANSWER_QUESTION", answer: "no" }),
  },
  {
    chord: "Ctrl+J",
    action: "navigate_down",
    description: "Navigate selection down",
    activeInStates: ["AWAITING_USER_DECISION"],
    handler: (dispatch) =>
      dispatch({ type: "NAVIGATE_SELECTION", direction: "down" }),
  },
  {
    chord: "Ctrl+K",
    action: "navigate_up_or_palette",
    description: "Navigate selection up / Command Palette",
    activeInStates: ["AWAITING_USER_DECISION", "IDLE", "REVIEWING"],
    handler: (dispatch, ctx) => {
      if (ctx.state === "AWAITING_USER_DECISION") {
        dispatch({ type: "NAVIGATE_SELECTION", direction: "up" });
      } else {
        dispatch({ type: "TOGGLE_COMMAND_PALETTE" });
      }
    },
  },
  {
    chord: "Ctrl+Shift+Enter",
    action: "submit_selection",
    description: "Submit selected option",
    activeInStates: ["AWAITING_USER_DECISION"],
    handler: (dispatch, ctx) => {
      if (ctx.question?.options) {
        const answer = ctx.question.options[ctx.selectedOptionIndex] ?? "";
        dispatch({ type: "ANSWER_QUESTION", answer });
      }
    },
  },

  // --- Global chords ---
  {
    chord: "Ctrl+Shift+P",
    action: "pipeline_switcher",
    description: "Pipeline Switcher",
    activeInStates: ["IDLE", "REVIEWING", "AGENT_STREAMING"],
    handler: (dispatch) => dispatch({ type: "TOGGLE_PIPELINE_SWITCHER" }),
  },
  {
    chord: "Ctrl+Shift+/",
    action: "cheat_sheet",
    description: "Keybind Cheat Sheet",
    activeInStates: [
      "IDLE",
      "COMPOSING",
      "AGENT_STREAMING",
      "AGENT_PAUSED",
      "AWAITING_USER_DECISION",
      "REVIEWING",
    ],
    handler: (dispatch) => dispatch({ type: "TOGGLE_KEYBIND_CHEAT_SHEET" }),
  },

  // --- COMPOSING chords ---
  {
    chord: "Ctrl+Shift+Escape",
    action: "cancel_or_dismiss",
    description: "Cancel composition / Dismiss overlay",
    activeInStates: ["COMPOSING", "AGENT_PAUSED", "AWAITING_USER_DECISION"],
    handler: (dispatch, ctx) => {
      if (ctx.state === "COMPOSING") {
        dispatch({ type: "CANCEL_COMPOSITION" });
      } else if (ctx.state === "AGENT_PAUSED") {
        dispatch({ type: "DISMISS_OVERLAY" });
      } else if (ctx.state === "AWAITING_USER_DECISION") {
        dispatch({ type: "DISMISS_DECISION_DOCK" });
      }
    },
  },

  // --- REVIEWING chords ---
  {
    chord: "Ctrl+Shift+L",
    action: "agent_layer_toggle",
    description: "Agent Layer Toggle — X-ray split view",
    activeInStates: ["AGENT_STREAMING", "REVIEWING"],
    handler: (dispatch) => dispatch({ type: "TOGGLE_AGENT_LAYER" }),
  },
  {
    chord: "Ctrl+Shift+;",
    action: "annotation_mode",
    description: "Inline Annotation Mode",
    activeInStates: ["REVIEWING"],
    handler: (dispatch) => dispatch({ type: "TOGGLE_ANNOTATION_MODE" }),
  },
];

/** Look up a keybind by chord string. */
export function findKeybind(chord: string): KeybindDef | undefined {
  return KEYBIND_REGISTRY.find((kb) => kb.chord === chord);
}

/** Check if a keybind is active in the given state. */
export function isActiveInState(def: KeybindDef, state: UIState): boolean {
  return def.activeInStates.includes(state);
}

/** Get all keybinds active in a given state. */
export function getKeybindsForState(state: UIState): KeybindDef[] {
  return KEYBIND_REGISTRY.filter((kb) => kb.activeInStates.includes(state));
}

/** Get keybinds grouped by state for the cheat sheet. */
export function getKeybindsByState(): Record<UIState, KeybindDef[]> {
  const states: UIState[] = [
    "IDLE",
    "COMPOSING",
    "AGENT_STREAMING",
    "AGENT_PAUSED",
    "AWAITING_USER_DECISION",
    "REVIEWING",
  ];
  const result: Record<string, KeybindDef[]> = {};
  for (const s of states) {
    result[s] = getKeybindsForState(s);
  }
  return result as Record<UIState, KeybindDef[]>;
}
