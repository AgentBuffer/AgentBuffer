"use client";

import { Card } from "@/components/ui/card";
import { StatusBadge } from "./status-badge";
import { cn } from "@/lib/utils";
import type { ContentSlot } from "@/lib/types/models";

interface Props {
  slot: ContentSlot;
  onClick: () => void;
  selected?: boolean;
}

const platformLabels: Record<string, string> = {
  linkedin: "LinkedIn",
  x: "X",
  instagram: "IG",
};

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export function SlotCard({ slot, onClick, selected }: Props) {
  const day = DAYS[(slot.slot_number - 1) % 7];

  return (
    <Card
      className={cn(
        "cursor-pointer transition-all hover:shadow-md",
        selected && "ring-2 ring-cyan-600"
      )}
      onClick={onClick}
    >
      <div className="p-3 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-medium text-slate-500 font-mono uppercase">{day}</span>
          <span className="text-[10px] text-slate-400 font-mono">
            {platformLabels[slot.platform] ?? slot.platform}
          </span>
        </div>

        <div className="aspect-square rounded-md bg-slate-50 flex items-center justify-center overflow-hidden relative">
          {slot.image_url ? (
            <img
              src={slot.image_url}
              alt={`Slot ${slot.slot_number}`}
              className="w-full h-full object-cover"
            />
          ) : (
            <span className="text-2xl text-slate-300">
              {slot.slot_number}
            </span>
          )}
        </div>

        <p className="text-xs text-slate-600 line-clamp-2">{slot.caption}</p>

        <div className="flex items-center justify-between">
          <StatusBadge status={slot.status} />
          {slot.critic_average !== undefined && (
            <span
              className={cn(
                "text-xs font-semibold",
                slot.critic_average >= 3.5
                  ? "text-lime-600"
                  : "text-red-500"
              )}
            >
              {slot.critic_average.toFixed(1)}
            </span>
          )}
        </div>
      </div>
    </Card>
  );
}
