"use client";

import { useKeybinds } from "@/lib/keybinds/use-keybinds";
import { getKeybindsByState } from "@/lib/keybinds/registry";
import type { UIState } from "@/lib/keybinds/types";
import { cn } from "@/lib/utils";
import { useEffect, useRef } from "react";

const STATE_LABELS: Record<UIState, string> = {
  IDLE: "Idle",
  COMPOSING: "Composing",
  AGENT_STREAMING: "Agent Streaming",
  AGENT_PAUSED: "Agent Paused",
  AWAITING_USER_DECISION: "Awaiting Decision",
  REVIEWING: "Reviewing",
};

export function KeybindCheatSheet() {
  const { ctx, dispatch } = useKeybinds();
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ctx.cheatSheetOpen) {
      panelRef.current?.focus();
    }
  }, [ctx.cheatSheetOpen]);

  useEffect(() => {
    if (!ctx.cheatSheetOpen) return;

    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault();
        dispatch({ type: "TOGGLE_KEYBIND_CHEAT_SHEET" });
      }
    }

    window.addEventListener("keydown", handleKey, true);
    return () => window.removeEventListener("keydown", handleKey, true);
  }, [ctx.cheatSheetOpen, dispatch]);

  if (!ctx.cheatSheetOpen) return null;

  const grouped = getKeybindsByState();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div
        ref={panelRef}
        tabIndex={-1}
        role="dialog"
        aria-label="Keybind Cheat Sheet"
        className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-y-auto p-6 outline-none"
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-slate-900">
            Keybind Cheat Sheet
          </h2>
          <kbd className="text-xs font-mono bg-slate-100 px-2 py-0.5 rounded text-slate-500">
            Esc to close
          </kbd>
        </div>

        <p className="text-xs text-slate-500 mb-4 font-mono">
          Current state:{" "}
          <span className="font-semibold text-cyan-600">{ctx.state}</span>
        </p>

        {(Object.entries(grouped) as [UIState, typeof grouped[UIState]][]).map(
          ([state, bindings]) => {
            if (bindings.length === 0) return null;
            const isCurrent = state === ctx.state;
            return (
              <div key={state} className="mb-4">
                <h3
                  className={cn(
                    "text-xs font-mono font-semibold uppercase tracking-wide mb-2",
                    isCurrent ? "text-cyan-600" : "text-slate-400"
                  )}
                >
                  {STATE_LABELS[state]}
                  {isCurrent && " (active)"}
                </h3>
                <div className="space-y-1">
                  {bindings.map((kb) => (
                    <div
                      key={`${state}-${kb.chord}`}
                      className={cn(
                        "flex items-center justify-between px-3 py-1.5 rounded text-sm",
                        isCurrent
                          ? "bg-cyan-50 text-slate-900"
                          : "bg-slate-50 text-slate-500"
                      )}
                    >
                      <kbd className="font-mono text-xs bg-white border border-slate-200 px-2 py-0.5 rounded">
                        {kb.chord}
                      </kbd>
                      <span className="text-xs">{kb.description}</span>
                    </div>
                  ))}
                </div>
              </div>
            );
          }
        )}
      </div>
    </div>
  );
}
