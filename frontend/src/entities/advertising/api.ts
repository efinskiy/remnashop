import { apiDelete, apiGet, apiGetRaw, apiPatch, apiPost } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";

export type AdLinkChannel = ApiSchema<"AdLinkChannel">;

export type AdLink = ApiSchema<"AdLinkResponse">;

export const DEFAULT_PAGE_SIZE = 50;

// mirror CreateAdLinkRequest.code in backend/app/modules/advertising/api/schemas.py
export const AD_LINK_CODE_PATTERN = /^[A-Za-z0-9_-]+$/;
export const AD_LINK_CODE_MAX_LENGTH = 48;

export type AdLinkListPage = ApiSchema<"AdLinkPageResponse">;

export interface AdLinkListFilters {
  isActive?: boolean;
  page?: number;
  pageSize?: number;
}

export function listAdLinks(
  filters: AdLinkListFilters = {},
  signal?: AbortSignal,
): Promise<AdLinkListPage> {
  const params = new URLSearchParams();
  if (filters.isActive !== undefined) params.set("is_active", String(filters.isActive));
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.pageSize ?? DEFAULT_PAGE_SIZE));

  return apiGet<AdLinkListPage>(`/advertising/links?${params.toString()}`, signal);
}

export type CreateAdLinkRequest = ApiSchema<"CreateAdLinkRequest">;

export function createAdLink(payload: CreateAdLinkRequest): Promise<AdLink> {
  return apiPost<AdLink, CreateAdLinkRequest>("/advertising/links", payload);
}

// promocode_id: null unlinks the promocode
export type UpdateAdLinkRequest = ApiSchema<"UpdateAdLinkRequest">;

export function updateAdLink(adLinkId: number, payload: UpdateAdLinkRequest): Promise<AdLink> {
  return apiPatch<AdLink, UpdateAdLinkRequest>(`/advertising/links/${adLinkId}`, payload);
}

export function deleteAdLink(adLinkId: number): Promise<void> {
  return apiDelete<void>(`/advertising/links/${adLinkId}`);
}

export function generateAdLinkCode(): Promise<string> {
  return apiPost<ApiSchema<"GeneratedAdLinkCodeResponse">, Record<string, never>>("/advertising/links/actions/generate-code", {}).then(
    (result) => result.code,
  );
}

export type AdLinkStats = Omit<ApiSchema<"AdLinkStatsResponse">, "attributions_by_channel"> & { attributions_by_channel: Partial<Record<AdLinkChannel, number>> };

// createdFrom: ISO timestamp; counts only attributions made since then.
export function getAdLinkStats(
  adLinkId: number,
  createdFrom?: string,
  signal?: AbortSignal,
): Promise<AdLinkStats> {
  const params = new URLSearchParams();
  if (createdFrom) params.set("created_from", createdFrom);
  return apiGet<AdLinkStats>(`/advertising/links/${adLinkId}/stats?${params.toString()}`, signal);
}

export type AdLinkPayout = ApiSchema<"AdLinkPayoutResponse">;

// paidFrom/paidTo: "YYYY-MM-DD", both days included
export function getAdLinkPayout(
  adLinkId: number,
  paidFrom: string,
  paidTo: string,
  signal?: AbortSignal,
): Promise<AdLinkPayout> {
  const params = new URLSearchParams({ paid_from: paidFrom, paid_to: paidTo });
  return apiGet<AdLinkPayout>(`/advertising/links/${adLinkId}/payout?${params.toString()}`, signal);
}

export type AdvertisingSummary = Omit<ApiSchema<"AdvertisingSummaryResponse">, "attributions_by_channel"> & { attributions_by_channel: Partial<Record<AdLinkChannel, number>> };

export function getAdvertisingSummary(
  /** createdTo: the summary as it looked at that moment (later attributions and payments left out) */
  filters: { isActive?: boolean; createdFrom?: string; createdTo?: string },
  signal?: AbortSignal,
): Promise<AdvertisingSummary> {
  const params = new URLSearchParams();
  if (filters.isActive !== undefined) params.set("is_active", String(filters.isActive));
  if (filters.createdFrom) params.set("created_from", filters.createdFrom);
  if (filters.createdTo) params.set("created_to", filters.createdTo);
  return apiGet<AdvertisingSummary>(`/advertising/summary?${params.toString()}`, signal);
}

export type AttributedUser = ApiSchema<"AttributedUserResponse">;

export type AttributedUserPage = ApiSchema<"AttributedUserPageResponse">;

export function listAdLinkAttributedUsers(
  adLinkId: number,
  page = 1,
  pageSize = DEFAULT_PAGE_SIZE,
  signal?: AbortSignal,
): Promise<AttributedUserPage> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  return apiGet<AttributedUserPage>(`/advertising/links/${adLinkId}/users?${params.toString()}`, signal);
}

export interface UserAdAttribution {
  ad_link_id: number;
  name: string;
  code: string;
  channel: AdLinkChannel;
  attributed_at: string;
}

export function getUserAdAttribution(userId: number, signal?: AbortSignal): Promise<UserAdAttribution | null> {
  return apiGet<ApiSchema<"UserAdAttributionResponse">>(`/users/${userId}/ad-attribution`, signal).then(
    (response) => response.attribution,
  );
}

// null = channel not allowed on the link, or its base URL isn't configured
export type AdLinkShareUrls = ApiSchema<"AdLinkShareUrlsResponse">;

export function getAdLinkShareUrls(adLinkId: number, signal?: AbortSignal): Promise<AdLinkShareUrls> {
  return apiGet<AdLinkShareUrls>(`/advertising/links/${adLinkId}/share`, signal);
}

export async function fetchAdLinkQr(adLinkId: number, channel: AdLinkChannel): Promise<Blob> {
  return (await apiGetRaw(`/advertising/links/${adLinkId}/qr?channel=${channel}`)).blob();
}
