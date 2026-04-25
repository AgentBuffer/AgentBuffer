import { Badge } from "@/components/ui/badge";
import type { ContentSlot } from "@/lib/types/models";

interface Props {
  status: ContentSlot["status"];
}

export function StatusBadge({ status }: Props) {
  return <Badge variant={status}>{status}</Badge>;
}
