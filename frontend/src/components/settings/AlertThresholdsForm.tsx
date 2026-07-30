import type { NotificationSettingsUpdate } from "@/types/settings";

interface AlertThresholdsFormProps {
  values: NotificationSettingsUpdate;
  onChange: (values: NotificationSettingsUpdate) => void;
}

export function AlertThresholdsForm({ values, onChange }: AlertThresholdsFormProps) {
  function set<K extends keyof NotificationSettingsUpdate>(key: K, value: NotificationSettingsUpdate[K]) {
    onChange({ ...values, [key]: value });
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
      <div>
        <label className="block text-xs text-slate-400">Offline alert threshold (minutes)</label>
        <input
          type="number"
          min={1}
          value={values.offline_threshold_minutes}
          onChange={(e) => set("offline_threshold_minutes", Number(e.target.value))}
          className="mt-1 w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
        />
        <p className="mt-1 text-xs text-slate-500">Raise a peer_offline alert after a peer has been down this long.</p>
      </div>
      <div>
        <label className="block text-xs text-slate-400">Router re-alert cooldown (minutes)</label>
        <input
          type="number"
          min={1}
          value={values.router_unreachable_realert_minutes}
          onChange={(e) => set("router_unreachable_realert_minutes", Number(e.target.value))}
          className="mt-1 w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
        />
        <p className="mt-1 text-xs text-slate-500">Minimum time between repeat notifications for a persisting alert.</p>
      </div>
      <div>
        <label className="block text-xs text-slate-400">Snapshot retention (days)</label>
        <input
          type="number"
          min={1}
          value={values.snapshot_retention_days}
          onChange={(e) => set("snapshot_retention_days", Number(e.target.value))}
          className="mt-1 w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
        />
        <p className="mt-1 text-xs text-slate-500">Older peer status history is pruned nightly.</p>
      </div>
    </div>
  );
}
