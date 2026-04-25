import { cn } from "@/lib/utils";
import { AgentAvatar } from "./agent-avatar";
import type { AgentEnvelope } from "@/lib/types/models";

interface Props {
  envelope: AgentEnvelope;
}

const agentBorderColors: Record<string, string> = {
  strategist: "border-l-blue-400",
  critic: "border-l-amber-400",
  publisher: "border-l-green-400",
};

function formatPayload(envelope: AgentEnvelope): string {
  const { payload, envelope_type } = envelope;

  switch (envelope_type) {
    case "slate_proposal":
      return `Generated weekly slate (${payload.slot_count ?? "?"} slots). Sending to Critic...`;
    case "rejection_notice":
      return `Reviewed slate. Slot${
        Array.isArray(payload.rejected_slots) && payload.rejected_slots.length > 1
          ? "s"
          : ""
      } ${
        Array.isArray(payload.rejected_slots)
          ? payload.rejected_slots.join(", ")
          : "?"
      } REJECTED. ${payload.reason ?? ""}`;
    case "slate_revision":
      return `Re-generating slot${
        Array.isArray(payload.revised_slots) && payload.revised_slots.length > 1
          ? "s"
          : ""
      } ${
        Array.isArray(payload.revised_slots)
          ? payload.revised_slots.join(", ")
          : "?"
      } with Critic feedback...`;
    case "full_approval":
      return `Full slate approved (${payload.approved_count ?? "?"} slots). Sending to Publisher...`;
    case "publish_result":
      return `Published ${payload.published ?? 0}, queued ${payload.queued ?? 0}, failed ${payload.failed ?? 0}.`;
    default:
      return JSON.stringify(payload);
  }
}

export function EnvelopeCard({ envelope }: Props) {
  const time = new Date(envelope.created_at).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div
      className={cn(
        "border-l-4 rounded-r-lg bg-white p-4 shadow-sm",
        agentBorderColors[envelope.from_agent] ?? "border-l-neutral-300"
      )}
    >
      <div className="flex items-start gap-3">
        <AgentAvatar agent={envelope.from_agent} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-semibold capitalize">
              {envelope.from_agent}
            </span>
            <span className="text-xs text-neutral-400">{time}</span>
          </div>
          <p className="text-sm text-neutral-700">
            {formatPayload(envelope)}
          </p>
          <p className="text-xs text-neutral-400 mt-1 font-mono">
            Envelope: {envelope.signature}
          </p>
        </div>
      </div>
    </div>
  );
}
