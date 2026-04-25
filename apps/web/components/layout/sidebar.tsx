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
    <aside className="w-56 shrink-0 border-r border-neutral-200 bg-neutral-50 flex flex-col">
      <div className="p-4 border-b border-neutral-200">
        <Link href="/dashboard/calendar" className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-neutral-900 flex items-center justify-center">
            <span className="text-white text-sm font-bold">AB</span>
          </div>
          <span className="font-semibold text-neutral-900">AgentBuffer</span>
        </Link>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-neutral-900 text-white"
                  : "text-neutral-600 hover:bg-neutral-200 hover:text-neutral-900"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
