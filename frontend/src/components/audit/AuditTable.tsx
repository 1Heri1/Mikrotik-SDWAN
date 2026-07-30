import { Fragment, useState } from "react";
import { Link } from "react-router-dom";

import { DiffView } from "@/components/audit/DiffView";
import { formatDateTime } from "@/lib/format";
import type { AuditLogEntry } from "@/types/audit";

export function AuditTable({ entries }: { entries: AuditLogEntry[] }) {
  const [expandedId, setExpandedId] = useState<number | null>(null);

  return (
    <div className="overflow-x-auto rounded-lg border border-surface-border">
      <table className="w-full min-w-[720px] text-sm">
        <thead className="bg-surface-raised text-left text-xs uppercase text-slate-500">
          <tr>
            <th className="px-4 py-2">Time</th>
            <th className="px-4 py-2">User</th>
            <th className="px-4 py-2">Action</th>
            <th className="px-4 py-2">Peer</th>
            <th className="px-4 py-2">IP</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-surface-border">
          {entries.map((entry) => (
            <Fragment key={entry.id}>
              <tr
                className="cursor-pointer hover:bg-surface-raised/50"
                onClick={() => setExpandedId(expandedId === entry.id ? null : entry.id)}
              >
                <td className="px-4 py-2 text-slate-400">{formatDateTime(entry.timestamp)}</td>
                <td className="px-4 py-2 text-slate-200">{entry.username ?? "system"}</td>
                <td className="px-4 py-2 text-slate-200">{entry.action}</td>
                <td className="px-4 py-2 text-slate-400">
                  {entry.target_peer_id ? (
                    <Link
                      to={`/peers/${entry.target_peer_id}`}
                      className="hover:underline"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {entry.peer_name ?? entry.target_peer_id}
                    </Link>
                  ) : (
                    "—"
                  )}
                </td>
                <td className="px-4 py-2 text-slate-500">{entry.ip_address ?? "—"}</td>
              </tr>
              {expandedId === entry.id && (
                <tr>
                  <td colSpan={5} className="bg-surface px-4 py-3">
                    <DiffView before={entry.before_json} after={entry.after_json} />
                  </td>
                </tr>
              )}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}
