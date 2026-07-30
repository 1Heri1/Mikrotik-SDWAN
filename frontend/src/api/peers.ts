import { apiClient } from "@/api/client";
import type {
  DiffPreview,
  ImportSummary,
  Paginated,
  Peer,
  PeerCreate,
  PeerHistoryPoint,
  PeerUpdate,
} from "@/types/peer";

export interface PeerListParams {
  search?: string;
  status_filter?: "online" | "offline";
  profile?: string;
  page?: number;
  page_size?: number;
}

export async function listPeers(params: PeerListParams): Promise<Paginated<Peer>> {
  const { data } = await apiClient.get<Paginated<Peer>>("/peers", { params });
  return data;
}

export async function getPeer(id: number): Promise<Peer> {
  const { data } = await apiClient.get<Peer>(`/peers/${id}`);
  return data;
}

export async function getPeerHistory(id: number, range: "24h" | "7d" | "30d"): Promise<PeerHistoryPoint[]> {
  const { data } = await apiClient.get<PeerHistoryPoint[]>(`/peers/${id}/history`, { params: { range } });
  return data;
}

export async function createPeer(body: PeerCreate): Promise<Peer> {
  const { data } = await apiClient.post<Peer>("/peers", body);
  return data;
}

export async function previewPeerUpdate(id: number, body: PeerUpdate): Promise<DiffPreview> {
  const { data } = await apiClient.post<DiffPreview>(`/peers/${id}/preview`, body);
  return data;
}

export async function updatePeer(id: number, body: PeerUpdate): Promise<Peer> {
  const { data } = await apiClient.patch<Peer>(`/peers/${id}`, body);
  return data;
}

export async function enablePeer(id: number): Promise<Peer> {
  const { data } = await apiClient.post<Peer>(`/peers/${id}/enable`);
  return data;
}

export async function disablePeer(id: number): Promise<Peer> {
  const { data } = await apiClient.post<Peer>(`/peers/${id}/disable`);
  return data;
}

export async function resetPeerPassword(id: number, newPassword?: string): Promise<Peer> {
  const { data } = await apiClient.post<Peer>(
    `/peers/${id}/reset-password`,
    {},
    { params: newPassword ? { new_password: newPassword } : {} }
  );
  return data;
}

export async function revealPeerPassword(id: number): Promise<{ known: boolean; password: string | null }> {
  const { data } = await apiClient.get<{ known: boolean; password: string | null }>(
    `/peers/${id}/reveal-password`
  );
  return data;
}

export async function importPeersFromRouter(): Promise<ImportSummary> {
  const { data } = await apiClient.post<ImportSummary>("/peers/import");
  return data;
}

export async function deletePeer(id: number): Promise<void> {
  await apiClient.delete(`/peers/${id}`);
}

export async function generatePassword(): Promise<string> {
  const { data } = await apiClient.get<{ password: string }>("/peers/generate-password");
  return data.password;
}
