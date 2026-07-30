import { apiClient } from "@/api/client";
import type { AvailabilityPoint, DashboardSummary, TimeRange } from "@/types/dashboard";

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const { data } = await apiClient.get<DashboardSummary>("/dashboard/summary");
  return data;
}

export async function getAvailability(range: TimeRange = "24h"): Promise<AvailabilityPoint[]> {
  const { data } = await apiClient.get<AvailabilityPoint[]>("/dashboard/availability", { params: { range } });
  return data;
}
