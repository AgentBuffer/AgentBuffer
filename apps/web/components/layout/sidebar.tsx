"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  Sparkles,
  Calendar,
  MessageSquare,
  Send,
} from "lucide-react";

const navItems = [
  { href: "/dashboard/onboard", label: "Onboard", icon: Sparkles },
  { href: "/dashboard/calendar", label: "Calendar", icon: Calendar },
  { href: "/dashboard/messages", label: "Messages", icon: MessageSquare },
  { href: "/dashboard/publish", label: "Publish", icon: Send },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 shrink-0 bg-[#0F172A] flex flex-col">
      <div className="p-4 border-b border-[#1E293B]">
        <Link href="/dashboard/calendar" className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-md border-2 border-cyan-600 flex items-center justify-center">
            <span className="text-white text-sm font-bold">AB</span>
          </div>
          <span className="font-semibold text-slate-200">AgentBuffer</span>
        </Link>
      </div>
      <nav className="flex-1 p-3 space-y-0.5">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 text-xs font-medium font-mono uppercase tracking-wide transition-colors rounded-md",
                isActive
                  ? "text-white border-l-[3px] border-l-cyan-400 ml-[-3px]"
                  : "text-slate-400 hover:bg-white/5 hover:text-slate-300"
              )}
            >
              <item.icon className="h-4 w-4 opacity-60" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
