"use client";

import {
  createContext,
  useCallback,
  useEffect,
  useReducer,
  useRef,
  type ReactNode,
} from "react";
import { fsmReducer, INITIAL_STATE, toUIContext, type FSMState } from "./state-machine";
import { findKeybind, isActiveInState, toChord } from "./registry";
import type { UIContext, UIEvent } from "./types";

export interface KeybindContextValue {
  ctx: UIContext;
  dispatch: (event: UIEvent) => void;
  fsmState: FSMState;
}

export const KeybindContext = createContext<KeybindContextValue | null>(null);

const KILL_TIMEOUT_MS = 2000;

export function KeybindProvider({ children }: { children: ReactNode }) {
  const [fsmState, dispatch] = useReducer(fsmReducer, INITIAL_STATE);
  const ctx = toUIContext(fsmState);

  // Refs synced via effects to satisfy React 19 lint rules
  const ctxRef = useRef(ctx);
  const dispatchRef = useRef(dispatch);

  useEffect(() => {
    ctxRef.current = ctx;
  }, [ctx]);

  useEffect(() => {
    dispatchRef.current = dispatch;
  }, [dispatch]);

  // Kill double-tap timer
  const killTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (fsmState.killArmed) {
      killTimerRef.current = setTimeout(() => {
        dispatchRef.current({ type: "KILL_DISARM" });
      }, KILL_TIMEOUT_MS);
    } else if (killTimerRef.current) {
      clearTimeout(killTimerRef.current);
      killTimerRef.current = null;
    }
    return () => {
      if (killTimerRef.current) {
        clearTimeout(killTimerRef.current);
      }
    };
  }, [fsmState.killArmed]);

  // Global keydown handler
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    const chord = toChord(e);
    if (!chord) return;

    const binding = findKeybind(chord);
    if (!binding) return;

    const currentCtx = ctxRef.current;
    if (!isActiveInState(binding, currentCtx.state)) return;

    e.preventDefault();
    e.stopPropagation();
    binding.handler(dispatchRef.current, currentCtx);
  }, []);

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown, true);
    return () => window.removeEventListener("keydown", handleKeyDown, true);
  }, [handleKeyDown]);

  return (
    <KeybindContext.Provider value={{ ctx, dispatch, fsmState }}>
      {children}
    </KeybindContext.Provider>
  );
}
