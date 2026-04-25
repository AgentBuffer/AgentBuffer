"use client";

import { useKeybinds } from "@/lib/keybinds/use-keybinds";
import { cn } from "@/lib/utils";
import type { UIState } from "@/lib/keybinds/types";

const STATE_COLORS: Record<UIState, string> = {
  IDLE: "bg-slate-100 text-slate-500",
  COMPOSING: "bg-blue-100 text-blue-700",
  AGENT_STREAMING: "bg-emerald-100 text-emerald-700",
  AGENT_PAUSED: "bg-amber-100 text-amber-700",
  AWAITING_USER_DECISION: "bg-purple-100 text-purple-700",
  REVIEWING: "bg-cyan-100 text-cyan-700",
};

/** Small inline badge showing the current FSM state. */
export function StateBadge() {
  const { ctx } = useKeybinds();

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase tracking-wide",
        STATE_COLORS[ctx.state]
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current opacity-60" />
      {ctx.state.replace(/_/g, " ")}
    </span>
  );
}
