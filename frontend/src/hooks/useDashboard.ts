import { useQuery } from "@tanstack/react-query";

import { getAvailability, getDashboardSummary } from "@/api/dashboard";
import type { TimeRange } from "@/types/dashboard";

export function useDashboardSummary() {
  return useQuery({
    queryKey: ["dashboard", "summary"],
    queryFn: getDashboardSummary,
    refetchInterval: 30_000,
  });
}

export function useAvailability(range: TimeRange = "24h") {
  return useQuery({
    queryKey: ["dashboard", "availability", range],
    queryFn: () => getAvailability(range),
    refetchInterval: 60_000,
  });
}
