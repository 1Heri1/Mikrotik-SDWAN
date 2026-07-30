import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { useAuth } from "@/auth/useAuth";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { DiffSummary } from "@/components/common/DiffSummary";
import { Spinner } from "@/components/common/Spinner";
import { ConnectionHistoryChart } from "@/components/peers/ConnectionHistoryChart";
import { PeerForm, type PeerFormValues } from "@/components/peers/PeerForm";
import { StatusBadge } from "@/components/peers/StatusBadge";
import {
  useDeletePeer,
  usePeer,
  usePeerHistory,
  usePreviewPeerUpdate,
  useResetPeerPassword,
  useRevealPeerPassword,
  useSetPeerEnabled,
  useUpdatePeer,
} from "@/hooks/usePeers";
import { formatDateTime } from "@/lib/format";
import type { DiffPreview, PeerUpdate } from "@/types/peer";

export function PeerDetailPage() {
  const { peerId } = useParams();
  const id = Number(peerId);
  const navigate = useNavigate();
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const [range, setRange] = useState<"24h" | "7d" | "30d">("24h");
  const { data: peer, isLoading } = usePeer(id);
  const { data: history } = usePeerHistory(id, range);

  const previewMutation = usePreviewPeerUpdate(id);
  const updateMutation = useUpdatePeer(id);
  const setEnabledMutation = useSetPeerEnabled(id);
  const resetPasswordMutation = useResetPeerPassword(id);
  const revealPasswordMutation = useRevealPeerPassword(id);
  const deleteMutation = useDeletePeer();

  const [pendingUpdate, setPendingUpdate] = useState<PeerUpdate | null>(null);
  const [diffPreview, setDiffPreview] = useState<DiffPreview | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [revealedPassword, setRevealedPassword] = useState<{ known: boolean; password: string | null } | null>(
    null
  );

  if (isLoading || !peer) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  async function handleFormSubmit(values: PeerFormValues) {
    const update: PeerUpdate = {
      mikrotik_profile: values.mikrotik_profile || undefined,
      assigned_local_address: values.assigned_local_address || null,
      assigned_remote_address: values.assigned_remote_address || null,
      comment: values.comment || null,
      password: values.password || undefined,
    };
    const preview = await previewMutation.mutateAsync(update);
    setPendingUpdate(update);
    setDiffPreview(preview);
  }

  async function confirmUpdate() {
    if (!pendingUpdate) return;
    await updateMutation.mutateAsync(pendingUpdate);
    setPendingUpdate(null);
    setDiffPreview(null);
  }

  async function handleDelete() {
    await deleteMutation.mutateAsync(id);
    navigate("/peers");
  }

  async function handleReveal() {
    const result = await revealPasswordMutation.mutateAsync();
    setRevealedPassword(result);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold text-slate-100">{peer.name}</h1>
          <div className="mt-1 flex items-center gap-2">
            <StatusBadge online={peer.is_online} enabled={peer.enabled} />
            <span className="text-xs text-slate-500">{peer.mikrotik_profile}</span>
          </div>
        </div>
        {isAdmin && (
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setEnabledMutation.mutate(!peer.enabled)}
              disabled={setEnabledMutation.isPending}
              className="rounded-md border border-surface-border px-3 py-1.5 text-sm text-slate-300 hover:bg-surface-raised disabled:opacity-50"
            >
              {peer.enabled ? "Disable" : "Enable"}
            </button>
            <button
              type="button"
              onClick={() => resetPasswordMutation.mutate(undefined)}
              disabled={resetPasswordMutation.isPending}
              className="rounded-md border border-surface-border px-3 py-1.5 text-sm text-slate-300 hover:bg-surface-raised disabled:opacity-50"
            >
              Reset password
            </button>
            <button
              type="button"
              onClick={handleReveal}
              disabled={revealPasswordMutation.isPending}
              className="rounded-md border border-surface-border px-3 py-1.5 text-sm text-slate-300 hover:bg-surface-raised disabled:opacity-50"
            >
              Reveal password
            </button>
            <button
              type="button"
              onClick={() => setShowDeleteConfirm(true)}
              className="rounded-md border border-danger px-3 py-1.5 text-sm text-danger hover:bg-danger-bg"
            >
              Delete
            </button>
          </div>
        )}
      </div>

      {revealedPassword && (
        <div className="rounded-md border border-warning bg-warning-bg px-3 py-2 text-sm text-warning">
          {revealedPassword.known ? (
            <>
              Current password: <code className="font-mono">{revealedPassword.password}</code>
            </>
          ) : (
            <>
              Password unknown — this peer was imported from the router and its real password was never
              available to the app. Use "Reset password" to set a new, known one.
            </>
          )}
          <button type="button" className="ml-3 underline" onClick={() => setRevealedPassword(null)}>
            Hide
          </button>
        </div>
      )}

      <div className="rounded-lg border border-surface-border bg-surface-raised p-4">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-sm font-medium text-slate-300">Connection history</h2>
          <div className="flex gap-1 text-xs">
            {(["24h", "7d", "30d"] as const).map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => setRange(r)}
                className={`rounded px-2 py-1 ${
                  range === r ? "bg-surface text-slate-100" : "text-slate-500 hover:text-slate-300"
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>
        {history && history.length > 0 ? (
          <ConnectionHistoryChart points={history} />
        ) : (
          <p className="py-10 text-center text-sm text-slate-500">No history data for this range yet.</p>
        )}
      </div>

      <dl className="grid grid-cols-2 gap-4 rounded-lg border border-surface-border bg-surface-raised p-4 text-sm md:grid-cols-4">
        <div>
          <dt className="text-xs text-slate-500">Local address</dt>
          <dd className="text-slate-200">{peer.assigned_local_address ?? "—"}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Remote address</dt>
          <dd className="text-slate-200">{peer.assigned_remote_address ?? "—"}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Last online</dt>
          <dd className="text-slate-200">{formatDateTime(peer.last_seen_online_at)}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Comment</dt>
          <dd className="text-slate-200">{peer.comment ?? "—"}</dd>
        </div>
      </dl>

      {isAdmin && (
        <div className="max-w-xl rounded-lg border border-surface-border bg-surface-raised p-4">
          <h2 className="mb-3 text-sm font-medium text-slate-300">Edit peer</h2>
          <PeerForm mode="edit" initialPeer={peer} onSubmit={handleFormSubmit} submitLabel="Review changes" />
        </div>
      )}

      <ConfirmDialog
        open={!!diffPreview}
        title="Confirm peer changes"
        confirmLabel="Apply changes"
        isSubmitting={updateMutation.isPending}
        onConfirm={confirmUpdate}
        onCancel={() => {
          setPendingUpdate(null);
          setDiffPreview(null);
        }}
      >
        {diffPreview && <DiffSummary diff={diffPreview} />}
      </ConfirmDialog>

      <ConfirmDialog
        open={showDeleteConfirm}
        title={`Delete peer "${peer.name}"?`}
        confirmLabel="Delete"
        danger
        isSubmitting={deleteMutation.isPending}
        onConfirm={handleDelete}
        onCancel={() => setShowDeleteConfirm(false)}
      >
        This removes the PPP secret from the router and deletes all local history for this peer. This cannot be
        undone.
      </ConfirmDialog>
    </div>
  );
}
