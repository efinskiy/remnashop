import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";

export type Locale = ApiSchema<"Locale">;

export type ActiveLocalesResult = ApiSchema<"ActiveLocalesResponse">;

export type TranslationEntry = ApiSchema<"TranslationEntryResponse">;

export function listActiveLocales(signal?: AbortSignal): Promise<ActiveLocalesResult> {
  return apiGet<ActiveLocalesResult>("/settings/locales", signal);
}

export function addLocale(locale: Locale): Promise<ActiveLocalesResult> {
  return apiPut<ActiveLocalesResult, Record<string, never>>(`/settings/locales/${locale}`, {});
}

export function removeLocale(locale: Locale): Promise<ActiveLocalesResult> {
  return apiDelete<ActiveLocalesResult>(`/settings/locales/${locale}`);
}

export function setDefaultLocale(locale: Locale): Promise<ActiveLocalesResult> {
  return apiPatch<ActiveLocalesResult, ApiSchema<"UpdateLocalesRequest">>("/settings/locales", { default: locale });
}

export function listTranslations(signal?: AbortSignal): Promise<TranslationEntry[]> {
  return apiGet<ApiSchema<"TranslationEntryListResponse">>("/translations", signal).then((response) => response.items);
}

export function updateTranslation(
  locale: string,
  messageId: string,
  attributeId: string,
  value: string,
): Promise<TranslationEntry> {
  const query = attributeId ? `?attribute_id=${encodeURIComponent(attributeId)}` : "";
  return apiPut<TranslationEntry, ApiSchema<"UpdateTranslationRequest">>(
    `/translations/${locale}/${messageId}${query}`,
    { value },
  );
}

export function resetTranslation(
  locale: string,
  messageId: string,
  attributeId: string,
): Promise<TranslationEntry> {
  const query = attributeId ? `?attribute_id=${encodeURIComponent(attributeId)}` : "";
  return apiPost<TranslationEntry, Record<string, never>>(
    `/translations/${locale}/${messageId}/actions/reset${query}`,
    {},
  );
}

export interface TranslationsExportPayload {
  version: number;
  texts: { locale: string; message_id: string; attribute_id: string; value: string }[];
}

export type TranslationsImportResult = ApiSchema<"TranslationsImportResponse">;

export function exportTranslations(): Promise<TranslationsExportPayload> {
  return apiGet<ApiSchema<"TranslationsExportResponse">>("/translations/export");
}

export function importTranslations(
  payload: TranslationsExportPayload,
): Promise<TranslationsImportResult> {
  return apiPost<TranslationsImportResult, TranslationsExportPayload>(
    "/translations/actions/import",
    payload,
  );
}

export function resetAllTranslations(): Promise<TranslationEntry[]> {
  return apiPost<ApiSchema<"TranslationEntryListResponse">, Record<string, never>>(
    "/translations/actions/reset-all",
    {},
  ).then((response) => response.items);
}
