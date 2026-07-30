import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { PeerForm, type PeerFormValues } from "@/components/peers/PeerForm";
import { useCreatePeer } from "@/hooks/usePeers";

export function PeerAddPage() {
  const navigate = useNavigate();
  const createPeer = useCreatePeer();
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(values: PeerFormValues) {
    setError(null);
    try {
      const peer = await createPeer.mutateAsync({
        name: values.name,
        password: values.password,
        mikrotik_profile: values.mikrotik_profile,
        service: values.service,
        assigned_local_address: values.assigned_local_address || null,
        assigned_remote_address: values.assigned_remote_address || null,
        comment: values.comment || null,
      });
      navigate(`/peers/${peer.id}`);
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Failed to create peer.";
      setError(message);
    }
  }

  return (
    <div className="max-w-xl space-y-4">
      <h1 className="text-lg font-semibold text-slate-100">Add peer</h1>
      <div className="rounded-lg border border-surface-border bg-surface-raised p-4">
        {error && <p className="mb-3 text-sm text-danger">{error}</p>}
        <PeerForm mode="create" onSubmit={handleSubmit} isSubmitting={createPeer.isPending} submitLabel="Create peer" />
      </div>
    </div>
  );
}
