import clsx from "clsx";

export function Spinner({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const sizeClass = { sm: "h-4 w-4 border-2", md: "h-8 w-8 border-2", lg: "h-12 w-12 border-4" }[size];
  return (
    <div
      className={clsx("animate-spin rounded-full border-slate-600 border-t-slate-200", sizeClass)}
      role="status"
      aria-label="Loading"
    />
  );
}
