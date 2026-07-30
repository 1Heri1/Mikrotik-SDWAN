export interface Peer {
  id: number;
  name: string;
  mikrotik_profile: string;
  service: string;
  assigned_local_address: string | null;
  assigned_remote_address: string | null;
  comment: string | null;
  enabled: boolean;
  last_seen_online_at: string | null;
  created_at: string;
  is_online: boolean;
}

export interface PeerCreate {
  name: string;
  password: string;
  mikrotik_profile: string;
  service: "pptp" | "l2tp";
  assigned_local_address?: string | null;
  assigned_remote_address?: string | null;
  comment?: string | null;
}

export interface PeerUpdate {
  password?: string | null;
  mikrotik_profile?: string | null;
  assigned_local_address?: string | null;
  assigned_remote_address?: string | null;
  comment?: string | null;
}

export interface DiffPreview {
  changes: Record<string, { before: unknown; after: unknown }>;
  has_changes: boolean;
}

export interface PeerHistoryPoint {
  timestamp: string;
  is_online: boolean;
  uptime_seconds: number | null;
  caller_id: string | null;
  remote_address: string | null;
  tx_bytes: number | null;
  rx_bytes: number | null;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
