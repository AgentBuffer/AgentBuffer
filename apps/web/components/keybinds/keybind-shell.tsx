"use client";

import type { ReactNode } from "react";
import { KeybindProvider } from "@/lib/keybinds/provider";
import { KeybindCheatSheet } from "./keybind-cheat-sheet";
import { CommandPalette } from "./command-palette";
import { PipelineSwitcher } from "./pipeline-switcher";
import { DecisionDock } from "./decision-dock";
import { KillConfirmToast } from "./kill-confirm-toast";
import { StateAnnouncer } from "./state-announcer";

/**
 * Wraps the dashboard content with the keybind FSM provider and all
 * overlay/modal components that respond to FSM state changes.
 */
export function KeybindShell({ children }: { children: ReactNode }) {
  return (
    <KeybindProvider>
      {children}

      {/* Overlays rendered outside the layout flow */}
      <KeybindCheatSheet />
      <CommandPalette />
      <PipelineSwitcher />
      <DecisionDock />
      <KillConfirmToast />
      <StateAnnouncer />
    </KeybindProvider>
  );
}
