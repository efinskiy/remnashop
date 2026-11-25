import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";

export type NotificationChannels = ApiSchema<"NotificationChannelsResponse">;

export type PushSubscriptionItem = ApiSchema<"PushSubscriptionResponse">;

export type PushSubscriptionBody = ApiSchema<"SubscribePushRequest">;

export type NotificationSettings = ApiSchema<"NotificationSettingsResponse">;

interface NotificationSettingsUpdate {
  vapid_contact?: string;
  report_timezone?: string;
  daily_report_hour?: number;
}

export function getNotificationChannels(signal?: AbortSignal): Promise<NotificationChannels> {
  return apiGet<NotificationChannels>("/notifications/channels", signal);
}

export function updateNotificationChannels(channels: Record<string, string[]>): Promise<NotificationChannels> {
  return apiPut<NotificationChannels, ApiSchema<"UpdateNotificationChannelsRequest">>("/notifications/channels", {
    channels,
  });
}

export function getPushPublicKey(): Promise<{ public_key: string | null }> {
  return apiGet<ApiSchema<"PushPublicKeyResponse">>("/notifications/push/public-key");
}

export function listPushSubscriptions(signal?: AbortSignal): Promise<ApiSchema<"PushSubscriptionListResponse">> {
  return apiGet<ApiSchema<"PushSubscriptionListResponse">>("/notifications/push-subscriptions", signal);
}

export function subscribePush(body: PushSubscriptionBody): Promise<PushSubscriptionItem> {
  return apiPost<PushSubscriptionItem, PushSubscriptionBody>("/notifications/push-subscriptions", body);
}

export function deletePushSubscription(id: number): Promise<void> {
  return apiDelete<void>(`/notifications/push-subscriptions/${id}`);
}

export function sendTestPush(): Promise<{ delivered: number }> {
  return apiPost<ApiSchema<"TestPushResponse">, Record<string, never>>("/notifications/push-subscriptions/actions/test", {});
}

export function getNotificationSettings(signal?: AbortSignal): Promise<NotificationSettings> {
  return apiGet<NotificationSettings>("/notifications/settings", signal);
}

export function updateNotificationSettings(body: NotificationSettingsUpdate): Promise<NotificationSettings> {
  return apiPatch<NotificationSettings, ApiSchema<"UpdateNotificationSettingsRequest">>("/notifications/settings", body);
}

export function generateVapidKeys(): Promise<NotificationSettings> {
  return apiPost<NotificationSettings, Record<string, never>>(
    "/notifications/settings/actions/generate-vapid-keys",
    {},
  );
}
