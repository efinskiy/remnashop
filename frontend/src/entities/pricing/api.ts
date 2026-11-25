import type { TFunction } from "i18next";

import { apiGet, apiPost, apiPut } from "@shared/api/http";
import { formatDuration } from "@shared/lib/duration";
import type { ApiSchema } from "@shared/api/schemas";

// Decimals arrive as strings (pydantic v2's JSON mode) and stay strings, so
// a round-trip through <input type="number"> loses no precision.

export type Currency = ApiSchema<"Currency">;
export const CURRENCIES: readonly Currency[] = ["USD", "XTR", "RUB"];
export type RoundingMode = ApiSchema<"RoundingMode">;
export type BulkAdjustScope = ApiSchema<"PriceAdjustScope">;

export type CurrencyRate = ApiSchema<"CurrencyRateResponse">;

export type PriceBookCell = ApiSchema<"PriceBookCellResponse">;

export type PriceBookRow = ApiSchema<"PriceBookRowResponse">;

export type PriceBook = ApiSchema<"PriceBookResponse">;

// loyalty_thresholds: filled only for an anchor switch
export type PricingDiff = ApiSchema<"PricingDiffResponse">;

export function getPriceBook(signal?: AbortSignal): Promise<PriceBook> {
  return apiGet<PriceBook>("/pricing/book", signal);
}

export type UpdateCurrencyRateBody = ApiSchema<"UpdateCurrencyRateRequest">;

export function updateCurrencyRate(currency: Currency, body: UpdateCurrencyRateBody): Promise<PriceBook> {
  return apiPut<PriceBook, UpdateCurrencyRateBody>(`/pricing/rates/${currency}`, body);
}

export function switchAnchorCurrency(newAnchor: Currency): Promise<PriceBook> {
  return apiPost<PriceBook, { new_anchor: Currency }>("/pricing/actions/switch-anchor", { new_anchor: newAnchor });
}

export type PriceAdjustMode = ApiSchema<"PriceAdjustMode">;
export type PinnedPriceAction = ApiSchema<"PinnedPriceAction">;

export type AdjustBasePricesBody = ApiSchema<"AdjustBasePricesRequest">;

export type PreviewPricingChangeBody =
  | { rate: UpdateCurrencyRateBody & { currency: Currency } }
  | { anchor: Currency }
  | { adjust: AdjustBasePricesBody };

export function previewPricingChange(body: PreviewPricingChangeBody): Promise<PricingDiff> {
  return apiPost<PricingDiff, PreviewPricingChangeBody>("/pricing/actions/preview", body);
}

export function adjustBasePrices(body: AdjustBasePricesBody): Promise<PriceBook> {
  return apiPost<PriceBook, AdjustBasePricesBody>("/pricing/actions/adjust-base-prices", body);
}

// built whole by the matrix, every list present
export type SetMatrixPricesBody = Required<ApiSchema<"SetMatrixPricesRequest">>;

/** Every edit of the matrix in one transaction: all of them land, or none. */
export function setMatrixPrices(body: SetMatrixPricesBody): Promise<PriceBook> {
  return apiPost<PriceBook, SetMatrixPricesBody>("/pricing/bulk/set-prices", body);
}

/** "Стандарт · 30 дн." for a plan duration, just the name for an add-on. */
export function pricingRowLabel(
  row: { name: string; days: number | null },
  t: TFunction,
): string {
  return row.days === null ? row.name : `${row.name} · ${formatDuration(row.days, t)}`;
}
