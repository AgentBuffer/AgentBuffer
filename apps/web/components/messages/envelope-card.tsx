import { cn } from "@/lib/utils";
import { AgentAvatar } from "./agent-avatar";
import type { AgentEnvelope } from "@/lib/types/models";

interface Props {
  envelope: AgentEnvelope;
}

const agentBorderColors: Record<string, string> = {
  strategist: "border-l-cyan-400",
  critic: "border-l-orange-400",
  publisher: "border-l-lime-400",
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
        "border-l-[3px] rounded-r-md bg-white p-3 shadow-[0_1px_2px_rgba(15,23,42,0.04)]",
        agentBorderColors[envelope.from_agent] ?? "border-l-slate-300"
      )}
    >
      <div className="flex items-start gap-3">
        <AgentAvatar agent={envelope.from_agent} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold uppercase font-mono tracking-wide">
              {envelope.from_agent}
            </span>
            <span className="text-[10px] text-slate-400 font-mono">{time}</span>
          </div>
          <p className="text-sm text-slate-600">
            {formatPayload(envelope)}
          </p>
          <span className="inline-block text-[10px] text-slate-400 font-mono mt-1.5 bg-slate-50 px-2 py-0.5 rounded">
            {envelope.signature}
          </span>
        </div>
      </div>
    </div>
  );
}
