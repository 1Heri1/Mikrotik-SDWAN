import { createBrowserRouter } from "react-router-dom";

import { RequireAuth } from "@/auth/RequireAuth";
import { AppLayout } from "@/layouts/AppLayout";
import { AuthLayout } from "@/layouts/AuthLayout";
import { AuditLogPage } from "@/pages/AuditLogPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { LoginPage } from "@/pages/LoginPage";
import { NotFoundPage } from "@/pages/NotFoundPage";
import { PeerAddPage } from "@/pages/PeerAddPage";
import { PeerDetailPage } from "@/pages/PeerDetailPage";
import { PeersListPage } from "@/pages/PeersListPage";
import { SettingsPage } from "@/pages/SettingsPage";

export const router = createBrowserRouter([
  {
    element: <AuthLayout />,
    children: [{ path: "/login", element: <LoginPage /> }],
  },
  {
    element: (
      <RequireAuth>
        <AppLayout />
      </RequireAuth>
    ),
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "/peers", element: <PeersListPage /> },
      {
        path: "/peers/new",
        element: (
          <RequireAuth roles={["admin"]}>
            <PeerAddPage />
          </RequireAuth>
        ),
      },
      { path: "/peers/:peerId", element: <PeerDetailPage /> },
      {
        path: "/audit",
        element: (
          <RequireAuth roles={["admin"]}>
            <AuditLogPage />
          </RequireAuth>
        ),
      },
      {
        path: "/settings",
        element: (
          <RequireAuth roles={["admin"]}>
            <SettingsPage />
          </RequireAuth>
        ),
      },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
]);
