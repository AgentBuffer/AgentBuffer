"use client";

import { useKeybinds } from "@/lib/keybinds/use-keybinds";
import type { PipelineId } from "@/lib/keybinds/types";
import { cn } from "@/lib/utils";
import { useEffect, useRef } from "react";
import { Video, Image, Palette } from "lucide-react";
import type { ComponentType } from "react";
import type { LucideProps } from "lucide-react";

interface PipelineTab {
  id: PipelineId;
  label: string;
  icon: ComponentType<LucideProps>;
  status: "active" | "idle" | "error";
  lastRun: string;
  shortcut: string;
}

const PIPELINE_TABS: PipelineTab[] = [
  {
    id: "video",
    label: "Video",
    icon: Video,
    status: "active",
    lastRun: "2m ago",
    shortcut: "Ctrl+1",
  },
  {
    id: "carousel",
    label: "Carousel",
    icon: Image,
    status: "idle",
    lastRun: "1h ago",
    shortcut: "Ctrl+2",
  },
  {
    id: "design",
    label: "Design",
    icon: Palette,
    status: "idle",
    lastRun: "5m ago",
    shortcut: "Ctrl+3",
  },
];

const STATUS_STYLES: Record<string, { dot: string; label: string }> = {
  active: { dot: "bg-emerald-500", label: "active" },
  idle: { dot: "bg-slate-300", label: "idle" },
  error: { dot: "bg-red-500", label: "error" },
};

export function PipelineSwitcher() {
  const { ctx, dispatch } = useKeybinds();
  const panelRef = useRef<HTMLDivElement>(null);
  const isReadOnly = ctx.state === "AGENT_STREAMING";

  useEffect(() => {
    if (ctx.pipelineSwitcherOpen) {
      panelRef.current?.focus();
    }
  }, [ctx.pipelineSwitcherOpen]);

  useEffect(() => {
    if (!ctx.pipelineSwitcherOpen) return;

    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault();
        e.stopPropagation();
        dispatch({ type: "TOGGLE_PIPELINE_SWITCHER" });
        return;
      }

      if (e.ctrlKey && !e.shiftKey && !e.altKey) {
        const idx = parseInt(e.key, 10) - 1;
        if (idx >= 0 && idx < PIPELINE_TABS.length && !isReadOnly) {
          e.preventDefault();
          e.stopPropagation();
          dispatch({
            type: "SELECT_PIPELINE",
            pipeline: PIPELINE_TABS[idx].id,
          });
        }
      }
    }

    window.addEventListener("keydown", handleKey, true);
    return () => window.removeEventListener("keydown", handleKey, true);
  }, [ctx.pipelineSwitcherOpen, dispatch, isReadOnly]);

  if (!ctx.pipelineSwitcherOpen) return null;

  return (
    <div className="fixed inset-x-0 top-0 z-50 flex justify-center pt-2 pointer-events-none">
      <div
        ref={panelRef}
        tabIndex={-1}
        role="tablist"
        aria-label="Pipeline Switcher"
        className="pointer-events-auto bg-white rounded-xl shadow-2xl border border-slate-200 px-2 py-3 flex items-center gap-2 outline-none"
      >
        {PIPELINE_TABS.map((tab) => {
          const isCurrent = ctx.activePipeline === tab.id;
          const statusStyle = STATUS_STYLES[tab.status];
          return (
            <button
              key={tab.id}
              role="tab"
              aria-selected={isCurrent}
              disabled={isReadOnly}
              onClick={() => {
                if (!isReadOnly) {
                  dispatch({ type: "SELECT_PIPELINE", pipeline: tab.id });
                }
              }}
              className={cn(
                "flex flex-col items-center gap-1.5 px-6 py-2 rounded-lg transition-colors min-w-[120px]",
                isCurrent
                  ? "bg-cyan-50 border border-cyan-200"
                  : "hover:bg-slate-50",
                isReadOnly && "opacity-60 cursor-not-allowed"
              )}
            >
              <tab.icon
                className={cn(
                  "h-5 w-5",
                  isCurrent ? "text-cyan-600" : "text-slate-400"
                )}
              />
              <span
                className={cn(
                  "text-xs font-semibold font-mono uppercase tracking-wide",
                  isCurrent ? "text-cyan-700" : "text-slate-600"
                )}
              >
                {tab.label}
              </span>
              <div className="flex items-center gap-1.5">
                <span
                  className={cn(
                    "h-1.5 w-1.5 rounded-full",
                    statusStyle.dot
                  )}
                />
                <span className="text-[10px] text-slate-400 font-mono">
                  {statusStyle.label}
                </span>
              </div>
              <span className="text-[10px] text-slate-300 font-mono">
                {tab.lastRun}
              </span>
              <kbd className="text-[10px] font-mono bg-slate-100 px-1.5 py-0.5 rounded text-slate-400">
                {tab.shortcut}
              </kbd>
            </button>
          );
        })}

        {isReadOnly && (
          <p className="text-[10px] text-amber-600 font-mono px-2 max-w-[140px] text-center">
            Peek only — switch after run completes
          </p>
        )}
      </div>
    </div>
  );
}
