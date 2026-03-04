import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface PricePoint {
  date: string;
  close: number;
}

interface Props {
  data: PricePoint[];
  ticker: string;
}

const CustomTooltip = ({ active, payload, label }: {
  active?: boolean;
  payload?: Array<{ value: number }>;
  label?: string;
}) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-slate-200 rounded-lg px-3 py-2 shadow-md">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-sm font-bold text-slate-900">${payload[0].value.toFixed(2)}</p>
    </div>
  );
};

export default function PriceChart({ data, ticker }: Props) {
  if (!data.length) {
    return (
      <div className="h-48 flex items-center justify-center text-slate-400 text-sm">
        No price data available
      </div>
    );
  }

  const first = data[0].close;
  const last = data[data.length - 1].close;
  const positive = last >= first;
  const color = positive ? "#059669" : "#dc2626";
  const fillId = `fill-${ticker}`;

  // Thin out data for display (max 120 points)
  const step = Math.max(1, Math.floor(data.length / 120));
  const display = data.filter((_, i) => i % step === 0 || i === data.length - 1);

  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={display} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id={fillId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.15} />
            <stop offset="95%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11, fill: "#94a3b8" }}
          tickLine={false}
          axisLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{ fontSize: 11, fill: "#94a3b8" }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `$${v}`}
          domain={["auto", "auto"]}
          width={60}
        />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="close"
          stroke={color}
          strokeWidth={2}
          fill={`url(#${fillId})`}
          dot={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
