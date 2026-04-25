"use client";

import { useEffect, useState } from "react";
import { WeekGrid } from "@/components/calendar/week-grid";
import { fetchCalendar } from "@/lib/gateway";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { ContentSlot, Platform } from "@/lib/types/models";

const PLATFORM_OPTIONS: { value: Platform | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "instagram" as Platform, label: "Instagram" },
  { value: "x" as Platform, label: "X" },
  { value: "linkedin" as Platform, label: "LinkedIn" },
  { value: "tiktok" as Platform, label: "TikTok" },
];

function mondayOf(date: Date): Date {
  const d = new Date(date);
  d.setUTCDate(d.getUTCDate() - ((d.getUTCDay() + 6) % 7));
  d.setUTCHours(0, 0, 0, 0);
  return d;
}

function formatWeekLabel(monday: Date): string {
  const sun = new Date(monday);
  sun.setUTCDate(sun.getUTCDate() + 6);
  const opts: Intl.DateTimeFormatOptions = { month: "short", day: "numeric" };
  const start = monday.toLocaleDateString("en-US", { ...opts, timeZone: "UTC" });
  const end = sun.toLocaleDateString("en-US", { ...opts, timeZone: "UTC" });
  return `${start} – ${end}`;
}

function toDateStr(d: Date): string {
  return d.toISOString().slice(0, 10);
}

export function CalendarView() {
  const [weekOffset, setWeekOffset] = useState(0);
  const [slots, setSlots] = useState<ContentSlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [platformFilter, setPlatformFilter] = useState<Platform | "all">("all");

  const currentMonday = mondayOf(new Date());

  const displayedMonday = new Date(currentMonday);
  displayedMonday.setUTCDate(displayedMonday.getUTCDate() + weekOffset * 7);

  const weekStart = toDateStr(displayedMonday);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      const data = await fetchCalendar("brand-001", weekStart);
      if (!cancelled) {
        setSlots(data.posts);
        setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [weekStart]);

  const reloadWeek = async () => {
    setLoading(true);
    const data = await fetchCalendar("brand-001", weekStart);
    setSlots(data.posts);
    setLoading(false);
  };

  const filteredSlots =
    platformFilter === "all"
      ? slots
      : slots.filter((s) => s.platform === platformFilter);

  const isCurrentWeek = weekOffset === 0;

  return (
    <div className="space-y-4">
      {/* Week navigation */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setWeekOffset((o) => o - 1)}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-sm font-semibold font-mono min-w-[180px] text-center">
            {formatWeekLabel(displayedMonday)}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setWeekOffset((o) => o + 1)}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
          {!isCurrentWeek && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setWeekOffset(0)}
            >
              Today
            </Button>
          )}
        </div>

        {/* Platform filter */}
        <div className="flex items-center gap-1">
          {PLATFORM_OPTIONS.map((opt) => (
            <Button
              key={opt.value}
              variant={platformFilter === opt.value ? "default" : "outline"}
              size="sm"
              onClick={() => setPlatformFilter(opt.value)}
            >
              {opt.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Week grid */}
      {loading ? (
        <div className="flex items-center justify-center h-64 text-slate-400 font-mono text-sm">
          Loading content slots...
        </div>
      ) : (
        <WeekGrid
          slots={filteredSlots}
          weekStart={weekStart}
          onSlotsChanged={reloadWeek}
        />
      )}
    </div>
  );
}
