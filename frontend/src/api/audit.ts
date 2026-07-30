import { apiClient } from "@/api/client";
import type { AuditLogEntry } from "@/types/audit";
import type { Paginated } from "@/types/peer";

export interface AuditListParams {
  user_id?: number;
  action?: string;
  peer_id?: number;
  page?: number;
  page_size?: number;
}

export async function listAuditLog(params: AuditListParams): Promise<Paginated<AuditLogEntry>> {
  const { data } = await apiClient.get<Paginated<AuditLogEntry>>("/audit", { params });
  return data;
}
