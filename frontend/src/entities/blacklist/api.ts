import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";

export type BlacklistKind = ApiSchema<"BlacklistKind">;

export type Blacklist = ApiSchema<"BlacklistResponse">;

export type BlacklistSource = ApiSchema<"BlacklistSourceResponse">;

export function getBlacklist(signal?: AbortSignal): Promise<Blacklist> {
  return apiGet<Blacklist>("/blacklist", signal);
}

function entryPath(kind: BlacklistKind, value: string): string {
  return `/blacklist/entries/${kind}/${encodeURIComponent(value)}`;
}

export function addBlacklistEntry(kind: BlacklistKind, value: string): Promise<Blacklist> {
  return apiPut<Blacklist, Record<string, never>>(entryPath(kind, value), {});
}

export function removeBlacklistEntry(kind: BlacklistKind, value: string): Promise<Blacklist> {
  return apiDelete<Blacklist>(entryPath(kind, value));
}

export function listBlacklistSources(signal?: AbortSignal): Promise<BlacklistSource[]> {
  return apiGet<ApiSchema<"BlacklistSourceListResponse">>("/blacklist/sources", signal).then((response) => response.items);
}

export function addBlacklistSource(url: string, name?: string): Promise<BlacklistSource> {
  return apiPost<BlacklistSource, ApiSchema<"AddSourceRequest">>("/blacklist/sources", {
    url,
    name,
  });
}

export function removeBlacklistSource(id: number): Promise<void> {
  return apiDelete<void>(`/blacklist/sources/${id}`);
}

export function updateBlacklistSource(id: number, enabled: boolean): Promise<BlacklistSource> {
  return apiPatch<BlacklistSource, ApiSchema<"UpdateSourceRequest">>(`/blacklist/sources/${id}`, { enabled });
}

export function syncBlacklistSources(): Promise<void> {
  return apiPost<void, Record<string, never>>("/blacklist/sources/actions/sync", {});
}

// source_id: null = the manual list
export type BlacklistOrigin = ApiSchema<"BlacklistOriginResponse">;

export type BlacklistMatchUser = ApiSchema<"UserResponse">;

export type BlacklistMatch = ApiSchema<"BlacklistMatchResponse">;

export type BlacklistMatchPage = ApiSchema<"BlacklistMatchPageResponse">;

export interface BlacklistMatchFilters {
  search?: string;
  origin?: ApiSchema<"BlacklistMatchOrigin">;
  page: number;
  pageSize: number;
}

export function listBlacklistMatches(
  filters: BlacklistMatchFilters,
  signal?: AbortSignal,
): Promise<BlacklistMatchPage> {
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  if (filters.origin) params.set("origin", filters.origin);
  params.set("page", String(filters.page));
  params.set("page_size", String(filters.pageSize));

  return apiGet<BlacklistMatchPage>(`/users/blacklist-matches?${params.toString()}`, signal);
}

// Drops the matched users' manual entries too; source-list matches are re-blocked on the next reconcile.
export function unblockBlacklistMatches(): Promise<ApiSchema<"UnblockBlacklistMatchesResponse">> {
  return apiPost<ApiSchema<"UnblockBlacklistMatchesResponse">, Record<string, never>>("/users/bulk/unblock-blacklist-matches", {});
}
