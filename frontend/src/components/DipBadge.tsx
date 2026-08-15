import { Badge } from "@/components/ui/badge";
import type { DipLevel } from "@/lib/api";

const VARIANT: Record<DipLevel, "success" | "warning" | "destructive"> = {
  GREEN: "success",
  AMBER: "warning",
  RED: "destructive",
};

export default function DipBadge({ level }: { level: DipLevel }) {
  return <Badge variant={VARIANT[level]}>{level}</Badge>;
}
