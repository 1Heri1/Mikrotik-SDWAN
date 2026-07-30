import { useState } from "react";

import { useTestTelegram } from "@/hooks/useSettings";
import type { NotificationSettings, NotificationSettingsUpdate } from "@/types/settings";

interface NotificationSettingsFormProps {
  current: NotificationSettings;
  values: NotificationSettingsUpdate;
  onChange: (values: NotificationSettingsUpdate) => void;
}

export function NotificationSettingsForm({ current, values, onChange }: NotificationSettingsFormProps) {
  const [testResult, setTestResult] = useState<string | null>(null);
  const testTelegram = useTestTelegram();

  function set<K extends keyof NotificationSettingsUpdate>(key: K, value: NotificationSettingsUpdate[K]) {
    onChange({ ...values, [key]: value });
  }

  async function handleTestTelegram() {
    setTestResult(null);
    const result = await testTelegram.mutateAsync({
      botToken: values.telegram_bot_token ?? undefined,
      chatId: values.telegram_chat_id ?? undefined,
    });
    setTestResult(result.message);
  }

  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <label className="flex items-center gap-2 text-sm text-slate-200">
          <input
            type="checkbox"
            checked={values.telegram_enabled}
            onChange={(e) => set("telegram_enabled", e.target.checked)}
          />
          Telegram notifications
        </label>
        {values.telegram_enabled && (
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div>
              <label className="block text-xs text-slate-400">Bot token</label>
              <input
                type="password"
                placeholder={current.telegram_token_configured ? "Unchanged" : "Bot token"}
                value={values.telegram_bot_token ?? ""}
                onChange={(e) => set("telegram_bot_token", e.target.value)}
                className="mt-1 w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400">Chat ID</label>
              <input
                value={values.telegram_chat_id ?? ""}
                onChange={(e) => set("telegram_chat_id", e.target.value)}
                className="mt-1 w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
              />
            </div>
            <div className="md:col-span-2">
              <button
                type="button"
                onClick={handleTestTelegram}
                disabled={testTelegram.isPending}
                className="rounded-md border border-surface-border px-3 py-1.5 text-xs text-slate-300 hover:bg-surface-raised disabled:opacity-50"
              >
                Send test message
              </button>
              {testResult && <span className="ml-3 text-xs text-slate-400">{testResult}</span>}
            </div>
          </div>
        )}
      </section>

      <section className="space-y-3">
        <label className="flex items-center gap-2 text-sm text-slate-200">
          <input type="checkbox" checked={values.smtp_enabled} onChange={(e) => set("smtp_enabled", e.target.checked)} />
          SMTP email notifications
        </label>
        {values.smtp_enabled && (
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div>
              <label className="block text-xs text-slate-400">SMTP host</label>
              <input
                value={values.smtp_host ?? ""}
                onChange={(e) => set("smtp_host", e.target.value)}
                className="mt-1 w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400">SMTP port</label>
              <input
                type="number"
                value={values.smtp_port ?? 587}
                onChange={(e) => set("smtp_port", Number(e.target.value))}
                className="mt-1 w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400">Username</label>
              <input
                value={values.smtp_username ?? ""}
                onChange={(e) => set("smtp_username", e.target.value)}
                className="mt-1 w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400">Password</label>
              <input
                type="password"
                placeholder={current.smtp_password_configured ? "Unchanged" : "Password"}
                value={values.smtp_password ?? ""}
                onChange={(e) => set("smtp_password", e.target.value)}
                className="mt-1 w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400">From address</label>
              <input
                value={values.smtp_from_address ?? ""}
                onChange={(e) => set("smtp_from_address", e.target.value)}
                className="mt-1 w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400">To address</label>
              <input
                value={values.smtp_to_address ?? ""}
                onChange={(e) => set("smtp_to_address", e.target.value)}
                className="mt-1 w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-slate-300 md:col-span-2">
              <input type="checkbox" checked={values.smtp_use_tls} onChange={(e) => set("smtp_use_tls", e.target.checked)} />
              Use STARTTLS
            </label>
          </div>
        )}
      </section>
    </div>
  );
}
