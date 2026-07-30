import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { PeerHistoryPoint } from "@/types/peer";

function formatTick(iso: string) {
  return new Date(iso).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

export function ConnectionHistoryChart({ points }: { points: PeerHistoryPoint[] }) {
  const data = points.map((p) => ({ ...p, online: p.is_online ? 1 : 0 }));

  return (
    <div className="h-48 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="peerOnlineGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#22c55e" stopOpacity={0.5} />
              <stop offset="95%" stopColor="#22c55e" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
          <XAxis dataKey="timestamp" tickFormatter={formatTick} stroke="#6b7280" tick={{ fontSize: 10 }} minTickGap={60} />
          <YAxis domain={[0, 1]} ticks={[0, 1]} tickFormatter={(v) => (v ? "Online" : "Offline")} stroke="#6b7280" tick={{ fontSize: 10 }} width={50} />
          <Tooltip
            contentStyle={{ background: "#111827", border: "1px solid #1f2937", fontSize: 12 }}
            labelFormatter={(iso: string) => new Date(iso).toLocaleString()}
            formatter={(value: number) => [value ? "Online" : "Offline", "Status"]}
          />
          <Area type="stepAfter" dataKey="online" stroke="#22c55e" fill="url(#peerOnlineGradient)" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
