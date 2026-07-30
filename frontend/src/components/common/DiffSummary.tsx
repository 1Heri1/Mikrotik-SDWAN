import type { DiffPreview } from "@/types/peer";

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  return String(value);
}

export function DiffSummary({ diff }: { diff: DiffPreview }) {
  const entries = Object.entries(diff.changes);

  if (entries.length === 0) {
    return <p className="text-slate-400">No changes to apply.</p>;
  }

  return (
    <table className="w-full border-collapse text-sm">
      <thead>
        <tr className="text-left text-xs uppercase text-slate-500">
          <th className="pb-2 pr-4">Field</th>
          <th className="pb-2 pr-4">Before</th>
          <th className="pb-2">After</th>
        </tr>
      </thead>
      <tbody>
        {entries.map(([field, change]) => (
          <tr key={field} className="border-t border-surface-border">
            <td className="py-2 pr-4 font-medium text-slate-200">{field.replaceAll("_", " ")}</td>
            <td className="py-2 pr-4 text-danger">{formatValue(change.before)}</td>
            <td className="py-2 text-ok">{formatValue(change.after)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
