/** Finite state machine states for the agent streaming UI. */
export type UIState =
  | "IDLE"
  | "COMPOSING"
  | "AGENT_STREAMING"
  | "AGENT_PAUSED"
  | "AWAITING_USER_DECISION"
  | "REVIEWING";

/** Events that trigger FSM transitions. */
export type UIEvent =
  | { type: "FOCUS_PROMPT" }
  | { type: "SUBMIT_PROMPT"; text: string }
  | { type: "CANCEL_COMPOSITION" }
  | { type: "AGENT_STARTED" }
  | { type: "AGENT_COMPLETED" }
  | { type: "HALT_AND_PIVOT" }
  | { type: "APPROVE" }
  | { type: "KILL_ARM" }
  | { type: "KILL_CONFIRM" }
  | { type: "KILL_DISARM" }
  | { type: "AGENT_ASK_QUESTION"; question: AgentQuestion }
  | { type: "SUBMIT_STEERING"; text: string }
  | { type: "DISMISS_OVERLAY" }
  | { type: "ANSWER_QUESTION"; answer: string }
  | { type: "DISMISS_DECISION_DOCK" }
  | { type: "START_NEW_RUN" }
  | { type: "TOGGLE_COMMAND_PALETTE" }
  | { type: "TOGGLE_PIPELINE_SWITCHER" }
  | { type: "TOGGLE_KEYBIND_CHEAT_SHEET" }
  | { type: "TOGGLE_AGENT_LAYER" }
  | { type: "TOGGLE_ANNOTATION_MODE" }
  | { type: "SELECT_PIPELINE"; pipeline: PipelineId }
  | { type: "NAVIGATE_SELECTION"; direction: "up" | "down" };

/** Pipeline identifiers. */
export type PipelineId = "video" | "carousel" | "design";

/** Agent question types for the Decision Dock. */
export interface AgentQuestion {
  id: string;
  text: string;
  questionType: "yes_no" | "list" | "free_form";
  options?: string[];
}

/** A registered keybind definition. */
export interface KeybindDef {
  chord: string;
  action: string;
  description: string;
  activeInStates: UIState[];
  handler: (dispatch: (event: UIEvent) => void, context: UIContext) => void;
}

/** Extended FSM context exposed to keybind handlers and UI components. */
export interface UIContext {
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
