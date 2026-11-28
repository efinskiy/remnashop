import { apiGet } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";
import { todayIn } from "@shared/lib/iso-date";
import { useAsyncResource } from "@shared/lib/use-async-resource";

// one shop, one zone: loaded once per page, replaced when the owner changes it
let zone: string | null = null;
let pending: Promise<string> | null = null;

export function loadShopTimeZone(): Promise<string> {
  pending ??= apiGet<ApiSchema<"ShopTimezoneResponse">>("/settings/timezone").then(
    (response) => (zone = response.timezone),
    (error: unknown) => {
      pending = null;
      throw error;
    },
  );
  return pending;
}

export function setShopTimeZone(value: string): void {
  zone = value;
  pending = Promise.resolve(value);
}

/** The shop's today, the day the server counts in; the browser's until the zone has loaded. */
export function shopToday(): Date {
  return todayIn(zone ?? Intl.DateTimeFormat().resolvedOptions().timeZone);
}

/** True once the shop's zone is known, so a day computed from shopToday() is the server's. */
export function useShopTimeZoneReady(): boolean {
  const [state] = useAsyncResource(loadShopTimeZone);
  return state.kind !== "loading";
}
