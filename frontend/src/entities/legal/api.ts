import { apiDelete, apiGet, apiPatch, apiPut } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";

export type LegalKind = ApiSchema<"LegalDocumentKind">;
export type LegalChannel = ApiSchema<"PurchaseChannel">;

export type LegalText = ApiSchema<"LegalTextResponse">;

export type LegalDocument = ApiSchema<"LegalDocumentItemResponse">;

type LegalDocumentFlags = Omit<LegalDocument, "texts" | "templates">;

export type LegalDocumentsResponse = ApiSchema<"LegalDocumentsResponse">;

export type LegalAcceptance = ApiSchema<"LegalAcceptanceResponse">;

export const LEGAL_KINDS: LegalKind[] = ["OFFER", "USER_AGREEMENT", "PRIVACY_POLICY"];

export function listLegalDocuments(signal?: AbortSignal): Promise<LegalDocumentsResponse> {
  return apiGet<LegalDocumentsResponse>("/legal-documents", signal);
}

export function updateLegalDocument(
  kind: LegalKind,
  payload: { show_in_bot?: boolean; show_in_cabinet?: boolean },
): Promise<LegalDocumentFlags> {
  return apiPatch<ApiSchema<"LegalDocumentResponse">, ApiSchema<"UpdateLegalDocumentRequest">>(`/legal-documents/${kind}`, payload);
}

function textPath(kind: LegalKind, locale: string, channel: LegalChannel | null): string {
  return `/legal-documents/${kind}/${locale}${channel ? `?channel=${channel}` : ""}`;
}

export function setLegalText(
  kind: LegalKind,
  locale: string,
  channel: LegalChannel | null,
  payload: ApiSchema<"LegalTextRequest">,
): Promise<LegalText> {
  return apiPut<LegalText, ApiSchema<"LegalTextRequest">>(textPath(kind, locale, channel), payload);
}

export function removeLegalText(kind: LegalKind, locale: string, channel: LegalChannel | null): Promise<null> {
  return apiDelete<null>(textPath(kind, locale, channel));
}

export function listUserLegalAcceptances(
  userId: number,
  signal?: AbortSignal,
): Promise<{ items: LegalAcceptance[]; total: number }> {
  return apiGet<ApiSchema<"LegalAcceptancesResponse">>(`/users/${userId}/legal-acceptances`, signal);
}
