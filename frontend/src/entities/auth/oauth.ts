import { apiDelete, apiGet, apiPost } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";

export type OAuthProvider = "github" | "telegram" | "oidc";

export const OAUTH_PROVIDERS: OAuthProvider[] = ["github", "telegram", "oidc"];

/** sign-in and account linking both answer with the provider's URL */
export interface OAuthAuthorizeResult {
  url: string;
}

export interface OAuthCallbackPayload {
  code: string;
  state: string;
}

export type OAuthIdentity = ApiSchema<"OAuthIdentityResponse">;

export function getOAuthLoginAuthorizeUrl(provider: OAuthProvider): Promise<OAuthAuthorizeResult> {
  return apiPost<ApiSchema<"OAuthAuthorizeResponse">, ApiSchema<"OAuthAuthorizeRequest">>(`/auth/oauth/${provider}/authorize`, {
    audience: "dashboard",
  });
}

export function oauthLoginCallback(
  provider: OAuthProvider,
  payload: OAuthCallbackPayload,
): Promise<{ access_token: string }> {
  // the same route signs in to the cabinet, so it answers with more than the dashboard needs
  return apiPost<ApiSchema<"OAuthSignInResponse">, ApiSchema<"OAuthCallbackRequest">>(`/auth/oauth/${provider}/callback`, payload);
}

export function listConnectedAccounts(signal?: AbortSignal): Promise<OAuthIdentity[]> {
  return apiGet<ApiSchema<"OAuthIdentityListResponse">>("/auth/oauth", signal).then((response) => response.items);
}

export function getOAuthConnectAuthorizeUrl(
  provider: OAuthProvider,
): Promise<OAuthAuthorizeResult> {
  return apiPost<ApiSchema<"OAuthConnectAuthorizeResponse">, Record<string, never>>(`/auth/oauth/${provider}/connect/authorize`, {});
}

export function oauthConnectCallback(
  provider: OAuthProvider,
  payload: OAuthCallbackPayload,
): Promise<OAuthIdentity> {
  return apiPost<OAuthIdentity, ApiSchema<"OAuthConnectCallbackRequest">>(
    `/auth/oauth/${provider}/connect/callback`,
    payload,
  );
}

export function disconnectOAuth(provider: OAuthProvider): Promise<void> {
  return apiDelete<void>(`/auth/oauth/${provider}`);
}
