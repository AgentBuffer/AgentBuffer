"use client";

import { useKeybinds } from "@/lib/keybinds/use-keybinds";
import { cn } from "@/lib/utils";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Sparkles,
  History,
  Video,
  Image,
  Palette,
  Settings,
  Keyboard,
} from "lucide-react";
import type { ComponentType } from "react";
import type { LucideProps } from "lucide-react";

interface PaletteAction {
  id: string;
  label: string;
  category: string;
  icon: ComponentType<LucideProps>;
  onSelect: () => void;
}

function CommandPaletteInner({
  onDismiss,
}: {
  onDismiss: () => void;
}) {
  const { dispatch } = useKeybinds();
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const actions: PaletteAction[] = useMemo(
    () => [
      {
        id: "new-run",
        label: "Start new agent run",
        category: "Agent",
        icon: Sparkles,
        onSelect: () => {
          onDismiss();
          dispatch({ type: "FOCUS_PROMPT" });
        },
      },
      {
        id: "past-runs",
        label: "View past runs",
        category: "Navigation",
        icon: History,
        onSelect: () => onDismiss(),
      },
      {
        id: "pipeline-video",
        label: "Switch pipeline → Video",
        category: "Pipeline",
        icon: Video,
        onSelect: () => {
          onDismiss();
          dispatch({ type: "SELECT_PIPELINE", pipeline: "video" });
        },
      },
      {
        id: "pipeline-carousel",
        label: "Switch pipeline → Carousel",
        category: "Pipeline",
        icon: Image,
        onSelect: () => {
          onDismiss();
          dispatch({ type: "SELECT_PIPELINE", pipeline: "carousel" });
        },
      },
      {
        id: "pipeline-design",
        label: "Switch pipeline → Design",
        category: "Pipeline",
        icon: Palette,
        onSelect: () => {
          onDismiss();
          dispatch({ type: "SELECT_PIPELINE", pipeline: "design" });
        },
      },
      {
        id: "settings",
        label: "Open settings",
        category: "Navigation",
        icon: Settings,
        onSelect: () => onDismiss(),
      },
      {
        id: "cheat-sheet",
        label: "Show keybind cheat sheet",
        category: "Help",
        icon: Keyboard,
        onSelect: () => {
          onDismiss();
          dispatch({ type: "TOGGLE_KEYBIND_CHEAT_SHEET" });
        },
      },
    ],
    [dispatch, onDismiss]
  );

  const filtered = useMemo(() => {
    if (!query.trim()) return actions;
    const q = query.toLowerCase();
    return actions.filter(
      (a) =>
        a.label.toLowerCase().includes(q) ||
        a.category.toLowerCase().includes(q)
    );
  }, [query, actions]);

  const clampedIndex = Math.min(selectedIndex, Math.max(filtered.length - 1, 0));

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault();
        e.stopPropagation();
        onDismiss();
        return;
      }

      if (e.ctrlKey && e.key === "j") {
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < filtered.length - 1 ? prev + 1 : 0
        );
        return;
      }
      if (e.ctrlKey && e.key === "k") {
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev > 0 ? prev - 1 : filtered.length - 1
        );
        return;
      }

      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        const action = filtered[clampedIndex];
        if (action) action.onSelect();
      }
    }

    window.addEventListener("keydown", handleKey, true);
    return () => window.removeEventListener("keydown", handleKey, true);
  }, [onDismiss, filtered, clampedIndex]);

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh] bg-black/30">
      <div
        role="listbox"
        aria-label="Command Palette"
        className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden"
      >
        <div className="px-4 py-3 border-b border-slate-100">
          <input
            ref={inputRef}
            type="text"
            placeholder="Search actions..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            className="w-full text-sm text-slate-900 placeholder:text-slate-400 outline-none bg-transparent"
            aria-label="Search actions"
          />
        </div>

        <div className="max-h-64 overflow-y-auto py-1">
          {filtered.length === 0 && (
            <div className="px-4 py-6 text-center text-sm text-slate-400">
              No matching actions
            </div>
          )}
          {filtered.map((action, i) => (
            <button
              key={action.id}
              role="option"
              aria-selected={i === clampedIndex}
              onClick={action.onSelect}
              className={cn(
                "flex items-center gap-3 w-full px-4 py-2 text-left text-sm transition-colors",
                i === clampedIndex
                  ? "bg-cyan-50 text-cyan-900"
                  : "text-slate-700 hover:bg-slate-50"
              )}
            >
              <action.icon className="h-4 w-4 shrink-0 opacity-60" />
              <span className="flex-1">{action.label}</span>
              <span className="text-[10px] text-slate-400 font-mono">
                {action.category}
              </span>
            </button>
          ))}
        </div>

        <div className="px-4 py-2 border-t border-slate-100 flex items-center gap-3 text-[10px] text-slate-400 font-mono">
          <span>Ctrl+J/K navigate</span>
          <span>Enter select</span>
          <span>Esc dismiss</span>
        </div>
      </div>
    </div>
  );
}

export function CommandPalette() {
  const { ctx, dispatch } = useKeybinds();

  const dismiss = useCallback(() => {
    dispatch({ type: "TOGGLE_COMMAND_PALETTE" });
  }, [dispatch]);

  if (!ctx.commandPaletteOpen) return null;

  return <CommandPaletteInner onDismiss={dismiss} />;
}
