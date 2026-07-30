export type AlertSeverity = "info" | "warning" | "critical";

export interface Alert {
  id: number;
  peer_id: number | null;
  peer_name: string | null;
  type: string;
  severity: AlertSeverity;
  message: string;
  created_at: string;
  resolved_at: string | null;
  acknowledged_by: number | null;
  acknowledged_by_username: string | null;
  acknowledged_at: string | null;
}
