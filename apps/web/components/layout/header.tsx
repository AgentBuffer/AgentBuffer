"use client";

import { Button } from "@/components/ui/button";
import { LogOut } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";

interface HeaderProps {
  brandName?: string;
}

export function Header({ brandName }: HeaderProps) {
  const router = useRouter();

  async function handleSignOut() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
  }

  return (
    <header className="h-14 border-b border-neutral-200 bg-white flex items-center justify-between px-6">
      <div className="flex items-center gap-3">
        <h1 className="text-sm font-semibold text-neutral-900">AgentBuffer</h1>
        {brandName && (
          <>
            <span className="text-neutral-300">/</span>
            <span className="text-sm text-neutral-600">{brandName}</span>
          </>
        )}
      </div>
      <Button variant="ghost" size="sm" onClick={handleSignOut}>
        <LogOut className="h-4 w-4 mr-1.5" />
        Sign out
      </Button>
    </header>
  );
}
