interface PeerFilterBarProps {
  search: string;
  onSearchChange: (value: string) => void;
  statusFilter: "online" | "offline" | "";
  onStatusFilterChange: (value: "online" | "offline" | "") => void;
}

export function PeerFilterBar({ search, onSearchChange, statusFilter, onStatusFilterChange }: PeerFilterBarProps) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <input
        type="text"
        placeholder="Search by name or comment…"
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
        className="w-64 rounded-md border border-surface-border bg-surface-raised px-3 py-1.5 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
      />
      <select
        value={statusFilter}
        onChange={(e) => onStatusFilterChange(e.target.value as "online" | "offline" | "")}
        className="rounded-md border border-surface-border bg-surface-raised px-3 py-1.5 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
      >
        <option value="">All statuses</option>
        <option value="online">Online</option>
        <option value="offline">Offline</option>
      </select>
    </div>
  );
}
