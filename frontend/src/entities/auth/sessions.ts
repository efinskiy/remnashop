import { apiDelete, apiGet, apiPost } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";

export type Session = ApiSchema<"SessionResponse">;

export function listOwnSessions(signal?: AbortSignal): Promise<Session[]> {
  return apiGet<ApiSchema<"SessionListResponse">>("/auth/sessions", signal).then((response) => response.items);
}

export function revokeOwnSession(sessionId: number): Promise<void> {
  return apiDelete<void>(`/auth/sessions/${sessionId}`);
}

export function revokeOtherOwnSessions(): Promise<void> {
  return apiPost<void, Record<string, never>>("/auth/sessions/actions/revoke-others", {});
}

export function listUserSessions(userId: number, signal?: AbortSignal): Promise<Session[]> {
  return apiGet<ApiSchema<"SessionListResponse">>(`/users/${userId}/sessions`, signal).then((response) => response.items);
}

export function revokeUserSession(userId: number, sessionId: number): Promise<void> {
  return apiDelete<void>(`/users/${userId}/sessions/${sessionId}`);
}
