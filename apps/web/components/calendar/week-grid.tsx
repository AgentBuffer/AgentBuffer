"use client";

import { useState } from "react";
import { SlotCard } from "./slot-card";
import { SlotDetail } from "./slot-detail";
import type { ContentSlot } from "@/lib/types/models";

interface Props {
  slots: ContentSlot[];
}

export function WeekGrid({ slots }: Props) {
  const [selectedSlotId, setSelectedSlotId] = useState<string | null>(null);
  const selectedSlot = slots.find((s) => s.slot_id === selectedSlotId);

  return (
    <div className="flex gap-6">
      <div className="flex-1">
        <div className="grid grid-cols-7 gap-3">
          {slots.map((slot) => (
            <SlotCard
              key={slot.slot_id}
              slot={slot}
              onClick={() =>
                setSelectedSlotId(
                  selectedSlotId === slot.slot_id ? null : slot.slot_id
                )
              }
              selected={selectedSlotId === slot.slot_id}
            />
          ))}
        </div>
      </div>

      {selectedSlot && (
        <div className="shrink-0">
          <SlotDetail
            slot={selectedSlot}
            onClose={() => setSelectedSlotId(null)}
          />
        </div>
      )}
    </div>
  );
}
