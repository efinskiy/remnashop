import { apiGet, apiPost } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";

export type AuthStatus = ApiSchema<"StatusResponse">;

export type AuthResult = ApiSchema<"AuthResponse">;

export type BootstrapOwnerPayload = ApiSchema<"BootstrapRequest">;

export type LoginPayload = ApiSchema<"LoginRequest">;

export function getAuthStatus(signal?: AbortSignal): Promise<AuthStatus> {
  return apiGet<AuthStatus>("/auth/status", signal);
}

export function bootstrapOwner(payload: BootstrapOwnerPayload): Promise<AuthResult> {
  return apiPost<AuthResult, BootstrapOwnerPayload>("/auth/bootstrap", payload);
}

export function login(payload: LoginPayload): Promise<AuthResult> {
  return apiPost<AuthResult, LoginPayload>("/auth/login", payload);
}
