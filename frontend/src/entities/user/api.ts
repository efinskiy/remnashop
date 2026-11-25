import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";

export type CurrentUser = ApiSchema<"CurrentUserResponse">;

export type UpdateOwnProfileRequest = ApiSchema<"UpdateOwnProfileRequest">;

export function getCurrentUser(signal?: AbortSignal): Promise<CurrentUser> {
  return apiGet<CurrentUser>("/users/me", signal);
}

export function updateOwnProfile(payload: UpdateOwnProfileRequest): Promise<CurrentUser> {
  return apiPatch<CurrentUser, UpdateOwnProfileRequest>("/users/me", payload);
}

export type UserBase = ApiSchema<"UserResponse">;

export type UserListItem = ApiSchema<"UserListItemResponse">;

export const DEFAULT_PAGE_SIZE = 50;

export type UserListPage = ApiSchema<"UserPageResponse">;

export type UserSort = "created_at" | "points" | "discount" | "name" | "channels" | "subscriptions";

// exclude: live accounts only (the default); include: both; only: deleted ones
export type DeletedFilter = "exclude" | "include" | "only";

// which blacklist a blocked user is on: the manual list or external sources
export type BlockedBy = "manual" | "lists";

export interface UserListFilters {
  search?: string;
  includeStaff?: boolean;
  blockedBy?: BlockedBy;
  deleted?: DeletedFilter;
  hasSubscription?: boolean;
  isTrialAvailable?: boolean;
  sort?: UserSort;
  descending?: boolean;
  page?: number;
  pageSize?: number;
}

export interface UserListStats {
  total: number;
  subscribed: number;
  blocked: number;
  /** registrations over the last 30 days */
  total_growth: number;
  /** an expired subscription and nothing active or limited */
  churned: number;
}

export function listUsers(
  filters: UserListFilters = {},
  signal?: AbortSignal,
): Promise<UserListPage> {
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  if (filters.includeStaff) params.set("include_staff", "true");
  if (filters.blockedBy) params.set("blocked_by", filters.blockedBy);
  if (filters.deleted) params.set("deleted", filters.deleted);
  if (filters.hasSubscription !== undefined) params.set("has_subscription", String(filters.hasSubscription));
  if (filters.isTrialAvailable !== undefined) params.set("is_trial_available", String(filters.isTrialAvailable));
  if (filters.sort) params.set("sort", filters.sort);
  if (filters.descending !== undefined) params.set("descending", String(filters.descending));
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.pageSize ?? DEFAULT_PAGE_SIZE));

  return apiGet<UserListPage>(`/users?${params.toString()}`, signal);
}

export function getUser(userId: number, signal?: AbortSignal): Promise<UserListItem> {
  return apiGet<UserListItem>(`/users/${userId}`, signal);
}

export function getUserListStats(includeStaff: boolean, signal?: AbortSignal): Promise<UserListStats> {
  return apiGet<UserListStats>(`/users/summary${includeStaff ? "?include_staff=true" : ""}`, signal);
}

export function deleteUser(userId: number): Promise<void> {
  return apiDelete<void>(`/users/${userId}`);
}

export function setUserMarkup(userId: number, markupPercent: number): Promise<UserListItem> {
  return apiPatch<UserListItem, { markup_percent: number }>(`/users/${userId}/markup`, {
    markup_percent: markupPercent,
  });
}

export function setUserDiscount(
  userId: number,
  discounts: { personal_discount?: number; purchase_discount?: number },
): Promise<UserListItem> {
  return apiPatch<UserListItem, typeof discounts>(`/users/${userId}/discount`, discounts);
}

export function blockUser(userId: number): Promise<UserListItem> {
  return apiPost<UserListItem, Record<string, never>>(`/users/${userId}/actions/block`, {});
}

export function setUserTrialAvailability(userId: number, isTrialAvailable: boolean): Promise<UserListItem> {
  return apiPatch<UserListItem, { is_trial_available: boolean }>(`/users/${userId}/trial`, {
    is_trial_available: isTrialAvailable,
  });
}

/** drops the customer's bot dialog and sends them a fresh main menu */
export function resetUserBotMenu(userId: number): Promise<void> {
  return apiPost<void, Record<string, never>>(`/users/${userId}/actions/reset-bot-menu`, {});
}

export function clearEmailUndeliverable(userId: number): Promise<UserListItem> {
  return apiPost<UserListItem, Record<string, never>>(`/users/${userId}/actions/clear-email-undeliverable`, {});
}

export function unblockUser(userId: number): Promise<UserListItem> {
  return apiPost<UserListItem, Record<string, never>>(`/users/${userId}/actions/unblock`, {});
}

export type MergeSide = "source" | "target";

export type MergePreview = ApiSchema<"MergePreviewResponse">;

export function getMergePreview(targetId: number, sourceId: number, signal?: AbortSignal): Promise<MergePreview> {
  return apiGet<MergePreview>(`/users/${targetId}/merge-preview?source_id=${sourceId}`, signal);
}

export function mergeUsers(
  targetId: number,
  sourceId: number,
  choices: Record<string, MergeSide>,
  fingerprint: string,
): Promise<UserListItem> {
  return apiPost<UserListItem, { source_id: number; choices: Record<string, MergeSide>; fingerprint: string }>(
    `/users/${targetId}/actions/merge`,
    { source_id: sourceId, choices, fingerprint },
  );
}

export function bindUserTelegram(userId: number, telegramId: number): Promise<UserListItem> {
  return apiPut<UserListItem, { telegram_id: number }>(`/users/${userId}/telegram`, { telegram_id: telegramId });
}

export function unbindUserTelegram(userId: number): Promise<UserListItem> {
  return apiDelete<UserListItem>(`/users/${userId}/telegram`);
}

export type RegistrationSource = ApiSchema<"RegistrationSource">;

export interface RegistrationSnapshot {
  source: RegistrationSource;
  start_payload: string | null;
  telegram_language_code: string | null;
  telegram_is_premium: boolean | null;
  ip_address: string | null;
  user_agent: string | null;
  browser: string | null;
  landing_url: string | null;
  referer: string | null;
  utm_source: string | null;
  utm_medium: string | null;
  utm_campaign: string | null;
  utm_content: string | null;
  utm_term: string | null;
  click_id: string | null;
  platform: string | null;
  created_at: string;
}

// registration is null for accounts made before snapshots were kept
export function getUserRegistration(
  userId: number,
  signal?: AbortSignal,
): Promise<{ registration: RegistrationSnapshot | null }> {
  return apiGet<{ registration: RegistrationSnapshot | null }>(`/users/${userId}/registration`, signal);
}
