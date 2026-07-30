import { useEffect, useState } from "react";

import { Spinner } from "@/components/common/Spinner";
import { AlertThresholdsForm } from "@/components/settings/AlertThresholdsForm";
import { NotificationSettingsForm } from "@/components/settings/NotificationSettingsForm";
import { RouterConfigForm } from "@/components/settings/RouterConfigForm";
import { UserManagementTable } from "@/components/settings/UserManagementTable";
import { useNotificationSettings, useRouterConfig, useUpdateNotificationSettings } from "@/hooks/useSettings";
import type { NotificationSettingsUpdate } from "@/types/settings";

type Tab = "router" | "notifications" | "users";

function toUpdate(current: ReturnType<typeof useNotificationSettings>["data"]): NotificationSettingsUpdate | null {
  if (!current) return null;
  return {
    telegram_enabled: current.telegram_enabled,
    telegram_chat_id: current.telegram_chat_id,
    smtp_enabled: current.smtp_enabled,
    smtp_host: current.smtp_host,
    smtp_port: current.smtp_port,
    smtp_username: current.smtp_username,
    smtp_from_address: current.smtp_from_address,
    smtp_to_address: current.smtp_to_address,
    smtp_use_tls: current.smtp_use_tls,
    offline_threshold_minutes: current.offline_threshold_minutes,
    router_unreachable_realert_minutes: current.router_unreachable_realert_minutes,
    snapshot_retention_days: current.snapshot_retention_days,
  };
}

function NotificationsTab() {
  const { data: current, isLoading } = useNotificationSettings();
  const updateMutation = useUpdateNotificationSettings();
  const [values, setValues] = useState<NotificationSettingsUpdate | null>(null);

  useEffect(() => {
    if (current && !values) setValues(toUpdate(current));
  }, [current, values]);

  if (isLoading || !current || !values) {
    return (
      <div className="flex h-40 items-center justify-center">
        <Spinner />
      </div>
    );
  }

  async function handleSave() {
    if (values) await updateMutation.mutateAsync(values);
  }

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-surface-border bg-surface-raised p-4">
        <h2 className="mb-3 text-sm font-medium text-slate-300">Notification channels</h2>
        <NotificationSettingsForm current={current} values={values} onChange={setValues} />
      </div>
      <div className="rounded-lg border border-surface-border bg-surface-raised p-4">
        <h2 className="mb-3 text-sm font-medium text-slate-300">Alert thresholds</h2>
        <AlertThresholdsForm values={values} onChange={setValues} />
      </div>
      <button
        type="button"
        onClick={handleSave}
        disabled={updateMutation.isPending}
        className="rounded-md bg-slate-100 px-4 py-2 text-sm font-medium text-slate-900 hover:bg-white disabled:opacity-50"
      >
        {updateMutation.isPending ? "Saving…" : "Save notification settings"}
      </button>
    </div>
  );
}

export function SettingsPage() {
  const [tab, setTab] = useState<Tab>("router");
  const { data: routerConfig, isLoading: routerLoading } = useRouterConfig();

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-semibold text-slate-100">Settings</h1>

      <div className="flex gap-1 border-b border-surface-border text-sm">
        {(
          [
            { id: "router", label: "Router connection" },
            { id: "notifications", label: "Notifications & alerts" },
            { id: "users", label: "Users" },
          ] as const
        ).map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`px-3 py-2 ${
              tab === t.id ? "border-b-2 border-slate-100 text-slate-100" : "text-slate-500 hover:text-slate-300"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "router" &&
        (routerLoading ? (
          <div className="flex h-40 items-center justify-center">
            <Spinner />
          </div>
        ) : (
          <div className="max-w-2xl rounded-lg border border-surface-border bg-surface-raised p-4">
            <RouterConfigForm current={routerConfig ?? null} />
          </div>
        ))}

      {tab === "notifications" && <NotificationsTab />}

      {tab === "users" && (
        <div>
          <UserManagementTable />
        </div>
      )}
    </div>
  );
}
