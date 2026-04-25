"use client";

import { useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Upload, X } from "lucide-react";
import type { BrandFormData } from "./onboarding-wizard";

interface Props {
  form: BrandFormData;
  onChange: (updates: Partial<BrandFormData>) => void;
  onBack: () => void;
  onNext: () => void;
}

export function UploadAssetsStep({ form, onChange, onBack, onNext }: Props) {
  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const files = Array.from(e.dataTransfer.files).filter(
        (f) => f.type === "application/pdf"
      );
      onChange({ pdfs: [...form.pdfs, ...files] });
    },
    [form.pdfs, onChange]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files ?? []);
      onChange({ pdfs: [...form.pdfs, ...files] });
    },
    [form.pdfs, onChange]
  );

  function removePdf(index: number) {
    onChange({ pdfs: form.pdfs.filter((_, i) => i !== index) });
  }

  return (
    <Card>
      <CardHeader>
        <h2 className="text-lg font-semibold">Upload Assets</h2>
        <p className="text-sm text-neutral-500">
          Upload brand guidelines, marketing PDFs, or past content for AI extraction.
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          className="border-2 border-dashed border-neutral-300 rounded-lg p-8 text-center hover:border-neutral-400 transition-colors cursor-pointer"
        >
          <input
            type="file"
            accept=".pdf"
            multiple
            onChange={handleFileSelect}
            className="hidden"
            id="pdf-upload"
          />
          <label htmlFor="pdf-upload" className="cursor-pointer">
            <Upload className="h-8 w-8 text-neutral-400 mx-auto mb-2" />
            <p className="text-sm text-neutral-600 font-medium">
              Drop PDFs here or click to upload
            </p>
            <p className="text-xs text-neutral-400 mt-1">
              Brand guidelines, marketing decks, content calendars
            </p>
          </label>
        </div>

        {form.pdfs.length > 0 && (
          <div className="space-y-2">
            {form.pdfs.map((file, i) => (
              <div
                key={`${file.name}-${i}`}
                className="flex items-center justify-between bg-neutral-50 rounded-lg px-3 py-2"
              >
                <span className="text-sm text-neutral-700 truncate">
                  {file.name}
                </span>
                <button
                  onClick={() => removePdf(i)}
                  className="text-neutral-400 hover:text-red-500"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="space-y-2">
          <label className="text-sm font-medium">
            Past video URLs (optional)
          </label>
          <Input
            placeholder="https://youtube.com/watch?v=..."
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                const val = (e.target as HTMLInputElement).value.trim();
                if (val) {
                  onChange({ video_urls: [...form.video_urls, val] });
                  (e.target as HTMLInputElement).value = "";
                }
              }
            }}
          />
          {form.video_urls.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {form.video_urls.map((url, i) => (
                <span
                  key={`${url}-${i}`}
                  className="inline-flex items-center gap-1 bg-neutral-100 text-xs rounded-full px-2.5 py-1"
                >
                  {url.substring(0, 40)}...
                  <button
                    onClick={() =>
                      onChange({
                        video_urls: form.video_urls.filter((_, j) => j !== i),
                      })
                    }
                  >
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="flex justify-between pt-2">
          <Button variant="outline" onClick={onBack}>
            Back
          </Button>
          <Button onClick={onNext}>Next</Button>
        </div>
      </CardContent>
    </Card>
  );
}
