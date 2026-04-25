import { cn } from "@/lib/utils";

const agentConfig: Record<
  string,
  { label: string; bgClass: string; textClass: string }
> = {
  strategist: {
    label: "S",
    bgClass: "bg-cyan-500",
    textClass: "text-white",
  },
  critic: {
    label: "C",
    bgClass: "bg-orange-400",
    textClass: "text-white",
  },
  publisher: {
    label: "P",
    bgClass: "bg-lime-400",
    textClass: "text-slate-900",
  },
};

interface Props {
  agent: string;
}

export function AgentAvatar({ agent }: Props) {
  const config = agentConfig[agent] ?? {
    label: "?",
    bgClass: "bg-neutral-100",
    textClass: "text-neutral-700",
  };

  return (
    <div
      className={cn(
        "h-7 w-7 rounded flex items-center justify-center text-xs font-bold shrink-0",
        config.bgClass,
        config.textClass
      )}
    >
      {config.label}
    </div>
  );
}
