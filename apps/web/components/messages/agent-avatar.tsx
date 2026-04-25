import { cn } from "@/lib/utils";

const agentConfig: Record<
  string,
  { label: string; bgClass: string; textClass: string }
> = {
  strategist: {
    label: "S",
    bgClass: "bg-blue-100",
    textClass: "text-blue-700",
  },
  critic: {
    label: "C",
    bgClass: "bg-amber-100",
    textClass: "text-amber-700",
  },
  publisher: {
    label: "P",
    bgClass: "bg-green-100",
    textClass: "text-green-700",
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
        "h-8 w-8 rounded-full flex items-center justify-center text-sm font-bold shrink-0",
        config.bgClass,
        config.textClass
      )}
    >
      {config.label}
    </div>
  );
}
