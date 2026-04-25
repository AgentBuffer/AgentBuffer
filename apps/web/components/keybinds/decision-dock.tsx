"use client";

import { useKeybinds } from "@/lib/keybinds/use-keybinds";
import { cn } from "@/lib/utils";
import { useEffect, useRef, useState } from "react";
import type { AgentQuestion } from "@/lib/keybinds/types";

function DecisionDockInner({ question }: { question: AgentQuestion }) {
  const { ctx, dispatch } = useKeybinds();
  const [freeFormText, setFreeFormText] = useState("");
  const [urgency, setUrgency] = useState(0);
  const panelRef = useRef<HTMLDivElement>(null);
  const textInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    panelRef.current?.focus();
  }, []);

  // Timeout urgency visual
  useEffect(() => {
    const t1 = setTimeout(() => setUrgency(1), 30_000);
    const t2 = setTimeout(() => setUrgency(2), 60_000);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, []);

  // Handle Ctrl+Enter for free-form submit
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (
        e.ctrlKey &&
        e.key === "Enter" &&
        !e.shiftKey &&
        document.activeElement === textInputRef.current
      ) {
        e.preventDefault();
        e.stopPropagation();
        if (freeFormText.trim()) {
          dispatch({ type: "ANSWER_QUESTION", answer: freeFormText.trim() });
        }
      }
    }

    window.addEventListener("keydown", handleKey, true);
    return () => window.removeEventListener("keydown", handleKey, true);
  }, [freeFormText, dispatch]);

  const isYesNo = question.questionType === "yes_no";
  const isList = question.questionType === "list" && question.options;
  const isFreeForm = question.questionType === "free_form";

  return (
    <div className="fixed inset-x-0 bottom-0 z-40 flex justify-center pb-4 pointer-events-none">
      <div
        ref={panelRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-label="Agent Decision"
        className={cn(
          "pointer-events-auto bg-white rounded-xl shadow-2xl border w-full max-w-lg p-5 outline-none transition-colors",
          urgency === 0 && "border-slate-200",
          urgency === 1 && "border-amber-300 animate-pulse",
          urgency >= 2 && "border-amber-500 animate-pulse"
        )}
      >
        <p className="text-sm font-semibold text-slate-900 mb-4">
          {question.text}
        </p>

        {isYesNo && (
          <div className="flex gap-3 mb-4">
            <button
              onClick={() =>
                dispatch({ type: "ANSWER_QUESTION", answer: "yes" })
              }
              className="flex-1 py-2 rounded-lg text-sm font-medium border border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 transition-colors"
            >
              Yes
              <kbd className="ml-2 text-[10px] font-mono bg-white px-1.5 py-0.5 rounded border border-emerald-200">
                Ctrl+Shift+Y
              </kbd>
            </button>
            <button
              onClick={() =>
                dispatch({ type: "ANSWER_QUESTION", answer: "no" })
              }
              className="flex-1 py-2 rounded-lg text-sm font-medium border border-red-200 bg-red-50 text-red-700 hover:bg-red-100 transition-colors"
            >
              No
              <kbd className="ml-2 text-[10px] font-mono bg-white px-1.5 py-0.5 rounded border border-red-200">
                Ctrl+Shift+N
              </kbd>
            </button>
          </div>
        )}

        {isList && question.options && (
          <div className="space-y-1.5 mb-4">
            {question.options.map((opt, i) => (
              <button
                key={i}
                role="option"
                aria-selected={i === ctx.selectedOptionIndex}
                onClick={() => {
                  dispatch({ type: "ANSWER_QUESTION", answer: opt });
                }}
                className={cn(
                  "flex items-center gap-2 w-full text-left px-3 py-2 rounded-lg text-sm transition-colors border",
                  i === ctx.selectedOptionIndex
                    ? "bg-cyan-50 border-cyan-200 text-cyan-900"
                    : "bg-white border-slate-100 text-slate-700 hover:bg-slate-50"
                )}
              >
                <span
                  className={cn(
                    "text-xs",
                    i === ctx.selectedOptionIndex
                      ? "text-cyan-600"
                      : "text-slate-300"
                  )}
                >
                  {i === ctx.selectedOptionIndex ? "▸" : " "}
                </span>
                <span className="flex-1">{opt}</span>
              </button>
            ))}
          </div>
        )}

        {(isFreeForm || isList) && (
          <div className="mb-4">
            <input
              ref={textInputRef}
              type="text"
              placeholder="Or type a free-form answer..."
              value={freeFormText}
              onChange={(e) => setFreeFormText(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg outline-none focus:border-cyan-300 focus:ring-1 focus:ring-cyan-200 placeholder:text-slate-400"
              aria-label="Free-form answer"
            />
          </div>
        )}

        {urgency >= 1 && (
          <p className="text-xs text-amber-600 font-mono mb-3">
            {urgency === 1
              ? "Waiting for your input..."
              : "Agent is still waiting..."}
          </p>
        )}

        <div className="flex flex-wrap items-center gap-2 text-[10px] text-slate-400 font-mono border-t border-slate-100 pt-3">
          {isYesNo && (
            <>
              <span>Ctrl+Shift+Y yes</span>
              <span>·</span>
              <span>Ctrl+Shift+N no</span>
            </>
          )}
          {isList && (
            <>
              <span>Ctrl+J/K navigate</span>
              <span>·</span>
              <span>Ctrl+Shift+Enter confirm</span>
            </>
          )}
          <span>·</span>
          <span>Ctrl+Shift+Esc dismiss</span>
        </div>
      </div>
    </div>
  );
}

export function DecisionDock() {
  const { ctx } = useKeybinds();

  if (ctx.state !== "AWAITING_USER_DECISION" || !ctx.question) return null;

  return <DecisionDockInner question={ctx.question} />;
}
