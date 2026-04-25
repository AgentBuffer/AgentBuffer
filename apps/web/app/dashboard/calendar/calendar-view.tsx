"use client";

import { useEffect, useState } from "react";
import { WeekGrid } from "@/components/calendar/week-grid";
import { fetchSlots } from "@/lib/gateway";
import type { ContentSlot } from "@/lib/types/models";

export function CalendarView() {
  const [slots, setSlots] = useState<ContentSlot[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSlots().then((data) => {
      setSlots(data);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400 font-mono text-sm">
        Loading content slots...
      </div>
    );
  }

  if (slots.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400 font-mono text-sm">
        No content slots yet. Onboard a brand to generate your first slate.
      </div>
    );
  }

  return <WeekGrid slots={slots} />;
}
