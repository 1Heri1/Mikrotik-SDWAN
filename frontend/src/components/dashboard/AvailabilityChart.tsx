import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { AvailabilityPoint } from "@/types/dashboard";

function formatTick(iso: string) {
  const date = new Date(iso);
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function AvailabilityChart({ data }: { data: AvailabilityPoint[] }) {
  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="onlineGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#22c55e" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#22c55e" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
          <XAxis
            dataKey="timestamp"
            tickFormatter={formatTick}
            stroke="#6b7280"
            tick={{ fontSize: 11 }}
            minTickGap={40}
          />
          <YAxis stroke="#6b7280" tick={{ fontSize: 11 }} width={32} allowDecimals={false} />
          <Tooltip
            contentStyle={{ background: "#111827", border: "1px solid #1f2937", fontSize: 12 }}
            labelFormatter={(iso: string) => new Date(iso).toLocaleString()}
          />
          <Area
            type="monotone"
            dataKey="online_count"
            name="Online peers"
            stroke="#22c55e"
            fill="url(#onlineGradient)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
