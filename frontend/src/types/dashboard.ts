export interface ConcentratorHealth {
  reachable: boolean;
  version: string | null;
  uptime_seconds: number | null;
  cpu_load_percent: number | null;
  free_memory_bytes: number | null;
  total_memory_bytes: number | null;
  last_poll_at: string | null;
  last_error: string | null;
}

export interface DashboardSummary {
  online_count: number;
  offline_count: number;
  total_peers: number;
  active_alert_count: number;
  concentrator: ConcentratorHealth;
}

export interface AvailabilityPoint {
  timestamp: string;
  online_count: number;
  total_count: number;
}

export type TimeRange = "24h" | "7d" | "30d";
