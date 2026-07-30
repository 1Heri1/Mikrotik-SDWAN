import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="flex h-screen flex-col items-center justify-center gap-2 bg-surface text-slate-300">
      <p className="text-4xl font-semibold">404</p>
      <p className="text-sm text-slate-500">Page not found.</p>
      <Link to="/" className="mt-2 text-sm text-slate-300 underline">
        Back to dashboard
      </Link>
    </div>
  );
}
