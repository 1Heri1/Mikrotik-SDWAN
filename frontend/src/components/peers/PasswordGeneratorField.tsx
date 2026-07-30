import { useState } from "react";

import { useGeneratePassword } from "@/hooks/usePeers";

interface PasswordGeneratorFieldProps {
  value: string;
  onChange: (value: string) => void;
  label?: string;
  placeholder?: string;
}

export function PasswordGeneratorField({
  value,
  onChange,
  label = "Password",
  placeholder,
}: PasswordGeneratorFieldProps) {
  const [reveal, setReveal] = useState(false);
  const generate = useGeneratePassword();

  async function handleGenerate() {
    const password = await generate.mutateAsync();
    onChange(password);
    setReveal(true);
  }

  return (
    <div>
      <label className="block text-xs font-medium text-slate-400">{label}</label>
      <div className="mt-1 flex gap-2">
        <input
          type={reveal ? "text" : "password"}
          value={value}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
          className="w-full rounded-md border border-surface-border bg-surface px-3 py-2 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
        />
        <button
          type="button"
          onClick={() => setReveal((r) => !r)}
          className="shrink-0 rounded-md border border-surface-border px-2 text-xs text-slate-300 hover:bg-surface-raised"
        >
          {reveal ? "Hide" : "Show"}
        </button>
        <button
          type="button"
          onClick={handleGenerate}
          disabled={generate.isPending}
          className="shrink-0 rounded-md border border-surface-border px-2 text-xs text-slate-300 hover:bg-surface-raised disabled:opacity-50"
        >
          Generate
        </button>
      </div>
    </div>
  );
}
