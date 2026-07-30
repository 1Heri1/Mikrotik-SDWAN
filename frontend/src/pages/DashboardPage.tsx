import { ActiveAlertsList } from "@/components/dashboard/ActiveAlertsList";
import { AvailabilityChart } from "@/components/dashboard/AvailabilityChart";
import { ConcentratorHealthCard } from "@/components/dashboard/ConcentratorHealthCard";
import { SummaryCard } from "@/components/dashboard/SummaryCard";
import { Spinner } from "@/components/common/Spinner";
import { useAvailability, useDashboardSummary } from "@/hooks/useDashboard";

export function DashboardPage() {
  const { data: summary, isLoading } = useDashboardSummary();
  const { data: availability } = useAvailability("24h");

  if (isLoading || !summary) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-lg font-semibold text-slate-100">Dashboard</h1>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <SummaryCard label="Online peers" value={summary.online_count} tone="ok" />
        <SummaryCard label="Offline peers" value={summary.offline_count} tone={summary.offline_count > 0 ? "danger" : "default"} />
        <SummaryCard
          label="Active alerts"
          value={summary.active_alert_count}
          tone={summary.active_alert_count > 0 ? "warning" : "default"}
        />
        <SummaryCard label="Total peers" value={summary.total_peers} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="rounded-lg border border-surface-border bg-surface-raised p-4 lg:col-span-2">
          <h2 className="mb-2 text-sm font-medium text-slate-300">Availability (last 24h)</h2>
          {availability && availability.length > 0 ? (
            <AvailabilityChart data={availability} />
          ) : (
            <p className="py-16 text-center text-sm text-slate-500">Not enough data yet.</p>
          )}
        </div>
        <ConcentratorHealthCard health={summary.concentrator} />
      </div>

      <div className="rounded-lg border border-surface-border bg-surface-raised p-4">
        <h2 className="mb-2 text-sm font-medium text-slate-300">Active alerts</h2>
        <ActiveAlertsList />
      </div>
    </div>
  );
}
