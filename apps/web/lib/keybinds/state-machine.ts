import type { UIState, UIEvent, UIContext, AgentQuestion, PipelineId } from "./types";

/** Full FSM + UI context state. */
export interface FSMState {
  state: UIState;
  killArmed: boolean;
  promptText: string;
  steeringText: string;
  question: AgentQuestion | null;
  selectedOptionIndex: number;
  commandPaletteOpen: boolean;
  pipelineSwitcherOpen: boolean;
  cheatSheetOpen: boolean;
  agentLayerOpen: boolean;
  annotationModeActive: boolean;
  activePipeline: PipelineId;
}

export const INITIAL_STATE: FSMState = {
  state: "IDLE",
  killArmed: false,
  promptText: "",
  steeringText: "",
  question: null,
  selectedOptionIndex: 0,
  commandPaletteOpen: false,
  pipelineSwitcherOpen: false,
  cheatSheetOpen: false,
  agentLayerOpen: false,
  annotationModeActive: false,
  activePipeline: "video",
};

/** Reducer implementing the FSM transition table with guard conditions. */
export function fsmReducer(prev: FSMState, event: UIEvent): FSMState {
  switch (event.type) {
    // --- IDLE transitions ---
    case "FOCUS_PROMPT":
      if (prev.state === "IDLE" || prev.state === "REVIEWING") {
        return {
          ...prev,
          state: "COMPOSING",
          commandPaletteOpen: false,
          annotationModeActive: false,
        };
      }
      return prev;

    // --- COMPOSING transitions ---
    case "SUBMIT_PROMPT":
      if (prev.state === "COMPOSING" && event.text.trim().length > 0) {
        return {
          ...prev,
          state: "AGENT_STREAMING",
          promptText: event.text,
        };
      }
      return prev;

    case "CANCEL_COMPOSITION":
      if (prev.state === "COMPOSING") {
        return { ...prev, state: "IDLE" };
      }
      return prev;

    // --- AGENT_STREAMING transitions ---
    case "AGENT_STARTED":
      return { ...prev, state: "AGENT_STREAMING" };

    case "AGENT_COMPLETED":
      if (prev.state === "AGENT_STREAMING") {
        return {
          ...prev,
          state: "REVIEWING",
          killArmed: false,
          agentLayerOpen: false,
        };
      }
      return prev;

    case "HALT_AND_PIVOT":
      if (prev.state === "AGENT_STREAMING") {
        return {
          ...prev,
          state: "AGENT_PAUSED",
          steeringText: "",
          killArmed: false,
        };
      }
      return prev;

    case "APPROVE":
      if (prev.state === "AGENT_STREAMING") {
        // Force-finalize current thought, stay in streaming for next step
        return prev;
      }
      return prev;

    case "KILL_ARM":
      if (prev.state === "AGENT_STREAMING" && !prev.killArmed) {
        return { ...prev, killArmed: true };
      }
      return prev;

    case "KILL_CONFIRM":
      if (prev.state === "AGENT_STREAMING" && prev.killArmed) {
        return {
          ...INITIAL_STATE,
          activePipeline: prev.activePipeline,
        };
      }
      return prev;

    case "KILL_DISARM":
      return { ...prev, killArmed: false };

    case "AGENT_ASK_QUESTION":
      if (prev.state === "AGENT_STREAMING") {
        return {
          ...prev,
          state: "AWAITING_USER_DECISION",
          question: event.question,
          selectedOptionIndex: 0,
          killArmed: false,
        };
      }
      return prev;

    // --- AGENT_PAUSED transitions ---
    case "SUBMIT_STEERING":
      if (prev.state === "AGENT_PAUSED" && event.text.trim().length > 0) {
        return {
          ...prev,
          state: "AGENT_STREAMING",
          steeringText: event.text,
        };
      }
      return prev;

    case "DISMISS_OVERLAY":
      if (prev.state === "AGENT_PAUSED") {
        return { ...prev, state: "AGENT_STREAMING" };
      }
      return prev;

    // --- AWAITING_USER_DECISION transitions ---
    case "ANSWER_QUESTION":
      if (prev.state === "AWAITING_USER_DECISION") {
        return {
          ...prev,
          state: "AGENT_STREAMING",
          question: null,
          selectedOptionIndex: 0,
        };
      }
      return prev;

    case "DISMISS_DECISION_DOCK":
      if (prev.state === "AWAITING_USER_DECISION") {
        return {
          ...prev,
          state: "AGENT_PAUSED",
          question: null,
          selectedOptionIndex: 0,
        };
      }
      return prev;

    case "NAVIGATE_SELECTION":
      if (prev.state === "AWAITING_USER_DECISION" && prev.question?.options) {
        const len = prev.question.options.length;
        if (len === 0) return prev;
        const next =
          event.direction === "down"
            ? (prev.selectedOptionIndex + 1) % len
            : (prev.selectedOptionIndex - 1 + len) % len;
        return { ...prev, selectedOptionIndex: next };
      }
      return prev;

    // --- REVIEWING transitions ---
    case "START_NEW_RUN":
      if (prev.state === "REVIEWING" || prev.state === "IDLE") {
        return { ...prev, state: "AGENT_STREAMING" };
      }
      return prev;

    // --- Overlay toggles ---
    case "TOGGLE_COMMAND_PALETTE":
      if (prev.state === "IDLE" || prev.state === "REVIEWING") {
        return {
          ...prev,
          commandPaletteOpen: !prev.commandPaletteOpen,
          pipelineSwitcherOpen: false,
          cheatSheetOpen: false,
        };
      }
      return prev;

    case "TOGGLE_PIPELINE_SWITCHER": {
      const allowed: UIState[] = ["IDLE", "REVIEWING", "AGENT_STREAMING"];
      if (allowed.includes(prev.state)) {
        return {
          ...prev,
          pipelineSwitcherOpen: !prev.pipelineSwitcherOpen,
          commandPaletteOpen: false,
          cheatSheetOpen: false,
        };
      }
      return prev;
    }

    case "TOGGLE_KEYBIND_CHEAT_SHEET":
      return {
        ...prev,
        cheatSheetOpen: !prev.cheatSheetOpen,
        commandPaletteOpen: false,
        pipelineSwitcherOpen: false,
      };

    case "TOGGLE_AGENT_LAYER":
      if (prev.state === "AGENT_STREAMING" || prev.state === "REVIEWING") {
        return { ...prev, agentLayerOpen: !prev.agentLayerOpen };
      }
      return prev;

    case "TOGGLE_ANNOTATION_MODE":
      if (prev.state === "REVIEWING") {
        return { ...prev, annotationModeActive: !prev.annotationModeActive };
      }
      return prev;

    case "SELECT_PIPELINE":
      if (prev.state === "IDLE" || prev.state === "REVIEWING") {
        return {
          ...prev,
          activePipeline: event.pipeline,
          pipelineSwitcherOpen: false,
        };
      }
      return prev;

    default:
      return prev;
  }
}

/** Convert FSMState to UIContext for keybind handlers and UI. */
export function toUIContext(s: FSMState): UIContext {
  return {
    state: s.state,
    killArmed: s.killArmed,
    promptText: s.promptText,
    steeringText: s.steeringText,
    question: s.question,
    selectedOptionIndex: s.selectedOptionIndex,
    commandPaletteOpen: s.commandPaletteOpen,
    pipelineSwitcherOpen: s.pipelineSwitcherOpen,
    cheatSheetOpen: s.cheatSheetOpen,
    agentLayerOpen: s.agentLayerOpen,
    annotationModeActive: s.annotationModeActive,
    activePipeline: s.activePipeline,
  };
}
