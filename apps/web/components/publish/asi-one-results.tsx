"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Star } from "lucide-react";
import type { RankedSlot, ContentSlot } from "@/lib/types/models";

interface Props {
  ranked: RankedSlot[];
  slots: ContentSlot[];
}

const platformLabels: Record<string, string> = {
  linkedin: "LinkedIn",
  x: "X",
  instagram: "Instagram",
};

export function AsiOneResults({ ranked, slots }: Props) {
  if (ranked.length === 0) return null;

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-neutral-700">
        ASI:One recommends these slots:
      </h3>
      {ranked.map((r) => {
        const slot = slots.find((s) => s.slot_id === r.slot_id);
        if (!slot) return null;
        return (
          <Card key={r.slot_id}>
            <CardContent className="py-3">
              <div className="flex items-start gap-3">
                <div className="h-8 w-8 rounded-full bg-amber-100 flex items-center justify-center shrink-0">
                  <Star className="h-4 w-4 text-amber-600" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-semibold">
                    #{r.rank}: Slot {slot.slot_number} (
                    {platformLabels[slot.platform] ?? slot.platform})
                  </p>
                  <p className="text-sm text-neutral-600 line-clamp-1 mt-0.5">
                    &ldquo;{slot.caption}&rdquo;
                  </p>
                  <p className="text-xs text-neutral-400 mt-1">
                    {r.reasoning}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
