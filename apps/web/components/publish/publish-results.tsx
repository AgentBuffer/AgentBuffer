import { Card, CardContent } from "@/components/ui/card";
import { Check, AlertCircle } from "lucide-react";
import type { PublishResult } from "@/lib/types/models";

interface Props {
  results: PublishResult[];
}

const platformLabels: Record<string, string> = {
  linkedin: "LinkedIn",
  x: "X",
  instagram: "IG",
};

export function PublishResults({ results }: Props) {
  if (results.length === 0) return null;

  return (
    <Card>
      <CardContent className="py-3 space-y-2">
        <h3 className="text-xs font-semibold text-slate-700 font-mono uppercase tracking-wider">Published</h3>
        {results.map((r) => (
          <div
            key={`${r.slot_id}-${r.platform}`}
            className="flex items-center gap-2 text-sm"
          >
            {r.success ? (
              <Check className="h-4 w-4 text-green-600 shrink-0" />
            ) : (
              <AlertCircle className="h-4 w-4 text-red-600 shrink-0" />
            )}
            <span>
              Slot &rarr; {platformLabels[r.platform] ?? r.platform}
            </span>
            {r.success && r.permalink && (
              <a
                href={r.permalink}
                target="_blank"
                rel="noopener noreferrer"
                className="text-cyan-600 hover:underline ml-auto text-xs font-mono"
              >
                permalink
              </a>
            )}
            {!r.success && r.error && (
              <span className="text-red-600 ml-auto">{r.error}</span>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
