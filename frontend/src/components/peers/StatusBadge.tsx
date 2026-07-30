import clsx from "clsx";

export function StatusBadge({ online, enabled = true }: { online: boolean; enabled?: boolean }) {
  if (!enabled) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-muted-bg px-2 py-0.5 text-xs font-medium text-muted">
        <span className="h-1.5 w-1.5 rounded-full bg-muted" />
        Disabled
      </span>
    );
  }

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium",
        online ? "bg-ok-bg text-ok" : "bg-danger-bg text-danger"
      )}
    >
      <span className={clsx("h-1.5 w-1.5 rounded-full", online ? "bg-ok" : "bg-danger")} />
      {online ? "Online" : "Offline"}
    </span>
  );
}
