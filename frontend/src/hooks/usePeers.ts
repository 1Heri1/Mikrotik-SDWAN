import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as peersApi from "@/api/peers";
import type { PeerCreate, PeerUpdate } from "@/types/peer";

export function usePeersList(params: peersApi.PeerListParams) {
  return useQuery({
    queryKey: ["peers", params],
    queryFn: () => peersApi.listPeers(params),
    refetchInterval: 30_000,
  });
}

export function usePeer(id: number) {
  return useQuery({
    queryKey: ["peers", id],
    queryFn: () => peersApi.getPeer(id),
    refetchInterval: 30_000,
  });
}

export function usePeerHistory(id: number, range: "24h" | "7d" | "30d") {
  return useQuery({
    queryKey: ["peers", id, "history", range],
    queryFn: () => peersApi.getPeerHistory(id, range),
  });
}

export function useCreatePeer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: PeerCreate) => peersApi.createPeer(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["peers"] }),
  });
}

export function usePreviewPeerUpdate(id: number) {
  return useMutation({ mutationFn: (body: PeerUpdate) => peersApi.previewPeerUpdate(id, body) });
}

function invalidatePeer(queryClient: ReturnType<typeof useQueryClient>, id: number) {
  queryClient.invalidateQueries({ queryKey: ["peers"] });
  queryClient.invalidateQueries({ queryKey: ["peers", id] });
  queryClient.invalidateQueries({ queryKey: ["audit"] });
}

export function useUpdatePeer(id: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: PeerUpdate) => peersApi.updatePeer(id, body),
    onSuccess: () => invalidatePeer(queryClient, id),
  });
}

export function useSetPeerEnabled(id: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (enabled: boolean) => (enabled ? peersApi.enablePeer(id) : peersApi.disablePeer(id)),
    onSuccess: () => invalidatePeer(queryClient, id),
  });
}

export function useResetPeerPassword(id: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (newPassword?: string) => peersApi.resetPeerPassword(id, newPassword),
    onSuccess: () => invalidatePeer(queryClient, id),
  });
}

export function useRevealPeerPassword(id: number) {
  return useMutation({ mutationFn: () => peersApi.revealPeerPassword(id) });
}

export function useDeletePeer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => peersApi.deletePeer(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["peers"] }),
  });
}

export function useGeneratePassword() {
  return useMutation({ mutationFn: () => peersApi.generatePassword() });
}
