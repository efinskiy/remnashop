import { apiGet } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";

export type OverviewPeriodDays = ApiSchema<"RevenueChartResponse">["days"];

export type OverviewSubscriptions = ApiSchema<"OverviewSubscriptionsResponse">;

/** Every field but `process` is null while the process sends no heartbeat. */
export type RuntimeProcess = ApiSchema<"RuntimeProcessResponse">;

export type HostMemory = ApiSchema<"HostMemoryResponse">;

export type HostStats = ApiSchema<"HostStatsResponse">;

export type RevenueToday = ApiSchema<"RevenueTodayResponse">;

export type RecentPayment = ApiSchema<"RecentPaymentResponse">;

export type Overview = ApiSchema<"OverviewResponse">;

export type RevenueChart = ApiSchema<"RevenueChartResponse">;

export type OnlineChart = ApiSchema<"OnlineChartResponse">;

export type HourlyOnline = ApiSchema<"HourlyOnlineResponse">;

export type NodeCard = ApiSchema<"NodeCardResponse">;

export type NodesOverview = ApiSchema<"NodesOverviewResponse">;

export type ClientApps = ApiSchema<"ClientAppsResponse">;

export type AttentionKind =
  | "process_down"
  | "host_disk_full"
  | "host_memory_high"
  | "event_loop_lag"
  | "outbox_stuck"
  | "panel_unavailable"
  | "node_offline"
  | "gateway_failures"
  | "smtp_failed"
  | "backup_failed"
  | "backup_overdue"
  | "broadcast_failed"
  | "paid_not_fulfilled"
  | "panel_users_missing"
  | "stale_pending"
  | "broadcast_stalled"
  | "email_undeliverable"
  | "expiring_paid"
  | "api_token_expiring"
  | "bot_webhook"
  | "plan_squads_missing"
  | "unrated_anchor_amounts";

export type AttentionItem = ApiSchema<"AttentionItemResponse">;

export function getOverview(signal?: AbortSignal): Promise<Overview> {
  return apiGet<Overview>("/overview", signal);
}

export function getRevenueChart(days: OverviewPeriodDays, signal?: AbortSignal): Promise<RevenueChart> {
  return apiGet<RevenueChart>(`/overview/revenue?days=${days}`, signal);
}

export function getOnlineChart(days: OverviewPeriodDays, signal?: AbortSignal): Promise<OnlineChart> {
  return apiGet<OnlineChart>(`/overview/online?days=${days}`, signal);
}

export function getHourlyOnline(signal?: AbortSignal): Promise<HourlyOnline> {
  return apiGet<HourlyOnline>("/overview/online/hourly", signal);
}

export function getNodesOverview(signal?: AbortSignal): Promise<NodesOverview> {
  return apiGet<NodesOverview>("/overview/nodes", signal);
}

export function getClientApps(signal?: AbortSignal): Promise<ClientApps> {
  return apiGet<ClientApps>("/overview/client-apps", signal);
}

export type Recap = ApiSchema<"RecapResponse">;

export function getRecap(signal?: AbortSignal): Promise<Recap> {
  return apiGet<Recap>("/overview/recap", signal);
}

export function getAttention(signal?: AbortSignal): Promise<ApiSchema<"AttentionResponse">> {
  return apiGet<ApiSchema<"AttentionResponse">>("/overview/attention", signal);
}
