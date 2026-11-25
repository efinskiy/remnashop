import { apiGet } from "@shared/api/http";
import { toIsoDate } from "@shared/lib/iso-date";
import type { Permission } from "@shared/types/rbac";
import type { ApiSchema } from "@shared/api/schemas";

export type AnalyticsPeriod =
  | { kind: "days"; days: 7 | 30 | 90 | 365 }
  | { kind: "all" }
  | { kind: "range"; from: string; to: string };

/** one per analytics tab, in tab order */
export const ANALYTICS_TAB_PERMISSIONS = {
  metrics: "ANALYTICS_VIEW",
  revenue: "ANALYTICS_REVENUE_VIEW",
  funnel: "ANALYTICS_FUNNEL_VIEW",
  trial: "ANALYTICS_TRIAL_VIEW",
  retention: "ANALYTICS_RETENTION_VIEW",
  ltv: "ANALYTICS_LTV_VIEW",
  sources: "ANALYTICS_SOURCES_VIEW",
  promocodes: "ANALYTICS_PROMOCODES_VIEW",
} as const satisfies Record<string, Permission>;

export type SourceKind = ApiSchema<"SourceKind">;
export type RevenueGranularity = ApiSchema<"RevenueResponse">["granularity"];

export type Analytics = ApiSchema<"AnalyticsResponse">;

export function periodParams(period: AnalyticsPeriod, today = new Date()): URLSearchParams {
  if (period.kind === "range") return new URLSearchParams({ period_from: period.from, period_to: period.to });
  const params = new URLSearchParams({ period_to: toIsoDate(today) });
  if (period.kind === "days") {
    const from = new Date(today.getFullYear(), today.getMonth(), today.getDate() - (period.days - 1));
    params.set("period_from", toIsoDate(from));
  }
  return params;
}

export function getAnalytics(period: AnalyticsPeriod, signal?: AbortSignal): Promise<Analytics> {
  return apiGet<Analytics>(`/analytics/overview?${periodParams(period).toString()}`, signal);
}

export type FunnelStep = ApiSchema<"FunnelStepResponse">;

export type FunnelSourceRow = ApiSchema<"FunnelSourceRowResponse">;

export type Funnel = ApiSchema<"FunnelResponse">;

export function getFunnel(period: AnalyticsPeriod, signal?: AbortSignal): Promise<Funnel> {
  return apiGet<Funnel>(`/analytics/funnel?${periodParams(period).toString()}`, signal);
}

export type Cohorts = ApiSchema<"CohortsResponse">;

export function getCohorts(signal?: AbortSignal): Promise<Cohorts> {
  return apiGet<Cohorts>("/analytics/cohorts", signal);
}

export type LtvDistribution = ApiSchema<"LtvDistributionResponse">;

export type LtvGroup = ApiSchema<"LtvGroupResponse">;

export type LtvBreakdown = ApiSchema<"LtvBreakdownResponse">;

export function getLtvDistribution(signal?: AbortSignal): Promise<LtvDistribution> {
  return apiGet<LtvDistribution>("/analytics/ltv-distribution", signal);
}

export function getLtvBreakdown(signal?: AbortSignal): Promise<LtvBreakdown> {
  return apiGet<LtvBreakdown>("/analytics/ltv-breakdown", signal);
}

export type RevenueGroup = ApiSchema<"RevenueGroupResponse">;

export type GatewayStats = ApiSchema<"GatewayStatsResponse">;

export type Revenue = ApiSchema<"RevenueResponse">;

export function getRevenue(
  period: AnalyticsPeriod,
  granularity: RevenueGranularity,
  signal?: AbortSignal,
): Promise<Revenue> {
  const params = periodParams(period);
  params.set("granularity", granularity);
  return apiGet<Revenue>(`/analytics/revenue?${params.toString()}`, signal);
}

export type Trial = ApiSchema<"TrialStatsResponse">;

export function getTrial(period: AnalyticsPeriod, signal?: AbortSignal): Promise<Trial> {
  return apiGet<Trial>(`/analytics/trial?${periodParams(period).toString()}`, signal);
}

export type Retention = ApiSchema<"RetentionResponse">;

export function getRetention(signal?: AbortSignal): Promise<Retention> {
  return apiGet<Retention>("/analytics/retention", signal);
}

export function listExpiringCustomers(
  page: number,
  pageSize: number,
  signal?: AbortSignal,
): Promise<ApiSchema<"ExpiringCustomerPageResponse">> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  return apiGet<ApiSchema<"ExpiringCustomerPageResponse">>(`/analytics/retention/expiring?${params.toString()}`, signal);
}

export type SourceRow = ApiSchema<"SourceRowResponse">;

export type Sources = ApiSchema<"SourcesResponse">;

export function getSources(period: AnalyticsPeriod, signal?: AbortSignal): Promise<Sources> {
  return apiGet<Sources>(`/analytics/sources?${periodParams(period).toString()}`, signal);
}

export type PromocodeRow = ApiSchema<"PromocodeRowResponse">;

export type PromocodeStats = ApiSchema<"PromocodeStatsResponse">;

export function getPromocodeStats(period: AnalyticsPeriod, signal?: AbortSignal): Promise<PromocodeStats> {
  return apiGet<PromocodeStats>(`/analytics/promocodes?${periodParams(period).toString()}`, signal);
}
