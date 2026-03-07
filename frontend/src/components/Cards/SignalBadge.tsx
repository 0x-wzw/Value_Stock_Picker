import React from "react";
import { CheckCircle, AlertTriangle, XCircle, Info } from "lucide-react";

type Variant = "good" | "warn" | "bad" | "info";

interface Props {
  text: string;
  variant: Variant;
}

const CONFIG: Record<Variant, { cls: string; Icon: React.ElementType }> = {
  good: { cls: "bg-emerald-50 text-emerald-800 border-emerald-200", Icon: CheckCircle },
  warn: { cls: "bg-amber-50 text-amber-800 border-amber-200", Icon: AlertTriangle },
  bad:  { cls: "bg-red-50 text-red-800 border-red-200", Icon: XCircle },
  info: { cls: "bg-blue-50 text-blue-800 border-blue-200", Icon: Info },
};

export default function SignalBadge({ text, variant }: Props) {
  const { cls, Icon } = CONFIG[variant];
  return (
    <div className={`flex items-start gap-2 px-3 py-2 rounded-lg border text-sm ${cls}`}>
      <Icon className="w-4 h-4 mt-0.5 shrink-0" />
      <span>{text}</span>
    </div>
  );
}
