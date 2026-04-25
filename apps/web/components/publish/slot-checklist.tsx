"use client";

import { cn } from "@/lib/utils";
import type { ContentSlot } from "@/lib/types/models";

interface Props {
  slots: ContentSlot[];
  selected: Set<string>;
  onToggle: (slotId: string) => void;
}

const platformLabels: Record<string, string> = {
  linkedin: "LinkedIn",
  x: "X",
  instagram: "IG",
};

export function SlotChecklist({ slots, selected, onToggle }: Props) {
  const approvedSlots = slots.filter((s) => s.status === "approved");

  return (
    <div className="space-y-2">
      <h3 className="text-xs font-semibold text-slate-700 font-mono uppercase tracking-wider">
        All approved slots:
      </h3>
      {approvedSlots.map((slot) => {
        const isIG = slot.platform === "instagram";
        const checked = selected.has(slot.slot_id);

        return (
          <label
            key={slot.slot_id}
            className={cn(
              "flex items-center gap-3 rounded-lg border px-3 py-2 cursor-pointer transition-colors",
              checked
                ? "border-cyan-600 bg-cyan-50/50"
                : "border-slate-200 hover:border-cyan-300"
            )}
          >
            <input
              type="checkbox"
              checked={checked}
              onChange={() => onToggle(slot.slot_id)}
              disabled={isIG}
              className="rounded"
            />
            <span className="text-sm flex-1">
              Slot {slot.slot_number} &middot;{" "}
              {platformLabels[slot.platform] ?? slot.platform} &middot;{" "}
              <span className="font-medium">
                {slot.critic_average?.toFixed(1)}/5
              </span>
            </span>
            {isIG && (
              <span className="text-[10px] bg-violet-50 text-violet-600 px-2 py-0.5 rounded font-mono">
                queued for review
              </span>
            )}
          </label>
        );
      })}
    </div>
  );
}
