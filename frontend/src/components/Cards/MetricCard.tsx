import React from "react";
import clsx from "clsx";

interface Props {
  label: string;
  value: string;
  sub?: string;
  trend?: "up" | "down" | "neutral";
  tooltip?: string;
  size?: "sm" | "md";
}

export default function MetricCard({ label, value, sub, trend, tooltip, size = "md" }: Props) {
  return (
    <div
      className={clsx(
        "card flex flex-col gap-1",
        size === "sm" ? "p-4" : "p-5"
      )}
      title={tooltip}
    >
      <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</p>
      <p
        className={clsx(
          "font-bold",
          size === "sm" ? "text-xl" : "text-2xl",
          trend === "up" && "text-emerald-600",
          trend === "down" && "text-red-600",
          trend === "neutral" && "text-slate-900",
          !trend && "text-slate-900"
        )}
      >
        {value}
      </p>
      {sub && <p className="text-xs text-slate-400">{sub}</p>}
    </div>
  );
}
