"use client";

import { cn } from "@/lib/utils";
import type { ContentSlot } from "@/lib/types/models";

interface Props {
  slot: ContentSlot;
  onClick: () => void;
  selected?: boolean;
}

const PLATFORM_COLORS: Record<string, string> = {
  instagram: "border-l-rose-400 bg-rose-50/50",
  x: "border-l-blue-400 bg-blue-50/50",
  linkedin: "border-l-teal-400 bg-teal-50/50",
  tiktok: "border-l-amber-400 bg-amber-50/50",
};

const PLATFORM_LABELS: Record<string, string> = {
  linkedin: "LinkedIn",
  x: "X",
  instagram: "IG",
  tiktok: "TikTok",
};

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    timeZone: "UTC",
  });
}

export function SlotCard({ slot, onClick, selected }: Props) {
  const colorClass = PLATFORM_COLORS[slot.platform] ?? "border-l-slate-300 bg-slate-50/50";
  const isPublished = slot.status === "published";
  const isPending = slot.status === "pending";
  const isApproved = slot.status === "approved";
  const isSkipped = slot.status === "skipped";

  return (
    <button
      type="button"
      className={cn(
        "w-full text-left rounded-md border-l-[3px] p-2 transition-all cursor-pointer text-xs",
        colorClass,
        selected && "ring-2 ring-cyan-600 shadow-md",
        isPublished && "opacity-50",
        isPending && "border border-dashed border-slate-300",
        isSkipped && "line-through opacity-40",
      )}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-0.5">
        <span className="text-[10px] font-semibold font-mono text-slate-500">
          {PLATFORM_LABELS[slot.platform] ?? slot.platform}
        </span>
        <span className="text-[10px] text-slate-400 font-mono">
          {formatTime(slot.scheduled_for)}
        </span>
      </div>
      <p className="text-slate-700 line-clamp-2 leading-tight">
        {slot.caption}
      </p>
      <div className="flex items-center gap-1 mt-1">
        {/* Status indicator dot */}
        {isApproved && (
          <span className="inline-block h-2 w-2 rounded-full bg-lime-500" />
        )}
        {isPending && (
          <span className="inline-block h-2 w-2 rounded-full border border-amber-500" />
        )}
        {isPublished && (
          <span className="inline-block h-2 w-2 rounded-full bg-violet-400" />
        )}
      </div>
    </button>
  );
}
