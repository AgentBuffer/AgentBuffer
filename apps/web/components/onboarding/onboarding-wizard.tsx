"use client";

import { useState } from "react";
import { BrandBasicsStep } from "./brand-basics-step";
import { UploadAssetsStep } from "./upload-assets-step";
import { ConnectSocialsStep } from "./connect-socials-step";
import { BrandKitReview } from "./brand-kit-review";
import type { BrandKit } from "@/lib/types/models";

const STEPS = ["Brand Basics", "Upload Assets", "Connect & Extract"];

export interface BrandFormData {
  name: string;
  industry: string;
  tagline: string;
  target_audience: string;
  voice_description: string;
  pdfs: File[];
  video_urls: string[];
  linkedin_url: string;
  x_url: string;
  instagram_url: string;
}

const INITIAL_FORM: BrandFormData = {
  name: "",
  industry: "",
  tagline: "",
  target_audience: "",
  voice_description: "",
  pdfs: [],
  video_urls: [],
  linkedin_url: "",
  x_url: "",
  instagram_url: "",
};

export function OnboardingWizard() {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<BrandFormData>(INITIAL_FORM);
  const [extractedKit, setExtractedKit] = useState<BrandKit | null>(null);
  const [extracting, setExtracting] = useState(false);

  function updateForm(updates: Partial<BrandFormData>) {
    setForm((prev) => ({ ...prev, ...updates }));
  }

  async function handleExtract() {
    setExtracting(true);
    // TODO: Call server action to extract brand kit via Claude
    // For now, simulate extraction
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setExtractedKit({
      brand_id: "brand-new",
      org_id: "org-new",
      name: form.name,
      tagline: form.tagline,
      voice_description: form.voice_description,
      target_audience: form.target_audience,
      color_palette: ["#2C1810", "#D4A574", "#F5F0EB"],
      logo_url: null,
      sample_captions: [],
      industry: form.industry,
    });
    setExtracting(false);
  }

  if (extractedKit) {
    return <BrandKitReview brandKit={extractedKit} />;
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-4">
          {STEPS.map((label, i) => (
            <div key={label} className="flex items-center gap-2">
              <div
                className={`h-8 w-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  i <= step
                    ? "bg-neutral-900 text-white"
                    : "bg-neutral-200 text-neutral-500"
                }`}
              >
                {i + 1}
              </div>
              <span
                className={`text-sm ${
                  i <= step ? "text-neutral-900 font-medium" : "text-neutral-400"
                }`}
              >
                {label}
              </span>
              {i < STEPS.length - 1 && (
                <div className="w-8 h-px bg-neutral-300" />
              )}
            </div>
          ))}
        </div>
      </div>

      {step === 0 && (
        <BrandBasicsStep
          form={form}
          onChange={updateForm}
          onNext={() => setStep(1)}
        />
      )}
      {step === 1 && (
        <UploadAssetsStep
          form={form}
          onChange={updateForm}
          onBack={() => setStep(0)}
          onNext={() => setStep(2)}
        />
      )}
      {step === 2 && (
        <ConnectSocialsStep
          form={form}
          onChange={updateForm}
          onBack={() => setStep(1)}
          onExtract={handleExtract}
          extracting={extracting}
        />
      )}
    </div>
  );
}
