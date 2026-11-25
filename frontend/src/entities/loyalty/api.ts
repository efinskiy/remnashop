import { apiGet, apiPatch, apiPost, apiPut } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";

export type LoyaltySettings = ApiSchema<"LoyaltySettingsResponse">;

export type SaveLoyaltySettingsRequest = Omit<LoyaltySettings, "currency">;

export type UserLoyalty = ApiSchema<"UserLoyaltyResponse">;

export function getLoyaltySettings(signal?: AbortSignal): Promise<LoyaltySettings> {
  return apiGet<LoyaltySettings>("/loyalty/settings", signal);
}

export function saveLoyaltySettings(payload: SaveLoyaltySettingsRequest): Promise<LoyaltySettings> {
  return apiPut<LoyaltySettings, ApiSchema<"LoyaltySettingsRequest">>("/loyalty/settings", payload);
}

export function resetLoyaltySettings(): Promise<LoyaltySettings> {
  return apiPost<LoyaltySettings, Record<string, never>>("/loyalty/settings/actions/reset", {});
}

export function getUserLoyalty(userId: number, signal?: AbortSignal): Promise<UserLoyalty> {
  return apiGet<UserLoyalty>(`/users/${userId}/loyalty`, signal);
}

export function setUserLoyaltyExcluded(userId: number, excluded: boolean): Promise<UserLoyalty> {
  return apiPatch<UserLoyalty, ApiSchema<"UserLoyaltyRequest">>(`/users/${userId}/loyalty`, { excluded });
}
