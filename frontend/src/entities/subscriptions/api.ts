import type { AddOnType } from "@entities/addons/api";
import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from "@shared/api/http";
import { DAY_MS } from "@shared/lib/period";
import type { BadgeTone } from "@shared/ui/Badge";
import type { ApiSchema } from "@shared/api/schemas";

export type SubscriptionStatus = ApiSchema<"SubscriptionStatus">;
export type TrafficLimitStrategy = ApiSchema<"TrafficLimitStrategy">;

/** a stretch of the term and what was paid for it; a plan change credits what's left of each */
export type CreditSegment = ApiSchema<"CreditSegmentResponse">;

export type SubscriptionListItem = ApiSchema<"SubscriptionResponse">;

export function addonTotal(subscription: Pick<SubscriptionListItem, "addon_entitlements">, type: AddOnType): number {
  return subscription.addon_entitlements.reduce((sum, item) => sum + (item.type === type ? item.amount : 0), 0);
}

export type SubscriptionRow = ApiSchema<"SubscriptionListItemResponse">;

export type SubscriptionDetail = ApiSchema<"SubscriptionDetailResponse">;

export const SUBSCRIPTION_STATUS_BADGE_TONE: Record<SubscriptionStatus, BadgeTone> = {
  ACTIVE: "success",
  LIMITED: "warning",
  EXPIRED: "error",
  DISABLED: "neutral",
  DELETED: "neutral",
};

export const EXPIRING_SOON_DAYS = 7;

export function daysUntil(iso: string): number {
  return Math.ceil((new Date(iso).getTime() - Date.now()) / DAY_MS);
}

export function expiryToneClassName(days: number): string {
  if (days < 0) return "text-error";
  return days <= EXPIRING_SOON_DAYS ? "text-warning" : "text-muted-foreground";
}

export function formatTraffic(gb: number, unlimitedLabel: string): string {
  return gb === 0 ? unlimitedLabel : `${gb} GB`;
}

export function formatLimit(value: number, unlimitedLabel: string): string {
  return value === 0 ? unlimitedLabel : String(value);
}

export const DEFAULT_PAGE_SIZE = 50;

export type SubscriptionListPage = ApiSchema<"SubscriptionPageResponse">;

export type SubscriptionSort = "created_at" | "expire_at";

export interface SubscriptionListFilters {
  status?: SubscriptionStatus;
  search?: string;
  userId?: number;
  sort?: SubscriptionSort;
  descending?: boolean;
  page?: number;
  pageSize?: number;
}

export function listSubscriptions(
  filters: SubscriptionListFilters = {},
  signal?: AbortSignal,
): Promise<SubscriptionListPage> {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.search) params.set("search", filters.search);
  if (filters.userId !== undefined) params.set("user_id", String(filters.userId));
  if (filters.sort) params.set("sort", filters.sort);
  if (filters.descending !== undefined) params.set("descending", String(filters.descending));
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.pageSize ?? DEFAULT_PAGE_SIZE));

  return apiGet<SubscriptionListPage>(`/subscriptions?${params.toString()}`, signal);
}

export type UpdateSubscriptionRequest = ApiSchema<"UpdateSubscriptionRequest">;

export function updateSubscription(
  subscriptionId: number,
  payload: UpdateSubscriptionRequest,
): Promise<SubscriptionListItem> {
  return apiPatch<SubscriptionListItem, UpdateSubscriptionRequest>(`/subscriptions/${subscriptionId}`, payload);
}

export type SubscriptionSquads = Required<ApiSchema<"UpdateSubscriptionSquadsRequest">>;

export function updateSubscriptionSquads(
  subscriptionId: number,
  squads: SubscriptionSquads,
): Promise<SubscriptionListItem> {
  return apiPut<SubscriptionListItem, SubscriptionSquads>(`/subscriptions/${subscriptionId}/squads`, squads);
}

export function getSubscription(subscriptionId: number, signal?: AbortSignal): Promise<SubscriptionDetail> {
  return apiGet<SubscriptionDetail>(`/subscriptions/${subscriptionId}`, signal);
}

export type PanelSquad = ApiSchema<"PanelSquadResponse">;

export function listPanelSquads(signal?: AbortSignal): Promise<{ items: PanelSquad[]; total: number }> {
  return apiGet<ApiSchema<"PanelSquadListResponse">>("/subscriptions/squads", signal);
}

export function deleteSubscription(subscriptionId: number): Promise<void> {
  return apiDelete<void>(`/subscriptions/${subscriptionId}`);
}

export function deleteUserSubscriptions(userId: number): Promise<{ deleted: number }> {
  return apiPost<ApiSchema<"DeletedSubscriptionsResponse">, Record<string, never>>(`/users/${userId}/subscriptions/bulk/delete`, {});
}

export type GrantSubscriptionRequest = ApiSchema<"GrantSubscriptionRequest">;

export function grantSubscription(payload: GrantSubscriptionRequest): Promise<SubscriptionListItem> {
  return apiPost<SubscriptionListItem, GrantSubscriptionRequest>("/subscriptions", payload);
}

export type ChangeSubscriptionPlanRequest = ApiSchema<"ChangeSubscriptionPlanRequest">;

export function changeSubscriptionPlan(
  subscriptionId: number,
  payload: ChangeSubscriptionPlanRequest,
): Promise<SubscriptionListItem> {
  return apiPost<SubscriptionListItem, ChangeSubscriptionPlanRequest>(
    `/subscriptions/${subscriptionId}/actions/change-plan`,
    payload,
  );
}

function subscriptionAction(subscriptionId: number, action: string): Promise<SubscriptionListItem> {
  return apiPost<SubscriptionListItem, Record<string, never>>(`/subscriptions/${subscriptionId}/actions/${action}`, {});
}

export const enableSubscription = (subscriptionId: number) => subscriptionAction(subscriptionId, "enable");
export const disableSubscription = (subscriptionId: number) => subscriptionAction(subscriptionId, "disable");
export const resetSubscriptionTraffic = (subscriptionId: number) => subscriptionAction(subscriptionId, "reset-traffic");
export const reissueSubscriptionLink = (subscriptionId: number) => subscriptionAction(subscriptionId, "reissue");

export type SubscriptionDeviceList = ApiSchema<"DeviceListResponse">;

export function listSubscriptionDevices(subscriptionId: number, signal?: AbortSignal): Promise<SubscriptionDeviceList> {
  return apiGet<SubscriptionDeviceList>(`/subscriptions/${subscriptionId}/devices`, signal);
}

export function deleteSubscriptionDevice(subscriptionId: number, hwid: string): Promise<void> {
  return apiDelete<void>(`/subscriptions/${subscriptionId}/devices/${encodeURIComponent(hwid)}`);
}

export function deleteAllSubscriptionDevices(subscriptionId: number): Promise<SubscriptionListItem> {
  return apiPost<SubscriptionListItem, Record<string, never>>(`/subscriptions/${subscriptionId}/devices/bulk/delete`, {});
}

export type PanelSyncDirection = ApiSchema<"PanelSyncDirection">;

export type PanelSyncResult = ApiSchema<"PanelSyncResultResponse">;

export type PanelSyncDirectionStatus = ApiSchema<"PanelSyncDirectionStatusResponse">;

export type PanelSyncStatus = ApiSchema<"PanelSyncStatusResponse">;

export type PanelFieldDiff = ApiSchema<"PanelFieldDiffResponse">;

export type MissingSquad = ApiSchema<"MissingSquadResponse">;

/** a squad gone from the panel -> its replacement, null drops it */
export type SquadReplacements = Record<string, string | null>;

export type SubscriptionPanelDiff = ApiSchema<"SubscriptionPanelDiffResponse">;

export function listMissingPanelSquads(signal?: AbortSignal): Promise<{ items: MissingSquad[]; total: number }> {
  return apiGet<ApiSchema<"MissingSquadListResponse">>("/subscriptions/panel-sync/missing-squads", signal);
}

export type SubscriptionListStats = ApiSchema<"SubscriptionListStatsResponse">;

export function getSubscriptionListStats(signal?: AbortSignal): Promise<SubscriptionListStats> {
  return apiGet<SubscriptionListStats>("/subscriptions/summary", signal);
}

export async function getPanelSyncStatus(signal?: AbortSignal): Promise<PanelSyncStatus> {
  return apiGet<PanelSyncStatus>("/subscriptions/panel-sync", signal);
}

/** each direction reads its own: pull adopt_unnamed, respect_subscription_limit and create_users, push recreate_missing and delete_orphans */
export type PanelSyncOptions = Record<
  "adopt_unnamed" | "respect_subscription_limit" | "create_users" | "recreate_missing" | "delete_orphans",
  boolean
>;

export async function startPanelSync(
  direction: PanelSyncDirection,
  options: PanelSyncOptions,
  squadReplacements: SquadReplacements = {},
): Promise<PanelSyncDirectionStatus> {
  const action = direction === "FROM_PANEL" ? "pull" : "push";
  return apiPost<PanelSyncDirectionStatus, ApiSchema<"PanelSyncPullRequest"> | ApiSchema<"PanelSyncPushRequest">>(
    `/subscriptions/panel-sync/actions/${action}`,
    { ...options, squad_replacements: squadReplacements },
  );
}

export async function getSubscriptionPanelDiff(
  subscriptionId: number,
  signal?: AbortSignal,
): Promise<SubscriptionPanelDiff> {
  return apiGet<SubscriptionPanelDiff>(`/subscriptions/${subscriptionId}/panel-diff`, signal);
}

export const pullSubscriptionFromPanel = (subscriptionId: number) =>
  subscriptionAction(subscriptionId, "pull-from-panel");
export const pushSubscriptionToPanel = (subscriptionId: number, squadReplacements: SquadReplacements = {}) =>
  apiPost<SubscriptionListItem, ApiSchema<"PushToPanelRequest">>(
    `/subscriptions/${subscriptionId}/actions/push-to-panel`,
    { squad_replacements: squadReplacements },
  );
