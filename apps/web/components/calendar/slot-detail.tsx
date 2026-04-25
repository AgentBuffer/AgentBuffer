"use client";

import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "./status-badge";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";
import { approveSlot, skipSlot, regenerateSlot } from "@/lib/gateway";
import type { ContentSlot } from "@/lib/types/models";

interface Props {
  slot: ContentSlot;
  onClose: () => void;
  onAction: () => void;
}

const PLATFORM_LABELS: Record<string, string> = {
  linkedin: "LinkedIn",
  x: "X / Twitter",
  instagram: "Instagram",
  tiktok: "TikTok",
};

const CRITIC_AXES = [
  "Brand Voice Alignment",
  "Visual Coherence",
  "Platform Fit",
  "Audience Relevance",
  "Originality",
];

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZone: "UTC",
  });
}

export function SlotDetail({ slot, onClose, onAction }: Props) {
  async function handleApprove() {
    await approveSlot(slot.slot_id);
    onAction();
  }

  async function handleSkip() {
    await skipSlot(slot.slot_id);
    onAction();
  }

  async function handleRegenerate() {
    await regenerateSlot(slot.slot_id);
    onAction();
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between">
        <div>
          <h3 className="font-semibold">
            {PLATFORM_LABELS[slot.platform] ?? slot.platform}
          </h3>
          <p className="text-xs text-slate-500 font-mono mt-0.5">
            {formatDateTime(slot.scheduled_for)}
          </p>
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
        {/* Full content */}
        <div>
          <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest font-mono">
            Content
          </label>
          <p className="text-sm mt-1">{slot.caption}</p>
        </div>

        {/* Critic scores as labeled cells */}
        {slot.critic_scores && slot.critic_scores.length > 0 && (
          <div>
            <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest font-mono">
              Critic Scores
            </label>
            <div className="mt-2 grid grid-cols-3 gap-2">
              {CRITIC_AXES.map((axis) => {
                const found = slot.critic_scores?.find((s) => s.axis === axis);
                if (!found) return null;
                return (
                  <div
                    key={axis}
                    className="rounded-md border border-slate-200 p-2 text-center"
                  >
                    <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wide mb-1">
                      {axis.replace("Brand Voice Alignment", "Brand Fit")}
                    </div>
                    <div
                      className={cn(
                        "text-lg font-bold",
                        found.score >= 3.5 ? "text-lime-600" : "text-red-500",
                      )}
                    >
                      {found.score.toFixed(1)}
                    </div>
                  </div>
                );
              })}
              {slot.critic_average !== undefined && (
                <div className="rounded-md border border-slate-200 bg-slate-50 p-2 text-center">
                  <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wide mb-1">
                    Average
                  </div>
                  <div
                    className={cn(
                      "text-lg font-bold",
                      slot.critic_average >= 3.5
                        ? "text-lime-600"
                        : "text-red-500",
                    )}
                  >
                    {slot.critic_average.toFixed(1)}
                  </div>
                </div>
              )}
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

        {/* Engagement metrics for published posts */}
        {slot.status === "published" && slot.engagement && (
          <div>
            <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest font-mono">
              Engagement
            </label>
            <div className="mt-2 grid grid-cols-5 gap-2">
              {[
                { label: "Likes", value: slot.engagement.likes },
                { label: "Shares", value: slot.engagement.shares },
                { label: "Comments", value: slot.engagement.comments },
                { label: "Reach", value: slot.engagement.reach },
                {
                  label: "Rate",
                  value: `${slot.engagement.engagement_rate.toFixed(1)}%`,
                },
              ].map((m) => (
                <div
                  key={m.label}
                  className="rounded-md border border-slate-200 p-2 text-center"
                >
                  <div className="text-[10px] font-mono text-slate-500 uppercase">
                    {m.label}
                  </div>
                  <div className="text-sm font-bold text-slate-700">
                    {m.value}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/*
         * TODO: Wire PerformanceHarvester engagement data here.
         * When perf:{user_id}:{brand_id}:{post_id} is available,
         * read engagement metrics and display them for published posts
         * that don't yet have the engagement field populated.
         */}

        {/* Context-aware action buttons */}
        <div className="flex gap-2 pt-2">
          {slot.status === "pending" && (
            <>
              <Button onClick={handleApprove} size="sm">
                Approve
              </Button>
              <Button onClick={handleSkip} variant="outline" size="sm">
                Skip
              </Button>
              <Button onClick={handleRegenerate} variant="outline" size="sm">
                Regenerate
              </Button>
            </>
          )}
          {slot.status === "approved" && (
            <>
              <Button onClick={handleSkip} variant="outline" size="sm">
                Skip
              </Button>
              <Button onClick={handleRegenerate} variant="outline" size="sm">
                Regenerate
              </Button>
            </>
          )}
          {slot.status === "published" && (
            <a
              href="https://app.ayrshare.com/analytics"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center rounded-lg font-medium transition-colors border border-slate-200 bg-white hover:bg-slate-50 h-8 px-3 text-sm"
            >
              View Analytics
            </a>
          )}
        </div>

        {slot.note && (
          <p className="text-[10px] text-slate-400 font-mono italic">
            {slot.note}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
