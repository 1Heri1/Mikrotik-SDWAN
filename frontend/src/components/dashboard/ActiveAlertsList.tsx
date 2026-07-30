import { Link } from "react-router-dom";

import { SeverityPill } from "@/components/alerts/SeverityPill";
import { EmptyState } from "@/components/common/EmptyState";
import { useAcknowledgeAlert, useAlerts } from "@/hooks/useAlerts";
import { formatRelativeTime } from "@/lib/format";

export function ActiveAlertsList() {
  const { data: alerts, isLoading } = useAlerts("active");
  const acknowledge = useAcknowledgeAlert();

  if (isLoading) return <p className="text-sm text-slate-500">Loading alerts…</p>;
  if (!alerts || alerts.length === 0) {
    return <EmptyState title="No active alerts" description="Everything looks healthy right now." />;
  }

  return (
    <ul className="divide-y divide-surface-border">
      {alerts.map((alert) => (
        <li key={alert.id} className="flex items-start justify-between gap-3 py-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <SeverityPill severity={alert.severity} />
              {alert.peer_id && (
                <Link to={`/peers/${alert.peer_id}`} className="text-xs text-slate-400 hover:underline">
                  {alert.peer_name}
                </Link>
              )}
            </div>
            <p className="mt-1 truncate text-sm text-slate-200">{alert.message}</p>
            <p className="text-xs text-slate-500">{formatRelativeTime(alert.created_at)}</p>
          </div>
          {!alert.acknowledged_at && (
            <button
              type="button"
              onClick={() => acknowledge.mutate(alert.id)}
              disabled={acknowledge.isPending}
              className="shrink-0 rounded-md border border-surface-border px-2 py-1 text-xs text-slate-300 hover:bg-surface-raised disabled:opacity-50"
            >
              Acknowledge
            </button>
          )}
        </li>
      ))}
    </ul>
  );
}
