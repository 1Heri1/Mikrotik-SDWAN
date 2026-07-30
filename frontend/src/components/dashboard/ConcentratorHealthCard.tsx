import clsx from "clsx";

import { formatBytes, formatDuration, formatRelativeTime } from "@/lib/format";
import type { ConcentratorHealth } from "@/types/dashboard";

function LoadBar({ label, percent }: { label: string; percent: number | null }) {
  const value = percent ?? 0;
  const tone = value > 85 ? "bg-danger" : value > 60 ? "bg-warning" : "bg-ok";
  return (
    <div>
      <div className="flex justify-between text-xs text-slate-400">
        <span>{label}</span>
        <span>{percent === null ? "—" : `${percent}%`}</span>
      </div>
      <div className="mt-1 h-2 rounded-full bg-surface">
        <div className={clsx("h-2 rounded-full", tone)} style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
    </div>
  );
}

export function ConcentratorHealthCard({ health }: { health: ConcentratorHealth }) {
  const memPercent =
    health.free_memory_bytes != null && health.total_memory_bytes
      ? Math.round(((health.total_memory_bytes - health.free_memory_bytes) / health.total_memory_bytes) * 100)
      : null;

  return (
    <div className="rounded-lg border border-surface-border bg-surface-raised p-4">
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-wide text-slate-500">Concentrator</p>
        <span
          className={clsx(
            "rounded-full px-2 py-0.5 text-xs font-medium",
            health.reachable ? "bg-ok-bg text-ok" : "bg-danger-bg text-danger"
          )}
        >
          {health.reachable ? "Reachable" : "Unreachable"}
        </span>
      </div>

      {health.reachable ? (
        <div className="mt-3 space-y-3">
          <LoadBar label="CPU load" percent={health.cpu_load_percent} />
          <LoadBar label="Memory used" percent={memPercent} />
          <dl className="grid grid-cols-2 gap-2 text-xs text-slate-400">
            <div>
              <dt className="text-slate-500">Version</dt>
              <dd className="text-slate-200">{health.version ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Uptime</dt>
              <dd className="text-slate-200">{formatDuration(health.uptime_seconds)}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Free memory</dt>
              <dd className="text-slate-200">{formatBytes(health.free_memory_bytes)}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Last poll</dt>
              <dd className="text-slate-200">{formatRelativeTime(health.last_poll_at)}</dd>
            </div>
          </dl>
        </div>
      ) : (
        <p className="mt-3 text-sm text-danger">{health.last_error ?? "The concentrator could not be reached."}</p>
      )}
    </div>
  );
}
