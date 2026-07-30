export type UserRole = "admin" | "viewer";

export interface User {
  id: number;
  username: string;
  role: UserRole;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
}
