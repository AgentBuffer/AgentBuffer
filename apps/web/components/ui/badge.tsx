import { cn } from "@/lib/utils";

interface BadgeProps {
  variant?:
    | "default"
    | "draft"
    | "proposed"
    | "rejected"
    | "approved"
    | "published"
    | "failed"
    | "pending"
    | "skipped";
  className?: string;
  children: React.ReactNode;
}

export function Badge({ variant = "default", className, children }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider font-mono",
        {
          "bg-slate-100 text-slate-600": variant === "default",
          "bg-slate-100 text-slate-400": variant === "draft",
          "bg-cyan-50 text-cyan-700": variant === "proposed",
          "bg-red-50 text-red-500": variant === "rejected",
          "bg-green-50 text-lime-600": variant === "approved",
          "bg-violet-50 text-violet-600": variant === "published",
          "bg-orange-50 text-orange-500": variant === "failed",
          "bg-amber-50 text-amber-600": variant === "pending",
          "bg-slate-100 text-slate-400 line-through": variant === "skipped",
        },
        className
      )}
    >
      {children}
    </span>
  );
}
