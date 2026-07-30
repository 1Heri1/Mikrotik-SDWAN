import clsx from "clsx";
import { NavLink } from "react-router-dom";

import { useAuth } from "@/auth/useAuth";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: "📊", end: true },
  { to: "/peers", label: "Peers", icon: "🖧", end: false },
  { to: "/audit", label: "Audit log", icon: "📜", end: false, adminOnly: true },
  { to: "/settings", label: "Settings", icon: "⚙️", end: false, adminOnly: true },
];

export function Sidebar() {
  const { user } = useAuth();

  return (
    <aside className="hidden w-56 shrink-0 border-r border-surface-border bg-surface md:block">
      <div className="px-4 py-5">
        <p className="text-sm font-semibold tracking-wide text-slate-100">Mikrotik VPN Monitor</p>
      </div>
      <nav className="flex flex-col gap-1 px-2">
        {NAV_ITEMS.filter((item) => !item.adminOnly || user?.role === "admin").map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-surface-raised text-slate-100"
                  : "text-slate-400 hover:bg-surface-raised hover:text-slate-200"
              )
            }
          >
            <span aria-hidden>{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
