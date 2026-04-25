"use client";

import { useKeybinds } from "@/lib/keybinds/use-keybinds";
import { cn } from "@/lib/utils";

export function KillConfirmToast() {
  const { ctx } = useKeybinds();

  if (!ctx.killArmed || ctx.state !== "AGENT_STREAMING") return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 pointer-events-none">
      <div
        role="alert"
        aria-live="assertive"
        className={cn(
          "pointer-events-auto bg-red-50 border border-red-300 text-red-800 rounded-lg px-4 py-3 shadow-lg",
          "animate-pulse"
        )}
      >
        <p className="text-sm font-semibold">Kill process armed</p>
        <p className="text-xs text-red-600 font-mono mt-1">
          Press{" "}
          <kbd className="bg-white border border-red-200 px-1.5 py-0.5 rounded">
            Ctrl+Shift+K
          </kbd>{" "}
          again to confirm
        </p>
      </div>
    </div>
  );
}
