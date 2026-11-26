import { apiGet, apiPost } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";

export const DEFAULT_PAGE_SIZE = 50;

export type EventLogEntry = ApiSchema<"EventLogEntryResponse">;

// `location.state` for /dashboard/events: opens that entry's detail dialog on arrival
export interface EventLogLocationState {
  entry: EventLogEntry;
}

export type EventLogPage = ApiSchema<"EventLogPageResponse">;

export interface EventLogFilters {
  category?: string;
  actorId?: number;
  /** the account the event was about */
  targetId?: number;
  eventType?: string;
  search?: string;
  occurredFrom?: string;
  occurredTo?: string;
  /** keyset cursor: entries listed after this one */
  beforeId?: number;
  page?: number;
  pageSize?: number;
}

export function listEventLog(
  filters: EventLogFilters = {},
  signal?: AbortSignal,
): Promise<EventLogPage> {
  const params = new URLSearchParams();
  if (filters.category) params.set("category", filters.category);
  if (filters.actorId !== undefined) params.set("actor_id", String(filters.actorId));
  if (filters.targetId !== undefined) params.set("target_id", String(filters.targetId));
  if (filters.eventType) params.set("event_type", filters.eventType);
  if (filters.search) params.set("search", filters.search);
  if (filters.occurredFrom) params.set("occurred_from", filters.occurredFrom);
  if (filters.occurredTo) params.set("occurred_to", filters.occurredTo);
  if (filters.beforeId !== undefined) params.set("before_id", String(filters.beforeId));
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.pageSize ?? DEFAULT_PAGE_SIZE));

  return apiGet<EventLogPage>(`/events?${params.toString()}`, signal);
}

/** "Load more" over a live log: continues after the last row on screen, so new entries don't repeat it. */
export async function listEventLogAfter(
  filters: Omit<EventLogFilters, "beforeId" | "page">,
  loaded: EventLogEntry[] = [],
  signal?: AbortSignal,
): Promise<EventLogPage> {
  const page = await listEventLog({ ...filters, beforeId: loaded.at(-1)?.id }, signal);
  return { items: page.items, total: loaded.length + page.total };
}

export type Notifications = ApiSchema<"NotificationsResponse">;

export function getNotifications(signal?: AbortSignal): Promise<Notifications> {
  return apiGet<Notifications>("/events/notifications", signal);
}

export function markNotificationsRead(): Promise<void> {
  return apiPost<void, Record<string, never>>("/events/notifications/actions/mark-read", {});
}

export function clearNotifications(): Promise<void> {
  return apiPost<void, Record<string, never>>("/events/notifications/actions/clear", {});
}

export function retryPoisonedOutbox(): Promise<ApiSchema<"OutboxRetryResponse">> {
  return apiPost<ApiSchema<"OutboxRetryResponse">, Record<string, never>>("/events/outbox/actions/retry", {});
}
