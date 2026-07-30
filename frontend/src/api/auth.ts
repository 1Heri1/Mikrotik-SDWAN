import { apiClient } from "@/api/client";
import type { User } from "@/types/user";

export interface LoginResponse {
  access_token: string;
  token_type: string;
  role: User["role"];
  username: string;
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const { data } = await apiClient.post<LoginResponse>("/auth/login", { username, password });
  return data;
}

export async function refresh(): Promise<LoginResponse> {
  const { data } = await apiClient.post<LoginResponse>("/auth/refresh");
  return data;
}

export async function logout(): Promise<void> {
  await apiClient.post("/auth/logout");
}

export async function getMe(): Promise<User> {
  const { data } = await apiClient.get<User>("/auth/me");
  return data;
}
