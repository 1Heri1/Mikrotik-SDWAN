import { useState } from "react";

import { useAuth } from "@/auth/useAuth";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { useCreateUser, useDeleteUser, useUpdateUser, useUsers } from "@/hooks/useSettings";
import { formatDateTime } from "@/lib/format";
import type { UserRole } from "@/types/user";

export function UserManagementTable() {
  const { user: currentUser } = useAuth();
  const { data: users, isLoading } = useUsers();
  const createUser = useCreateUser();
  const updateUser = useUpdateUser();
  const deleteUser = useDeleteUser();

  const [newUsername, setNewUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newRole, setNewRole] = useState<UserRole>("viewer");
  const [deleteTarget, setDeleteTarget] = useState<{ id: number; username: string } | null>(null);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    await createUser.mutateAsync({ username: newUsername, password: newPassword, role: newRole });
    setNewUsername("");
    setNewPassword("");
    setNewRole("viewer");
  }

  if (isLoading) return <p className="text-sm text-slate-500">Loading users…</p>;

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto rounded-lg border border-surface-border">
        <table className="w-full min-w-[520px] text-sm">
          <thead className="bg-surface-raised text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-2">Username</th>
              <th className="px-4 py-2">Role</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Last login</th>
              <th className="px-4 py-2" />
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-border">
            {users?.map((u) => (
              <tr key={u.id}>
                <td className="px-4 py-2 text-slate-200">{u.username}</td>
                <td className="px-4 py-2">
                  <select
                    value={u.role}
                    disabled={u.id === currentUser?.id}
                    onChange={(e) => updateUser.mutate({ id: u.id, body: { role: e.target.value as UserRole } })}
                    className="rounded-md border border-surface-border bg-surface px-2 py-1 text-xs text-slate-200 disabled:opacity-50"
                  >
                    <option value="admin">admin</option>
                    <option value="viewer">viewer</option>
                  </select>
                </td>
                <td className="px-4 py-2">
                  <button
                    type="button"
                    disabled={u.id === currentUser?.id}
                    onClick={() => updateUser.mutate({ id: u.id, body: { is_active: !u.is_active } })}
                    className="rounded-md border border-surface-border px-2 py-1 text-xs text-slate-300 hover:bg-surface-raised disabled:opacity-50"
                  >
                    {u.is_active ? "Active" : "Disabled"}
                  </button>
                </td>
                <td className="px-4 py-2 text-slate-400">{formatDateTime(u.last_login_at)}</td>
                <td className="px-4 py-2 text-right">
                  <button
                    type="button"
                    disabled={u.id === currentUser?.id}
                    onClick={() => setDeleteTarget({ id: u.id, username: u.username })}
                    className="text-xs text-danger hover:underline disabled:opacity-50"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <form onSubmit={handleCreate} className="flex flex-wrap items-end gap-3 rounded-lg border border-surface-border bg-surface-raised p-3">
        <div>
          <label className="block text-xs text-slate-400">Username</label>
          <input
            required
            value={newUsername}
            onChange={(e) => setNewUsername(e.target.value)}
            className="mt-1 rounded-md border border-surface-border bg-surface px-2 py-1.5 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-xs text-slate-400">Password</label>
          <input
            required
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className="mt-1 rounded-md border border-surface-border bg-surface px-2 py-1.5 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-xs text-slate-400">Role</label>
          <select
            value={newRole}
            onChange={(e) => setNewRole(e.target.value as UserRole)}
            className="mt-1 rounded-md border border-surface-border bg-surface px-2 py-1.5 text-sm text-slate-100 focus:border-slate-500 focus:outline-none"
          >
            <option value="viewer">viewer</option>
            <option value="admin">admin</option>
          </select>
        </div>
        <button
          type="submit"
          disabled={createUser.isPending}
          className="rounded-md bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-900 hover:bg-white disabled:opacity-50"
        >
          Add user
        </button>
      </form>

      <ConfirmDialog
        open={!!deleteTarget}
        title={`Delete user "${deleteTarget?.username}"?`}
        confirmLabel="Delete"
        danger
        isSubmitting={deleteUser.isPending}
        onConfirm={async () => {
          if (deleteTarget) await deleteUser.mutateAsync(deleteTarget.id);
          setDeleteTarget(null);
        }}
        onCancel={() => setDeleteTarget(null)}
      >
        This user will immediately lose access to the app.
      </ConfirmDialog>
    </div>
  );
}
