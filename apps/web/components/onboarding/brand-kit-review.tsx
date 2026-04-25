"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Check } from "lucide-react";
import type { BrandKit } from "@/lib/types/models";

interface Props {
  brandKit: BrandKit;
}

export function BrandKitReview({ brandKit }: Props) {
  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div className="h-10 w-10 rounded-full bg-cyan-100 flex items-center justify-center">
          <Check className="h-5 w-5 text-cyan-600" />
        </div>
        <div>
          <h2 className="text-lg font-semibold">Brand Kit Extracted</h2>
          <p className="text-sm text-slate-500">
            AI has analyzed your brand. Review the results below.
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <h3 className="font-semibold">{brandKit.name}</h3>
          <p className="text-sm text-slate-500">{brandKit.industry}</p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest font-mono">
              Tagline
            </label>
            <p className="text-sm mt-1">{brandKit.tagline}</p>
          </div>
          <div>
            <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest font-mono">
              Brand Voice
            </label>
            <p className="text-sm mt-1">{brandKit.voice_description}</p>
          </div>
          <div>
            <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest font-mono">
              Target Audience
            </label>
            <p className="text-sm mt-1">{brandKit.target_audience}</p>
          </div>
          <div>
            <label className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest font-mono">
              Color Palette
            </label>
            <div className="flex gap-2 mt-2">
              {brandKit.color_palette.map((color) => (
                <div key={color} className="flex items-center gap-1.5">
                  <div
                    className="h-6 w-6 rounded-md border border-slate-200"
                    style={{ backgroundColor: color }}
                  />
                  <span className="text-xs text-slate-500 font-mono">
                    {color}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Link href="/dashboard/calendar">
          <Button size="lg">Go to Calendar</Button>
        </Link>
      </div>
    </div>
  );
}
