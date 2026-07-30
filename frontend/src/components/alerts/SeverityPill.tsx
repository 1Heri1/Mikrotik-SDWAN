import clsx from "clsx";

import type { AlertSeverity } from "@/types/alert";

const STYLES: Record<AlertSeverity, string> = {
  info: "bg-surface-raised text-slate-300",
  warning: "bg-warning-bg text-warning",
  critical: "bg-danger-bg text-danger",
};

export function SeverityPill({ severity }: { severity: AlertSeverity }) {
  return (
    <span className={clsx("rounded-full px-2 py-0.5 text-xs font-medium uppercase", STYLES[severity])}>
      {severity}
    </span>
  );
}
