import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { acknowledgeAlert, listAlerts, resolveAlert } from "@/api/alerts";

export function useAlerts(status: "active" | "resolved" = "active") {
  return useQuery({
    queryKey: ["alerts", status],
    queryFn: () => listAlerts(status),
    refetchInterval: 30_000,
  });
}

export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => acknowledgeAlert(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alerts"] }),
  });
}

export function useResolveAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => resolveAlert(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] });
    },
  });
}
