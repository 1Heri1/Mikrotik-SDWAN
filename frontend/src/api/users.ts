import { apiClient } from "@/api/client";
import type { User, UserRole } from "@/types/user";

export interface UserCreate {
  username: string;
  password: string;
  role: UserRole;
}

export interface UserUpdate {
  role?: UserRole;
  is_active?: boolean;
  password?: string;
}

export async function listUsers(): Promise<User[]> {
  const { data } = await apiClient.get<User[]>("/users");
  return data;
}

export async function createUser(body: UserCreate): Promise<User> {
  const { data } = await apiClient.post<User>("/users", body);
  return data;
}

export async function updateUser(id: number, body: UserUpdate): Promise<User> {
  const { data } = await apiClient.patch<User>(`/users/${id}`, body);
  return data;
}

export async function deleteUser(id: number): Promise<void> {
  await apiClient.delete(`/users/${id}`);
}
