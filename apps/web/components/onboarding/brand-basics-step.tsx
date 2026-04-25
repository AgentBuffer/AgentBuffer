"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import type { BrandFormData } from "./onboarding-wizard";

interface Props {
  form: BrandFormData;
  onChange: (updates: Partial<BrandFormData>) => void;
  onNext: () => void;
}

export function BrandBasicsStep({ form, onChange, onNext }: Props) {
  const canProceed =
    form.name.trim() && form.industry.trim() && form.tagline.trim();

  return (
    <Card>
      <CardHeader>
        <h2 className="text-lg font-semibold">Brand Basics</h2>
        <p className="text-sm text-neutral-500">
          Tell us about your brand so our AI agents can create on-brand content.
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Brand name</label>
          <Input
            placeholder="lumen.coffee"
            value={form.name}
            onChange={(e) => onChange({ name: e.target.value })}
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Industry</label>
          <Input
            placeholder="Coffee & Beverage"
            value={form.industry}
            onChange={(e) => onChange({ industry: e.target.value })}
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Tagline</label>
          <Input
            placeholder="Light up your morning"
            value={form.tagline}
            onChange={(e) => onChange({ tagline: e.target.value })}
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Target audience</label>
          <Textarea
            placeholder="Urban professionals aged 25-40 who appreciate specialty coffee"
            value={form.target_audience}
            onChange={(e) => onChange({ target_audience: e.target.value })}
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Brand voice</label>
          <Textarea
            placeholder="Warm, artisan, approachable. We speak like a knowledgeable barista..."
            value={form.voice_description}
            onChange={(e) => onChange({ voice_description: e.target.value })}
          />
        </div>
        <div className="flex justify-end pt-2">
          <Button onClick={onNext} disabled={!canProceed}>
            Next
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
