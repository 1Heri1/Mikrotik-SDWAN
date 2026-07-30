import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as settingsApi from "@/api/settings";
import * as usersApi from "@/api/users";
import type { NotificationSettingsUpdate, RouterConfigUpdate } from "@/types/settings";

export function useRouterConfig() {
  return useQuery({ queryKey: ["settings", "router"], queryFn: settingsApi.getRouterConfig });
}

export function useUpdateRouterConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: RouterConfigUpdate) => settingsApi.updateRouterConfig(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["settings", "router"] }),
  });
}

export function useTestRouterConnection() {
  return useMutation({ mutationFn: settingsApi.testRouterConnection });
}

export function useNotificationSettings() {
  return useQuery({ queryKey: ["settings", "notifications"], queryFn: settingsApi.getNotificationSettings });
}

export function useUpdateNotificationSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: NotificationSettingsUpdate) => settingsApi.updateNotificationSettings(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["settings", "notifications"] }),
  });
}

export function useTestTelegram() {
  return useMutation({
    mutationFn: ({ botToken, chatId }: { botToken?: string; chatId?: string }) =>
      settingsApi.testTelegram(botToken, chatId),
  });
}

export function useUsers() {
  return useQuery({ queryKey: ["users"], queryFn: usersApi.listUsers });
}

export function useCreateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: usersApi.createUser,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: usersApi.UserUpdate }) => usersApi.updateUser(id, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
  });
}

export function useDeleteUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: usersApi.deleteUser,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
  });
}
