"use client";

import { useKeybinds } from "@/lib/keybinds/use-keybinds";
import type { UIState } from "@/lib/keybinds/types";

const ANNOUNCEMENTS: Record<UIState, string> = {
  IDLE: "",
  COMPOSING: "Prompt input focused. Type your message.",
  AGENT_STREAMING: "Agent is generating output.",
  AGENT_PAUSED: "Agent paused. Steering input is ready.",
  AWAITING_USER_DECISION: "Agent is asking a question. Decision panel is open.",
  REVIEWING: "Agent run complete. Review output.",
};

export function StateAnnouncer() {
  const { ctx } = useKeybinds();
  const message = ANNOUNCEMENTS[ctx.state];

  return (
    <div
      role="status"
      aria-live="assertive"
      aria-atomic="true"
      className="sr-only"
    >
      {message}
    </div>
  );
}
