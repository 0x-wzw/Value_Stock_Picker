import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface DataPoint {
  period: string;
  value: number | null;
}

interface Props {
  data: DataPoint[];
  label: string;
  formatter?: (v: number) => string;
  color?: string;
}

const defaultFormatter = (v: number) =>
  Math.abs(v) >= 1e9
    ? `$${(v / 1e9).toFixed(1)}B`
    : Math.abs(v) >= 1e6
    ? `$${(v / 1e6).toFixed(0)}M`
    : `${v.toFixed(0)}`;

export default function BarMetricChart({
  data,
  label,
  formatter = defaultFormatter,
  color = "#3b82f6",
}: Props) {
  if (!data.length) {
    return (
      <div className="h-48 flex items-center justify-center text-slate-400 text-sm">
        No data
      </div>
    );
  }

  return (
    <div>
      <p className="text-xs font-medium text-slate-500 mb-2 uppercase tracking-wide">{label}</p>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
          <XAxis
            dataKey="period"
            tick={{ fontSize: 10, fill: "#94a3b8" }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            tick={{ fontSize: 10, fill: "#94a3b8" }}
            tickLine={false}
            axisLine={false}
            tickFormatter={formatter}
            width={56}
          />
          <Tooltip
            formatter={(v: number) => [formatter(v), label]}
            contentStyle={{
              fontSize: 12,
              borderRadius: 8,
              border: "1px solid #e2e8f0",
            }}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {data.map((entry, i) => (
              <Cell
                key={i}
                fill={(entry.value ?? 0) >= 0 ? color : "#ef4444"}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
