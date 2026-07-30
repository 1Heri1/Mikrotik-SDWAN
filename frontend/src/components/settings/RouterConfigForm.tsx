import { useState } from "react";

import { useTestRouterConnection, useUpdateRouterConfig } from "@/hooks/useSettings";
import type { RouterConfig, RouterConfigUpdate } from "@/types/settings";

const DEFAULTS: RouterConfigUpdate = {
  host: "",
  port: 8728,
  api_user: "",
  api_secret: "",
  protocol: "librouteros",
  verify_ssl: true,
  backup_before_bulk_ops: false,
};

export function RouterConfigForm({ current }: { current: RouterConfig | null }) {
  const [values, setValues] = useState<RouterConfigUpdate>(
    current
      ? {
          host: current.host,
          port: current.port,
          api_user: current.api_user,
          api_secret: "",
          protocol: current.protocol,
          verify_ssl: current.verify_ssl,
          backup_before_bulk_ops: current.backup_before_bulk_ops,
        }
      : DEFAULTS
  );
  const [testResult, setTestResult] = useState<string | null>(null);

  const updateMutation = useUpdateRouterConfig();
  const testMutation = useTestRouterConnection();

  function set<K extends keyof RouterConfigUpdate>(key: K, value: RouterConfigUpdate[K]) {
    setValues((v) => ({ ...v, [key]: value }));
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    await updateMutation.mutateAsync(values);
    setValues((v) => ({ ...v, api_secret: "" }));
  }

  async function handleTest() {
    setTestResult(null);
    const result = await testMutation.mutateAsync();
    setTestResult(result.message);
  }

  return (
    <form onSubmit={handleSave} className="space-y-4">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div>
          <label className="block text-xs text-slate-400">Protocol</label>
          <select
            value={values.protocol}
            onChange={(e) => set("protocol", e.target.value as RouterConfigUpdate["protocol"])}
            className="mt-1 w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
          >
            <option value="librouteros">librouteros (RouterOS &lt; 7, binary API)</option>
            <option value="rest">REST API (RouterOS 7.x, HTTPS)</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-400">Host</label>
          <input
            required
            value={values.host}
            onChange={(e) => set("host", e.target.value)}
            className="mt-1 w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-xs text-slate-400">Port</label>
          <input
            required
            type="number"
            value={values.port}
            onChange={(e) => set("port", Number(e.target.value))}
            className="mt-1 w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-xs text-slate-400">API user</label>
          <input
            required
            value={values.api_user}
            onChange={(e) => set("api_user", e.target.value)}
            className="mt-1 w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-xs text-slate-400">Password / API secret</label>
          <input
            type="password"
            placeholder={current ? "Unchanged" : "Required"}
            value={values.api_secret ?? ""}
            onChange={(e) => set("api_secret", e.target.value)}
            className="mt-1 w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
          />
        </div>
      </div>

      <div className="flex flex-wrap gap-6">
        <label className="flex items-center gap-2 text-sm text-slate-300">
          <input type="checkbox" checked={values.verify_ssl} onChange={(e) => set("verify_ssl", e.target.checked)} />
          Verify SSL certificate (REST only)
        </label>
        <label className="flex items-center gap-2 text-sm text-slate-300">
          <input
            type="checkbox"
            checked={values.backup_before_bulk_ops}
            onChange={(e) => set("backup_before_bulk_ops", e.target.checked)}
          />
          Take a router backup before bulk operations
        </label>
      </div>

      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={updateMutation.isPending}
          className="rounded-md bg-slate-100 px-4 py-2 text-sm font-medium text-slate-900 hover:bg-white disabled:opacity-50"
        >
          {updateMutation.isPending ? "Saving…" : "Save connection"}
        </button>
        <button
          type="button"
          onClick={handleTest}
          disabled={testMutation.isPending || !current}
          className="rounded-md border border-surface-border px-4 py-2 text-sm text-slate-300 hover:bg-surface-raised disabled:opacity-50"
        >
          Test connection
        </button>
        {testResult && <span className="text-xs text-slate-400">{testResult}</span>}
      </div>
    </form>
  );
}
