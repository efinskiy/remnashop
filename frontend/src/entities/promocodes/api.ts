import { apiDelete, apiGet, apiPatch, apiPost } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";

// mirrors CreatePromocodeRequest.code on the backend
export const PROMOCODE_CODE_MAX_LENGTH = 64;
export const PROMOCODE_CODE_PATTERN = /^[A-Z0-9_-]+$/;

export type PromocodeRewardType = ApiSchema<"PromocodeRewardType">;
export type PromocodeAvailability = ApiSchema<"PromocodeAvailability">;

export type Promocode = ApiSchema<"PromocodeResponse">;

export const DEFAULT_PAGE_SIZE = 50;
// the backend's MAX_PAGE_SIZE: a picker lists a shop's live promocodes in one page
export const PICKER_PAGE_SIZE = 200;

export interface PromocodeListFilters {
  status?: string;
  rewardType?: string;
  search?: string;
  page?: number;
  pageSize?: number;
}

export type PromocodeListPage = ApiSchema<"PromocodePageResponse">;

export function listPromocodes(filters: PromocodeListFilters = {}, signal?: AbortSignal): Promise<PromocodeListPage> {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.rewardType) params.set("reward_type", filters.rewardType);
  if (filters.search) params.set("search", filters.search);
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.pageSize ?? DEFAULT_PAGE_SIZE));

  return apiGet<PromocodeListPage>(`/promocodes?${params.toString()}`, signal);
}

export type UserPromocodeActivation = ApiSchema<"UserPromocodeActivationResponse">;

export type UserPromocodeActivationPage = ApiSchema<"UserPromocodeActivationPageResponse">;

export function listUserPromocodeActivations(
  userId: number,
  page: number,
  pageSize: number,
  signal?: AbortSignal,
): Promise<UserPromocodeActivationPage> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  return apiGet<UserPromocodeActivationPage>(`/users/${userId}/promocode-activations?${params.toString()}`, signal);
}

export type CreatePromocodeRequest = ApiSchema<"CreatePromocodeRequest">;

export function createPromocode(payload: CreatePromocodeRequest): Promise<Promocode> {
  return apiPost<Promocode, CreatePromocodeRequest>("/promocodes", payload);
}

export type UpdatePromocodeRequest = ApiSchema<"UpdatePromocodeRequest">;

export function updatePromocode(promocodeId: number, payload: UpdatePromocodeRequest): Promise<Promocode> {
  return apiPatch<Promocode, UpdatePromocodeRequest>(`/promocodes/${promocodeId}`, payload);
}

export function getPromocode(promocodeId: number, signal?: AbortSignal): Promise<Promocode> {
  return apiGet<Promocode>(`/promocodes/${promocodeId}`, signal);
}

export function deletePromocode(promocodeId: number): Promise<void> {
  return apiDelete<void>(`/promocodes/${promocodeId}`);
}

export function generatePromocodeCode(): Promise<string> {
  return apiPost<{ code: string }, Record<string, never>>("/promocodes/actions/generate-code", {}).then(
    (result) => result.code,
  );
}

export type PromocodeSummary = ApiSchema<"PromocodeSummaryResponse">;

export function getPromocodeSummary(signal?: AbortSignal): Promise<PromocodeSummary> {
  return apiGet<PromocodeSummary>("/promocodes/summary", signal);
}

export type PromocodeActivatedUser = ApiSchema<"PromocodeActivatedUserResponse">;

export type PromocodeActivatedUserPage = ApiSchema<"PromocodeActivatedUserPageResponse">;

export function listPromocodeActivatedUsers(
  promocodeId: number,
  page: number,
  pageSize: number,
  signal?: AbortSignal,
): Promise<PromocodeActivatedUserPage> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  return apiGet<PromocodeActivatedUserPage>(`/promocodes/${promocodeId}/users?${params.toString()}`, signal);
}
