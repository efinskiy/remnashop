import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";

export type PlanType = ApiSchema<"PlanType">;
export type PlanAvailability = ApiSchema<"PlanAvailability">;
export type PlanBadge = ApiSchema<"PlanBadge">;
export type TrafficLimitStrategy = ApiSchema<"TrafficLimitStrategy">;

export interface PlanIconValue {
  /** a Telegram custom emoji from an imported pack */
  icon_emoji_id: string | null;
  icon_emoji_fallback: string | null;
}

export const NO_PLAN_ICON: PlanIconValue = { icon_emoji_id: null, icon_emoji_fallback: null };
// lucide_dev's "box"
export const DEFAULT_PLAN_ICON: PlanIconValue = { icon_emoji_id: "5429613693287578957", icon_emoji_fallback: "📦" };

export type PlanTranslation = ApiSchema<"PlanTranslationResponse">;

export type Plan = ApiSchema<"PlanResponse">;

export function getPlan(planId: number, signal?: AbortSignal): Promise<Plan> {
  return apiGet<Plan>(`/plans/${planId}`, signal);
}

export function listPlans(signal?: AbortSignal): Promise<Plan[]> {
  return apiGet<ApiSchema<"PlanListResponse">>("/plans", signal).then((response) => response.items);
}

export type CreatePlanRequest = ApiSchema<"CreatePlanRequest">;

export function createPlan(payload: CreatePlanRequest): Promise<Plan> {
  return apiPost<Plan, CreatePlanRequest>("/plans", payload);
}

export type UpdatePlanRequest = ApiSchema<"UpdatePlanRequest">;

export function updatePlan(planId: number, payload: UpdatePlanRequest): Promise<Plan> {
  return apiPatch<Plan, UpdatePlanRequest>(`/plans/${planId}`, payload);
}

export function deletePlan(planId: number): Promise<void> {
  return apiDelete<void>(`/plans/${planId}`);
}

export function reorderPlans(planIds: number[]): Promise<Plan[]> {
  return apiPost<ApiSchema<"PlanListResponse">, ApiSchema<"ReorderPlansRequest">>("/plans/actions/reorder", { plan_ids: planIds }).then(
    (response) => response.items,
  );
}

export type SetPlanDurationsItem = ApiSchema<"PlanDurationRequest">;

export function setPlanDurations(planId: number, durations: SetPlanDurationsItem[]): Promise<Plan> {
  return apiPut<Plan, ApiSchema<"SetPlanDurationsRequest">>(`/plans/${planId}/durations`, { durations });
}

// the picker holds both, a request may leave either out
export type PlanSquads = Required<ApiSchema<"UpdatePlanSquadsRequest">>;

export function updatePlanSquads(planId: number, squads: PlanSquads): Promise<Plan> {
  return apiPut<Plan, PlanSquads>(`/plans/${planId}/squads`, squads);
}

export type UpdatePlanAccessRequest = ApiSchema<"UpdatePlanAccessRequest">;

export function updatePlanAccess(planId: number, payload: UpdatePlanAccessRequest): Promise<Plan> {
  return apiPut<Plan, UpdatePlanAccessRequest>(`/plans/${planId}/access`, payload);
}

export type UpdatePlanDiscountRequest = ApiSchema<"UpdatePlanDiscountRequest">;

export function updatePlanDiscount(planId: number, payload: UpdatePlanDiscountRequest): Promise<Plan> {
  return apiPut<Plan, UpdatePlanDiscountRequest>(`/plans/${planId}/discount`, payload);
}

export type PlanShareUrls = ApiSchema<"PlanShareUrlsResponse">;

export function getPlanShareUrls(planId: number, signal?: AbortSignal): Promise<PlanShareUrls> {
  return apiGet<PlanShareUrls>(`/plans/${planId}/share`, signal);
}
