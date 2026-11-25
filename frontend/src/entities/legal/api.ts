import { apiDelete, apiGet, apiPatch, apiPut } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";

export type LegalKind = ApiSchema<"LegalDocumentKind">;
export type LegalChannel = ApiSchema<"PurchaseChannel">;

export type LegalText = ApiSchema<"LegalTextResponse">;

export type LegalDocument = ApiSchema<"LegalDocumentItemResponse">;

type LegalDocumentFlags = Omit<LegalDocument, "texts" | "templates">;

export type LegalDocumentsResponse = ApiSchema<"LegalDocumentsResponse">;

export interface LegalAcceptance {
  id: number;
  kind: LegalKind;
  locale: string;
  channel: LegalChannel;
  trigger: "SIGN_UP" | "PAYMENT";
  transaction_id: number | null;
  accepted_at: string;
  revision_id: number;
  title: string;
}

export const LEGAL_KINDS: LegalKind[] = ["OFFER", "USER_AGREEMENT", "PRIVACY_POLICY"];

export function listLegalDocuments(signal?: AbortSignal): Promise<LegalDocumentsResponse> {
  return apiGet<LegalDocumentsResponse>("/legal-documents", signal);
}

export function updateLegalDocument(
  kind: LegalKind,
  payload: { show_in_bot?: boolean; show_in_cabinet?: boolean },
): Promise<LegalDocumentFlags> {
  return apiPatch<LegalDocumentFlags, typeof payload>(`/legal-documents/${kind}`, payload);
}

function textPath(kind: LegalKind, locale: string, channel: LegalChannel | null): string {
  return `/legal-documents/${kind}/${locale}${channel ? `?channel=${channel}` : ""}`;
}

export function setLegalText(
  kind: LegalKind,
  locale: string,
  channel: LegalChannel | null,
  payload: { title: string; body: string; requires_reacceptance: boolean },
): Promise<LegalText> {
  return apiPut<LegalText, typeof payload>(textPath(kind, locale, channel), payload);
}

export function removeLegalText(kind: LegalKind, locale: string, channel: LegalChannel | null): Promise<null> {
  return apiDelete<null>(textPath(kind, locale, channel));
}

export function listUserLegalAcceptances(
  userId: number,
  signal?: AbortSignal,
): Promise<{ items: LegalAcceptance[]; total: number }> {
  return apiGet<{ items: LegalAcceptance[]; total: number }>(`/users/${userId}/legal-acceptances`, signal);
}
