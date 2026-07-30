import { Link } from "react-router-dom";

import { StatusBadge } from "@/components/peers/StatusBadge";
import { formatRelativeTime } from "@/lib/format";
import type { Peer } from "@/types/peer";

export function PeersTable({ peers }: { peers: Peer[] }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-surface-border">
      <table className="w-full min-w-[640px] text-sm">
        <thead className="bg-surface-raised text-left text-xs uppercase text-slate-500">
          <tr>
            <th className="px-4 py-2">Name</th>
            <th className="px-4 py-2">Status</th>
            <th className="px-4 py-2">Profile</th>
            <th className="px-4 py-2">Last online</th>
            <th className="px-4 py-2">Remote address</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-surface-border">
          {peers.map((peer) => (
            <tr key={peer.id} className="hover:bg-surface-raised/50">
              <td className="px-4 py-2">
                <Link to={`/peers/${peer.id}`} className="font-medium text-slate-100 hover:underline">
                  {peer.name}
                </Link>
                {peer.comment && <p className="text-xs text-slate-500">{peer.comment}</p>}
              </td>
              <td className="px-4 py-2">
                <StatusBadge online={peer.is_online} enabled={peer.enabled} />
              </td>
              <td className="px-4 py-2 text-slate-300">{peer.mikrotik_profile}</td>
              <td className="px-4 py-2 text-slate-400">{formatRelativeTime(peer.last_seen_online_at)}</td>
              <td className="px-4 py-2 text-slate-400">{peer.assigned_remote_address ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
