import clsx from "clsx";
import type { ReactNode } from "react";

interface SummaryCardProps {
  label: string;
  value: ReactNode;
  tone?: "default" | "ok" | "danger" | "warning";
}

const TONE_CLASSES: Record<NonNullable<SummaryCardProps["tone"]>, string> = {
  default: "text-slate-100",
  ok: "text-ok",
  danger: "text-danger",
  warning: "text-warning",
};

export function SummaryCard({ label, value, tone = "default" }: SummaryCardProps) {
  return (
    <div className="rounded-lg border border-surface-border bg-surface-raised p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className={clsx("mt-1 text-2xl font-semibold", TONE_CLASSES[tone])}>{value}</p>
    </div>
  );
}
