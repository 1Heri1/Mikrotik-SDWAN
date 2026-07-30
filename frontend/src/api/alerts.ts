import { apiClient } from "@/api/client";
import type { Alert } from "@/types/alert";

export async function listAlerts(status: "active" | "resolved" = "active"): Promise<Alert[]> {
  const { data } = await apiClient.get<Alert[]>("/alerts", { params: { status_: status } });
  return data;
}

export async function acknowledgeAlert(id: number): Promise<Alert> {
  const { data } = await apiClient.post<Alert>(`/alerts/${id}/acknowledge`);
  return data;
}

export async function resolveAlert(id: number): Promise<Alert> {
  const { data } = await apiClient.post<Alert>(`/alerts/${id}/resolve`);
  return data;
}
