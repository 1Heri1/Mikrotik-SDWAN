import { useState } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "@/auth/useAuth";
import { EmptyState } from "@/components/common/EmptyState";
import { Spinner } from "@/components/common/Spinner";
import { PeerFilterBar } from "@/components/peers/PeerFilterBar";
import { PeersTable } from "@/components/peers/PeersTable";
import { useImportPeers, usePeersList } from "@/hooks/usePeers";

const PAGE_SIZE = 25;

export function PeersListPage() {
  const { user } = useAuth();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"online" | "offline" | "">("");
  const [page, setPage] = useState(1);
  const [importMessage, setImportMessage] = useState<string | null>(null);
  const [importError, setImportError] = useState<string | null>(null);

  const { data, isLoading } = usePeersList({
    search: search || undefined,
    status_filter: statusFilter || undefined,
    page,
    page_size: PAGE_SIZE,
  });
  const importMutation = useImportPeers();

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  async function handleImport() {
    setImportMessage(null);
    setImportError(null);
    try {
      const result = await importMutation.mutateAsync();
      let message =
        `Imported ${result.imported_count} peer${result.imported_count === 1 ? "" : "s"} from the router` +
        (result.skipped_count > 0 ? ` (${result.skipped_count} already tracked or duplicate, skipped)` : "") +
        ".";
      if (result.duplicate_names.length > 0) {
        message +=
          ` Warning: the router has duplicate secret names (only the first of each was imported): ` +
          result.duplicate_names.join(", ") +
          ". Rename the duplicates on the router if you want each tracked separately.";
      }
      setImportMessage(message);
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Import failed. Check that the router connection is configured and reachable.";
      setImportError(message);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-lg font-semibold text-slate-100">Peers</h1>
        {user?.role === "admin" && (
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleImport}
              disabled={importMutation.isPending}
              className="rounded-md border border-surface-border px-3 py-1.5 text-sm text-slate-300 hover:bg-surface-raised disabled:opacity-50"
            >
              {importMutation.isPending ? "Importing…" : "Import from router"}
            </button>
            <Link
              to="/peers/new"
              className="rounded-md bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-900 hover:bg-white"
            >
              + Add peer
            </Link>
          </div>
        )}
      </div>

      {importMessage && (
        <div className="rounded-md border border-surface-border bg-surface-raised px-3 py-2 text-sm text-slate-300">
          {importMessage}
          <button type="button" className="ml-3 underline" onClick={() => setImportMessage(null)}>
            Dismiss
          </button>
        </div>
      )}

      {importError && (
        <div className="rounded-md border border-danger bg-danger-bg px-3 py-2 text-sm text-danger">
          {importError}
          <button type="button" className="ml-3 underline" onClick={() => setImportError(null)}>
            Dismiss
          </button>
        </div>
      )}

      <PeerFilterBar
        search={search}
        onSearchChange={(v) => {
          setSearch(v);
          setPage(1);
        }}
        statusFilter={statusFilter}
        onStatusFilterChange={(v) => {
          setStatusFilter(v);
          setPage(1);
        }}
      />

      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <Spinner size="lg" />
        </div>
      ) : !data || data.items.length === 0 ? (
        <EmptyState title="No peers found" description="Try adjusting your search or filters." />
      ) : (
        <>
          <PeersTable peers={data.items} />
          <div className="flex items-center justify-between text-sm text-slate-400">
            <span>
              {data.total} peer{data.total === 1 ? "" : "s"}
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="rounded-md border border-surface-border px-2 py-1 disabled:opacity-40"
              >
                Prev
              </button>
              <span>
                Page {page} / {totalPages}
              </span>
              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="rounded-md border border-surface-border px-2 py-1 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
