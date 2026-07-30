function formatValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export function DiffView({
  before,
  after,
}: {
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
}) {
  const keys = Array.from(new Set([...Object.keys(before ?? {}), ...Object.keys(after ?? {})]));

  if (keys.length === 0) {
    return <p className="text-xs text-slate-500">No field-level detail recorded for this action.</p>;
  }

  return (
    <table className="w-full text-xs">
      <thead>
        <tr className="text-left uppercase text-slate-500">
          <th className="pb-1 pr-3">Field</th>
          <th className="pb-1 pr-3">Before</th>
          <th className="pb-1">After</th>
        </tr>
      </thead>
      <tbody>
        {keys.map((key) => (
          <tr key={key} className="border-t border-surface-border">
            <td className="py-1 pr-3 font-medium text-slate-300">{key}</td>
            <td className="py-1 pr-3 text-slate-400">{formatValue(before?.[key])}</td>
            <td className="py-1 text-slate-200">{formatValue(after?.[key])}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
