"use client";

import { useState } from "react";
import { SlotCard } from "./slot-card";
import { SlotDetail } from "./slot-detail";
import { AddPostForm } from "./add-post-form";
import type { ContentSlot } from "@/lib/types/models";

interface Props {
  slots: ContentSlot[];
  weekStart: string;
  onSlotsChanged: () => void;
}

const DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function dayDates(weekStart: string): Date[] {
  const mon = new Date(weekStart + "T00:00:00Z");
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(mon);
    d.setUTCDate(d.getUTCDate() + i);
    return d;
  });
}

function isSameUTCDay(a: Date, b: Date): boolean {
  return (
    a.getUTCFullYear() === b.getUTCFullYear() &&
    a.getUTCMonth() === b.getUTCMonth() &&
    a.getUTCDate() === b.getUTCDate()
  );
}

function isToday(d: Date): boolean {
  return isSameUTCDay(d, new Date());
}

export function WeekGrid({ slots, weekStart, onSlotsChanged }: Props) {
  const [selectedSlotId, setSelectedSlotId] = useState<string | null>(null);
  const [addingDay, setAddingDay] = useState<string | null>(null);
  const [showSkipped, setShowSkipped] = useState(false);

  const dates = dayDates(weekStart);
  const selectedSlot = slots.find((s) => s.slot_id === selectedSlotId);

  const buckets: Map<string, ContentSlot[]> = new Map();
  for (const d of dates) {
    buckets.set(d.toISOString().slice(0, 10), []);
  }
  for (const slot of slots) {
    if (!showSkipped && slot.status === "skipped") continue;
    const key = new Date(slot.scheduled_for).toISOString().slice(0, 10);
    buckets.get(key)?.push(slot);
  }

  return (
    <div className="space-y-4">
      {/* Toggle skipped */}
      <div className="flex justify-end">
        <button
          onClick={() => setShowSkipped(!showSkipped)}
          className="text-xs text-slate-400 hover:text-slate-600 font-mono"
        >
          {showSkipped ? "Hide skipped" : "Show skipped"}
        </button>
      </div>

      {/* Day columns */}
      <div className="grid grid-cols-7 gap-3">
        {dates.map((date, i) => {
          const key = date.toISOString().slice(0, 10);
          const daySlots = buckets.get(key) ?? [];
          const today = isToday(date);

          return (
            <div key={key} className="min-h-[160px]">
              {/* Day header */}
              <div
                className={`text-center mb-2 pb-1 border-b ${
                  today
                    ? "border-cyan-400"
                    : "border-slate-200"
                }`}
              >
                <span className="text-[10px] font-semibold font-mono uppercase tracking-widest text-slate-500">
                  {DAY_LABELS[i]}
                </span>
                <div
                  className={`text-sm font-semibold ${
                    today
                      ? "text-cyan-600"
                      : "text-slate-700"
                  }`}
                >
                  {date.getUTCDate()}
                </div>
              </div>

              {/* Slot chips */}
              <div className="space-y-2">
                {daySlots.length === 0 && (
                  <div className="text-center text-[10px] text-slate-300 font-mono py-4">
                    —
                  </div>
                )}
                {daySlots.map((slot) => (
                  <SlotCard
                    key={slot.slot_id}
                    slot={slot}
                    onClick={() =>
                      setSelectedSlotId(
                        selectedSlotId === slot.slot_id ? null : slot.slot_id,
                      )
                    }
                    selected={selectedSlotId === slot.slot_id}
                  />
                ))}
              </div>

              {/* + Add button */}
              <button
                onClick={() => setAddingDay(key)}
                className="mt-2 w-full text-[10px] text-slate-400 hover:text-cyan-600 font-mono py-1 border border-dashed border-slate-200 hover:border-cyan-400 rounded transition-colors"
              >
                + Add
              </button>
            </div>
          );
        })}
      </div>

      {/* Add post form */}
      {addingDay && (
        <AddPostForm
          defaultDate={addingDay}
          onClose={() => setAddingDay(null)}
          onAdded={onSlotsChanged}
        />
      )}

      {/* Inline detail panel (below the grid, not a modal) */}
      {selectedSlot && (
        <SlotDetail
          slot={selectedSlot}
          onClose={() => setSelectedSlotId(null)}
          onAction={onSlotsChanged}
        />
      )}
    </div>
  );
}
