"use client";

import { useEffect, useState } from "react";
import { AsiOneResults } from "@/components/publish/asi-one-results";
import { SlotChecklist } from "@/components/publish/slot-checklist";
import { PublishResults } from "@/components/publish/publish-results";
import { Button } from "@/components/ui/button";
import { fetchSlots, rankSlots, triggerPublish } from "@/lib/gateway";
import { toast } from "sonner";
import { Loader2, Send } from "lucide-react";
import type { ContentSlot, RankedSlot, PublishResult } from "@/lib/types/models";

export function PublishView() {
  const [slots, setSlots] = useState<ContentSlot[]>([]);
  const [ranked, setRanked] = useState<RankedSlot[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [results, setResults] = useState<PublishResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [publishing, setPublishing] = useState(false);

  useEffect(() => {
    async function load() {
      const slotsData = await fetchSlots();
      setSlots(slotsData);

      const approvedIds = slotsData
        .filter((s) => s.status === "approved")
        .map((s) => s.slot_id);

      if (approvedIds.length > 0) {
        const rankedData = await rankSlots(approvedIds);
        setRanked(rankedData);
        setSelected(new Set(rankedData.map((r) => r.slot_id)));
      }
      setLoading(false);
    }
    load();
  }, []);

  function handleToggle(slotId: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(slotId)) {
        next.delete(slotId);
      } else {
        next.add(slotId);
      }
      return next;
    });
  }

  async function handlePublish() {
    if (selected.size === 0) return;
    setPublishing(true);
    const publishResults = await triggerPublish(Array.from(selected));
    setResults(publishResults);
    setPublishing(false);
    const successes = publishResults.filter((r) => r.success).length;
    toast.success(`Published ${successes} slot(s)`);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-neutral-400">
        Loading slots and ASI:One rankings...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <AsiOneResults ranked={ranked} slots={slots} />
      <SlotChecklist
        slots={slots}
        selected={selected}
        onToggle={handleToggle}
      />
      <Button
        onClick={handlePublish}
        disabled={selected.size === 0 || publishing}
        size="lg"
        className="w-full"
      >
        {publishing ? (
          <>
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            Publishing...
          </>
        ) : (
          <>
            <Send className="h-4 w-4 mr-2" />
            Publish Selected ({selected.size})
          </>
        )}
      </Button>
      <PublishResults results={results} />
    </div>
  );
}
