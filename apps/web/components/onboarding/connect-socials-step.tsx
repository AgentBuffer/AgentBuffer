"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Sparkles, Loader2 } from "lucide-react";
import type { BrandFormData } from "./onboarding-wizard";

interface Props {
  form: BrandFormData;
  onChange: (updates: Partial<BrandFormData>) => void;
  onBack: () => void;
  onExtract: () => void;
  extracting: boolean;
}

export function ConnectSocialsStep({
  form,
  onChange,
  onBack,
  onExtract,
  extracting,
}: Props) {
  return (
    <Card>
      <CardHeader>
        <h2 className="text-lg font-semibold">Connect Socials & Extract</h2>
        <p className="text-sm text-slate-500">
          Link your social accounts and let AI extract your brand kit.
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">LinkedIn URL</label>
          <Input
            placeholder="https://linkedin.com/company/lumen-coffee"
            value={form.linkedin_url}
            onChange={(e) => onChange({ linkedin_url: e.target.value })}
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">X (Twitter) URL</label>
          <Input
            placeholder="https://x.com/lumencoffee"
            value={form.x_url}
            onChange={(e) => onChange({ x_url: e.target.value })}
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Instagram URL</label>
          <Input
            placeholder="https://instagram.com/lumencoffee"
            value={form.instagram_url}
            onChange={(e) => onChange({ instagram_url: e.target.value })}
          />
        </div>

        <div className="flex justify-between pt-4">
          <Button variant="outline" onClick={onBack} disabled={extracting}>
            Back
          </Button>
          <Button onClick={onExtract} disabled={extracting} size="lg">
            {extracting ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Extracting with AI...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 mr-2" />
                Extract Brand Kit with AI
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
