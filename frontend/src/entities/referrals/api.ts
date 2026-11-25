import { apiGet, apiPatch, apiPost } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";

export type ReferralAccrualStrategy = ApiSchema<"ReferralAccrualStrategy">;
export type ReferralRewardType = ApiSchema<"ReferralRewardType">;
export type ReferralRewardStrategy = ApiSchema<"ReferralRewardStrategy">;

export type ReferralLevel = 1 | 2 | 3;
/** Every level always has an amount; max_level decides which of them pay. */
export type ReferralRewardAmounts = Record<ReferralLevel, string>;

// anchor_currency: pricing's anchor: a PERCENT points reward is counted from the payment in it
// reward_amounts: keyed by level, which the generated schema types as any string
export type ReferralSettings = Omit<ApiSchema<"ReferralSettingsResponse">, "reward_amounts"> & {
  reward_amounts: ReferralRewardAmounts;
};

export function getReferralSettings(signal?: AbortSignal): Promise<ReferralSettings> {
  return apiGet<ReferralSettings>("/referrals/settings", signal);
}

export type UpdateReferralSettingsRequest = Omit<ApiSchema<"UpdateReferralSettingsRequest">, "reward_amounts"> & {
  reward_amounts?: ReferralRewardAmounts | null;
};

export function updateReferralSettings(payload: UpdateReferralSettingsRequest): Promise<ReferralSettings> {
  return apiPatch<ReferralSettings, UpdateReferralSettingsRequest>("/referrals/settings", payload);
}

export function resetReferralSettings(): Promise<ReferralSettings> {
  return apiPost<ReferralSettings, Record<string, never>>("/referrals/settings/actions/reset", {});
}

export type ReferralReward = ApiSchema<"ReferralRewardResponse">;

export type ReferralStats = Omit<ApiSchema<"ReferralStatsResponse">, "reward_amounts"> & { reward_amounts: Partial<Record<ReferralRewardType, string>> };

/** what the user's downline has paid, in the pricing anchor currency */
export type ReferralRevenue = ApiSchema<"ReferralRevenueResponse">;

export function getUserReferralRevenue(userId: number, signal?: AbortSignal): Promise<ReferralRevenue> {
  return apiGet<ReferralRevenue>(`/users/${userId}/referrals/revenue`, signal);
}

export function getUserReferralStats(userId: number, signal?: AbortSignal): Promise<ReferralStats> {
  return apiGet<ReferralStats>(`/users/${userId}/referrals`, signal);
}

export type ReferralRewardPage = ApiSchema<"ReferralRewardPageResponse">;

export function listUserReferralRewards(
  userId: number,
  page = 1,
  pageSize = REFERRALS_PAGE_SIZE,
  signal?: AbortSignal,
): Promise<ReferralRewardPage> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  return apiGet<ReferralRewardPage>(`/users/${userId}/referrals/rewards?${params.toString()}`, signal);
}

export function adjustUserPoints(userId: number, delta: string): Promise<ApiSchema<"PointsBalanceResponse">> {
  return apiPost<ApiSchema<"PointsBalanceResponse">, ApiSchema<"AdjustPointsRequest">>(`/users/${userId}/actions/adjust-points`, { delta });
}

export function adjustUserBonusDays(userId: number, delta: number): Promise<ApiSchema<"BonusDaysBalanceResponse">> {
  return apiPost<ApiSchema<"BonusDaysBalanceResponse">, ApiSchema<"AdjustBonusDaysRequest">>(`/users/${userId}/actions/adjust-bonus-days`, {
    delta,
  });
}

export function resetUserReferralCode(userId: number): Promise<ApiSchema<"ReferralCodeResponse">> {
  return apiPost<ApiSchema<"ReferralCodeResponse">, Record<string, never>>(
    `/users/${userId}/referral-code/actions/reset`,
    {},
  );
}

export const REFERRALS_PAGE_SIZE = 50;

export type ReferralUser = ApiSchema<"ReferralUserResponse">;

export type ReferralListItem = Omit<ApiSchema<"ReferralListItemResponse">, "reward_amounts"> & { reward_amounts: Partial<Record<ReferralRewardType, string>> };

export type ReferralListPage = ApiSchema<"ReferralPageResponse">;

export interface ReferralListFilters {
  level?: number;
  createdFrom?: string;
  search?: string;
  hasRewards?: boolean;
  rewardType?: ReferralRewardType;
  page?: number;
  pageSize?: number;
}

export function listReferrals(filters: ReferralListFilters = {}, signal?: AbortSignal): Promise<ReferralListPage> {
  const params = new URLSearchParams();
  if (filters.level) params.set("level", String(filters.level));
  if (filters.createdFrom) params.set("created_from", filters.createdFrom);
  if (filters.search) params.set("search", filters.search);
  if (filters.hasRewards !== undefined) params.set("has_rewards", String(filters.hasRewards));
  if (filters.rewardType) params.set("reward_type", filters.rewardType);
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.pageSize ?? REFERRALS_PAGE_SIZE));
  return apiGet<ReferralListPage>(`/referrals?${params.toString()}`, signal);
}

export type ReferralSummary = Omit<ApiSchema<"ReferralSummaryResponse">, "reward_amounts"> & { reward_amounts: Partial<Record<ReferralRewardType, string>> };

export function getReferralSummary(
  /** createdTo: the summary as it looked at that moment (later referrals and rewards left out) */
  filters: ReferralListFilters & { createdTo?: string } = {},
  signal?: AbortSignal,
): Promise<ReferralSummary> {
  const params = new URLSearchParams();
  if (filters.level) params.set("level", String(filters.level));
  if (filters.createdFrom) params.set("created_from", filters.createdFrom);
  if (filters.createdTo) params.set("created_to", filters.createdTo);
  if (filters.search) params.set("search", filters.search);
  if (filters.hasRewards !== undefined) params.set("has_rewards", String(filters.hasRewards));
  if (filters.rewardType) params.set("reward_type", filters.rewardType);
  return apiGet<ReferralSummary>(`/referrals/summary?${params.toString()}`, signal);
}

export type InvitedUser = Omit<ApiSchema<"InvitedUserResponse">, "reward_amounts"> & { reward_amounts: Partial<Record<ReferralRewardType, string>> };

export type InvitedUserPage = ApiSchema<"InvitedUserPageResponse">;

export interface InvitedUserFilters {
  level?: number;
  search?: string;
  page?: number;
  pageSize?: number;
}

export function listInvitedUsers(
  userId: number,
  filters: InvitedUserFilters = {},
  signal?: AbortSignal,
): Promise<InvitedUserPage> {
  const params = new URLSearchParams();
  if (filters.level) params.set("level", String(filters.level));
  if (filters.search) params.set("search", filters.search);
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.pageSize ?? REFERRALS_PAGE_SIZE));
  return apiGet<InvitedUserPage>(`/users/${userId}/referrals/invited?${params.toString()}`, signal);
}
