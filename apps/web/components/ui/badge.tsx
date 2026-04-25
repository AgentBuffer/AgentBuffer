import { cn } from "@/lib/utils";

interface BadgeProps {
  variant?:
    | "default"
    | "draft"
    | "proposed"
    | "rejected"
    | "approved"
    | "published"
    | "failed";
  className?: string;
  children: React.ReactNode;
}

export function Badge({ variant = "default", className, children }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide",
        {
          "bg-neutral-100 text-neutral-700": variant === "default",
          "bg-neutral-200 text-neutral-600": variant === "draft",
          "bg-blue-100 text-blue-700": variant === "proposed",
          "bg-red-100 text-red-700": variant === "rejected",
          "bg-green-100 text-green-700": variant === "approved",
          "bg-indigo-100 text-indigo-700": variant === "published",
          "bg-orange-100 text-orange-700": variant === "failed",
        },
        className
      )}
    >
      {children}
    </span>
  );
}
