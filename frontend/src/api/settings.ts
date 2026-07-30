import { apiClient } from "@/api/client";
import type {
  NotificationSettings,
  NotificationSettingsUpdate,
  RouterConfig,
  RouterConfigUpdate,
  TestConnectionResult,
} from "@/types/settings";

export async function getRouterConfig(): Promise<RouterConfig | null> {
  const { data } = await apiClient.get<RouterConfig | null>("/settings/router");
  return data;
}

export async function updateRouterConfig(body: RouterConfigUpdate): Promise<RouterConfig> {
  const { data } = await apiClient.put<RouterConfig>("/settings/router", body);
  return data;
}

export async function testRouterConnection(): Promise<TestConnectionResult> {
  const { data } = await apiClient.post<TestConnectionResult>("/settings/router/test-connection");
  return data;
}

export async function getNotificationSettings(): Promise<NotificationSettings> {
  const { data } = await apiClient.get<NotificationSettings>("/settings/notifications");
  return data;
}

export async function updateNotificationSettings(body: NotificationSettingsUpdate): Promise<NotificationSettings> {
  const { data } = await apiClient.put<NotificationSettings>("/settings/notifications", body);
  return data;
}

export async function testTelegram(botToken?: string, chatId?: string): Promise<TestConnectionResult> {
  const { data } = await apiClient.post<TestConnectionResult>("/settings/notifications/test-telegram", {
    bot_token: botToken || undefined,
    chat_id: chatId || undefined,
  });
  return data;
}
