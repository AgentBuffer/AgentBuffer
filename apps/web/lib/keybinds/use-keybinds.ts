"use client";

import { useContext } from "react";
import { KeybindContext, type KeybindContextValue } from "./provider";

/** Consume the keybind FSM context. Must be used inside <KeybindProvider>. */
export function useKeybinds(): KeybindContextValue {
  const value = useContext(KeybindContext);
  if (!value) {
    throw new Error("useKeybinds must be used within a <KeybindProvider>");
  }
  return value;
}
