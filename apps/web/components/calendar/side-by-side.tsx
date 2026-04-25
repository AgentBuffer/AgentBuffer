"use client";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { ContentSlot } from "@/lib/types/models";

interface Props {
  before: ContentSlot;
  after: ContentSlot;
  seed?: string;
}

export function SideBySide({ before, after, seed }: Props) {
  return (
    <Card>
      <CardHeader>
        <h3 className="font-semibold">
          Slot {before.slot_number} &mdash; Regenerated
        </h3>
        {seed && (
          <p className="text-[10px] text-slate-400 font-mono">
            Same seed: {seed}
          </p>
        )}
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest font-mono">
              Before
            </span>
            <div className="aspect-square rounded-md bg-slate-50 flex items-center justify-center">
              {before.image_url ? (
                <img
                  src={before.image_url}
                  alt="Before"
                  className="w-full h-full object-cover rounded-lg"
                />
              ) : (
                <span className="text-slate-300 font-mono">v1</span>
              )}
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-red-600 font-semibold">
                {before.critic_average?.toFixed(1)}/5
              </span>
              <span className="text-xs text-red-600 font-semibold uppercase">
                Rejected
              </span>
            </div>
          </div>

          <div className="space-y-2">
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest font-mono">
              After
            </span>
            <div className="aspect-square rounded-md bg-slate-50 flex items-center justify-center">
              {after.image_url ? (
                <img
                  src={after.image_url}
                  alt="After"
                  className="w-full h-full object-cover rounded-lg"
                />
              ) : (
                <span className="text-slate-300 font-mono">v2</span>
              )}
            </div>
            <div className="flex items-center justify-between">
              <span
                className={cn(
                  "text-xs font-semibold",
                  (after.critic_average ?? 0) >= 3.5
                    ? "text-lime-600"
                    : "text-red-500"
                )}
              >
                {after.critic_average?.toFixed(1)}/5
              </span>
              <span
                className={cn(
                  "text-xs font-semibold uppercase",
                  after.status === "approved"
                    ? "text-lime-600"
                    : "text-red-500"
                )}
              >
                {after.status}
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
