import { useState, type FormEvent } from "react";

import { PasswordGeneratorField } from "@/components/peers/PasswordGeneratorField";
import type { Peer } from "@/types/peer";

export interface PeerFormValues {
  name: string;
  password: string;
  mikrotik_profile: string;
  service: "pptp" | "l2tp";
  assigned_local_address: string;
  assigned_remote_address: string;
  comment: string;
}

interface PeerFormProps {
  mode: "create" | "edit";
  initialPeer?: Peer;
  isSubmitting?: boolean;
  submitLabel?: string;
  onSubmit: (values: PeerFormValues) => void;
}

export function PeerForm({ mode, initialPeer, isSubmitting, submitLabel, onSubmit }: PeerFormProps) {
  const [values, setValues] = useState<PeerFormValues>({
    name: initialPeer?.name ?? "",
    password: "",
    mikrotik_profile: initialPeer?.mikrotik_profile ?? "",
    service: (initialPeer?.service as "pptp" | "l2tp") ?? "pptp",
    assigned_local_address: initialPeer?.assigned_local_address ?? "",
    assigned_remote_address: initialPeer?.assigned_remote_address ?? "",
    comment: initialPeer?.comment ?? "",
  });

  function set<K extends keyof PeerFormValues>(key: K, value: PeerFormValues[K]) {
    setValues((v) => ({ ...v, [key]: value }));
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSubmit(values);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {mode === "create" && (
        <div>
          <label className="block text-xs font-medium text-slate-400">Name (PPP secret name)</label>
          <input
            required
            value={values.name}
            onChange={(e) => set("name", e.target.value)}
            className="mt-1 w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
          />
        </div>
      )}

      <PasswordGeneratorField
        label={mode === "create" ? "Password" : "New password (leave blank to keep current)"}
        value={values.password}
        onChange={(v) => set("password", v)}
        placeholder={mode === "edit" ? "Unchanged" : undefined}
      />

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-slate-400">Profile</label>
          <input
            required
            value={values.mikrotik_profile}
            onChange={(e) => set("mikrotik_profile", e.target.value)}
            className="mt-1 w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
          />
        </div>
        {mode === "create" && (
          <div>
            <label className="block text-xs font-medium text-slate-400">Service</label>
            <select
              value={values.service}
              onChange={(e) => set("service", e.target.value as "pptp" | "l2tp")}
              className="mt-1 w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
            >
              <option value="pptp">PPTP</option>
              <option value="l2tp">L2TP</option>
            </select>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-slate-400">Local address</label>
          <input
            value={values.assigned_local_address}
            onChange={(e) => set("assigned_local_address", e.target.value)}
            className="mt-1 w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-slate-400">Remote address</label>
          <input
            value={values.assigned_remote_address}
            onChange={(e) => set("assigned_remote_address", e.target.value)}
            className="mt-1 w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
          />
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-slate-400">Comment</label>
        <input
          value={values.comment}
          onChange={(e) => set("comment", e.target.value)}
          className="mt-1 w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
        />
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="rounded-md bg-slate-100 px-4 py-2 text-sm font-medium text-slate-900 hover:bg-white disabled:opacity-50"
      >
        {isSubmitting ? "Saving…" : submitLabel ?? "Save"}
      </button>
    </form>
  );
}
