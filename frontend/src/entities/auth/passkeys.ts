import { apiDelete, apiGet, apiPatch, apiPost } from "@shared/api/http";

import type { AuthResult } from "./api";
import type { ApiSchema } from "@shared/api/schemas";

export type Passkey = ApiSchema<"PasskeyResponse">;

export function getPasskeys(signal?: AbortSignal): Promise<Passkey[]> {
  return apiGet<ApiSchema<"PasskeyListResponse">>("/auth/passkeys", signal).then((response) => response.items);
}

export function getPasskeyRegistrationOptions(
  signal?: AbortSignal,
): Promise<Record<string, unknown>> {
  return apiGet<Record<string, unknown>>("/auth/passkeys/register/options", signal);
}

export function verifyPasskeyRegistration(
  credential: Record<string, unknown>,
  name: string | null,
): Promise<Passkey> {
  return apiPost<Passkey, ApiSchema<"VerifyPasskeyRegistrationRequest">>(
    "/auth/passkeys/register/verify",
    { credential, name },
  );
}

export function renamePasskey(id: number, name: string): Promise<Passkey> {
  return apiPatch<Passkey, ApiSchema<"RenamePasskeyRequest">>(`/auth/passkeys/${id}`, { name });
}

export function deletePasskey(id: number): Promise<void> {
  return apiDelete<void>(`/auth/passkeys/${id}`);
}

export function getPasskeyAuthenticationOptions(): Promise<Record<string, unknown>> {
  return apiGet<Record<string, unknown>>("/auth/passkeys/authenticate/options");
}

export function verifyPasskeyAuthentication(
  credential: Record<string, unknown>,
): Promise<AuthResult> {
  return apiPost<AuthResult, ApiSchema<"VerifyPasskeyAuthenticationRequest">>(
    "/auth/passkeys/authenticate/verify",
    { credential },
  );
}
