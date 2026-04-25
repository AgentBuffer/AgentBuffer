"use client";

import { Button } from "@/components/ui/button";
import { StateBadge } from "@/components/keybinds/state-badge";
import { LogOut, Keyboard } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import { useContext } from "react";
import { KeybindContext } from "@/lib/keybinds/provider";

interface HeaderProps {
  brandName?: string;
}

export function Header({ brandName }: HeaderProps) {
  const router = useRouter();
  const keybindCtx = useContext(KeybindContext);

  async function handleSignOut() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
  }

  return (
    <header className="h-13 border-b border-slate-200 bg-white flex items-center justify-between px-6">
      <div className="flex items-center gap-3">
        <h1 className="text-sm font-semibold text-slate-900">AgentBuffer</h1>
        {brandName && (
          <>
            <span className="text-slate-300">/</span>
            <span className="text-sm text-slate-500">{brandName}</span>
          </>
        )}
        {keybindCtx && <StateBadge />}
      </div>
      <div className="flex items-center gap-2">
        {keybindCtx && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() =>
              keybindCtx.dispatch({ type: "TOGGLE_KEYBIND_CHEAT_SHEET" })
            }
            aria-label="Keybind cheat sheet"
          >
            <Keyboard className="h-4 w-4 mr-1.5 opacity-60" />
            <span className="font-mono text-[10px] text-slate-400">
              Ctrl+Shift+/
            </span>
          </Button>
        )}
        <Button variant="ghost" size="sm" onClick={handleSignOut}>
          <LogOut className="h-4 w-4 mr-1.5" />
          <span className="font-mono text-xs uppercase">Sign out</span>
        </Button>
      </div>
    </header>
  );
}
