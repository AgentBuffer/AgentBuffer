"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { addManualPost } from "@/lib/gateway";
import { X } from "lucide-react";

interface Props {
  defaultDate: string;
  onClose: () => void;
  onAdded: () => void;
}

const PLATFORMS = [
  { value: "instagram", label: "Instagram" },
  { value: "x", label: "X" },
  { value: "linkedin", label: "LinkedIn" },
  { value: "tiktok", label: "TikTok" },
];

export function AddPostForm({ defaultDate, onClose, onAdded }: Props) {
  const [platform, setPlatform] = useState("instagram");
  const [time, setTime] = useState("09:00");
  const [content, setContent] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!content.trim()) return;
    setSubmitting(true);
    await addManualPost({
      platform,
      scheduled_for: `${defaultDate}T${time}:00Z`,
      content_text: content,
    });
    setSubmitting(false);
    onAdded();
    onClose();
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between">
        <div>
          <h3 className="font-semibold text-sm">Add Manual Post</h3>
          <p className="text-[10px] text-slate-500 font-mono mt-0.5">
            {defaultDate} &middot; Manual posts bypass the Critic and are
            auto-approved.
          </p>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-600"
        >
          <X className="h-5 w-5" />
        </button>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="flex gap-3">
            <div className="flex-1">
              <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest font-mono">
                Platform
              </label>
              <div className="flex gap-1 mt-1">
                {PLATFORMS.map((p) => (
                  <Button
                    key={p.value}
                    type="button"
                    variant={platform === p.value ? "default" : "outline"}
                    size="sm"
                    onClick={() => setPlatform(p.value)}
                  >
                    {p.label}
                  </Button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest font-mono">
                Time (UTC)
              </label>
              <Input
                type="time"
                value={time}
                onChange={(e) => setTime(e.target.value)}
                className="mt-1 w-28"
              />
            </div>
          </div>

          <div>
            <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest font-mono">
              Content
            </label>
            <Textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Write your post content..."
              rows={3}
              className="mt-1"
            />
          </div>

          <Button type="submit" disabled={submitting || !content.trim()}>
            {submitting ? "Adding..." : "Add Post"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
