import { useNavigate } from "react-router-dom";

import { useAuth } from "@/auth/useAuth";
import { ThemeToggle } from "@/components/common/ThemeToggle";

export function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <header className="flex h-14 items-center justify-between border-b border-surface-border bg-surface px-4">
      <div className="md:hidden text-sm font-semibold text-slate-100">Mikrotik VPN Monitor</div>
      <div className="flex-1" />
      <div className="flex items-center gap-3">
        <ThemeToggle />
        {user && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-slate-300">{user.username}</span>
            <span className="rounded bg-surface-raised px-2 py-0.5 text-xs uppercase text-slate-400">
              {user.role}
            </span>
          </div>
        )}
        <button
          type="button"
          onClick={handleLogout}
          className="rounded-md border border-surface-border px-3 py-1.5 text-xs text-slate-300 hover:bg-surface-raised"
        >
          Log out
        </button>
      </div>
    </header>
  );
}
