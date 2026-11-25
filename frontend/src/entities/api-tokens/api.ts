import { apiDelete, apiGet, apiPost } from "@shared/api/http";
import type { ListResponse } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";

export type ApiToken = ApiSchema<"ApiTokenResponse">;

export type CreatedApiToken = ApiSchema<"CreatedApiTokenResponse">;

export function listApiTokens(signal?: AbortSignal): Promise<ApiToken[]> {
  return apiGet<ListResponse<ApiToken>>("/api-tokens", signal).then((response) => response.items);
}

export function createApiToken(
  name: string,
  scopes: string[],
  expiresInDays: number,
  ipAllowlist: string[],
): Promise<CreatedApiToken> {
  return apiPost<CreatedApiToken, { name: string; scopes: string[]; expires_in_days: number; ip_allowlist: string[] }>("/api-tokens", {
    name,
    scopes,
    expires_in_days: expiresInDays,
    ip_allowlist: ipAllowlist,
  });
}

export function revokeApiToken(id: number): Promise<void> {
  return apiDelete<void>(`/api-tokens/${id}`);
}

export function issueDocsOtt(): Promise<string> {
  return apiPost<{ ott: string }, Record<string, never>>("/api-tokens/actions/issue-ott", {}).then(
    (response) => response.ott,
  );
}
