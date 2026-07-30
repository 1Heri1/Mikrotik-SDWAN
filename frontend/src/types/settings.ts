export type MikrotikProtocol = "librouteros" | "rest";

export interface RouterConfig {
  id: number;
  host: string;
  port: number;
  api_user: string;
  protocol: MikrotikProtocol;
  verify_ssl: boolean;
  backup_before_bulk_ops: boolean;
  updated_at: string;
  secret_configured: boolean;
}

export interface RouterConfigUpdate {
  host: string;
  port: number;
  api_user: string;
  api_secret?: string | null;
  protocol: MikrotikProtocol;
  verify_ssl: boolean;
  backup_before_bulk_ops: boolean;
}

export interface TestConnectionResult {
  success: boolean;
  message: string;
}

export interface NotificationSettings {
  telegram_enabled: boolean;
  telegram_chat_id: string | null;
  telegram_token_configured: boolean;
  smtp_enabled: boolean;
  smtp_host: string | null;
  smtp_port: number | null;
  smtp_username: string | null;
  smtp_password_configured: boolean;
  smtp_from_address: string | null;
  smtp_to_address: string | null;
  smtp_use_tls: boolean;
  offline_threshold_minutes: number;
  router_unreachable_realert_minutes: number;
  snapshot_retention_days: number;
  updated_at: string;
}

export interface NotificationSettingsUpdate {
  telegram_enabled: boolean;
  telegram_bot_token?: string | null;
  telegram_chat_id?: string | null;
  smtp_enabled: boolean;
  smtp_host?: string | null;
  smtp_port?: number | null;
  smtp_username?: string | null;
  smtp_password?: string | null;
  smtp_from_address?: string | null;
  smtp_to_address?: string | null;
  smtp_use_tls: boolean;
  offline_threshold_minutes: number;
  router_unreachable_realert_minutes: number;
  snapshot_retention_days: number;
}
