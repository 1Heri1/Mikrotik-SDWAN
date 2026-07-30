import type { ReactNode } from "react";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  children?: ReactNode;
  confirmLabel?: string;
  danger?: boolean;
  isSubmitting?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  open,
  title,
  children,
  confirmLabel = "Confirm",
  danger = false,
  isSubmitting = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-lg rounded-lg border border-surface-border bg-surface-raised p-5 shadow-xl">
        <h3 className="text-base font-semibold text-slate-100">{title}</h3>
        <div className="mt-3 max-h-96 overflow-y-auto text-sm text-slate-300">{children}</div>
        <div className="mt-5 flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-md border border-surface-border px-3 py-1.5 text-sm text-slate-300 hover:bg-surface"
            disabled={isSubmitting}
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isSubmitting}
            className={
              danger
                ? "rounded-md bg-danger px-3 py-1.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
                : "rounded-md bg-ok px-3 py-1.5 text-sm font-medium text-black hover:opacity-90 disabled:opacity-50"
            }
          >
            {isSubmitting ? "Working…" : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
