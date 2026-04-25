"use client";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "./status-badge";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";
import type { ContentSlot } from "@/lib/types/models";

interface Props {
  slot: ContentSlot;
  onClose: () => void;
}

const platformLabels: Record<string, string> = {
  linkedin: "LinkedIn",
  x: "X",
  instagram: "Instagram",
};

export function SlotDetail({ slot, onClose }: Props) {
  return (
    <Card className="max-w-md">
      <CardHeader className="flex flex-row items-start justify-between">
        <div>
          <h3 className="font-semibold">
            Slot {slot.slot_number} &mdash;{" "}
            {platformLabels[slot.platform] ?? slot.platform}
          </h3>
          <div className="mt-1">
            <StatusBadge status={slot.status} />
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-600"
        >
          <X className="h-5 w-5" />
        </button>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="aspect-video rounded-md bg-slate-50 flex items-center justify-center overflow-hidden">
          {slot.image_url ? (
            <img
              src={slot.image_url}
              alt={`Slot ${slot.slot_number}`}
              className="w-full h-full object-cover"
            />
          ) : (
            <span className="text-slate-300 text-sm">No image generated</span>
          )}
        </div>

        <div>
          <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest font-mono">
            Caption
          </label>
          <p className="text-sm mt-1">{slot.caption}</p>
        </div>

        {slot.critic_scores && slot.critic_scores.length > 0 && (
          <div>
            <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest font-mono">
              Critic Scores
            </label>
            <div className="mt-2 border border-slate-200 rounded-md overflow-hidden">
              <table className="w-full text-sm">
                <tbody>
                  {slot.critic_scores.map((score) => (
                    <tr
                      key={score.axis}
                      className="border-b border-slate-100 last:border-b-0"
                    >
                      <td className="px-3 py-2 text-slate-600">
                        {score.axis}
                      </td>
                      <td
                        className={cn(
                          "px-3 py-2 text-right font-semibold",
                          score.score >= 3.5
                            ? "text-lime-600"
                            : "text-red-500"
                        )}
                      >
                        {score.score.toFixed(1)}
                      </td>
                    </tr>
                  ))}
                  {slot.critic_average !== undefined && (
                    <tr className="bg-slate-50 font-semibold">
                      <td className="px-3 py-2">Average</td>
                      <td
                        className={cn(
                          "px-3 py-2 text-right",
                          slot.critic_average >= 3.5
                            ? "text-lime-600"
                            : "text-red-500"
                        )}
                      >
                        {slot.critic_average.toFixed(1)}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {slot.critic_summary && (
          <div>
            <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest font-mono">
              Critic Note
            </label>
            <p className="text-sm mt-1 text-slate-500 italic">
              &ldquo;{slot.critic_summary}&rdquo;
            </p>
          </div>
        )}

        {slot.status === "rejected" && (
          <Button className="w-full">Regenerate Slot</Button>
        )}
      </CardContent>
    </Card>
  );
}
