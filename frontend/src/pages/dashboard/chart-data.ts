import type { OverviewPeriodDays } from "@entities/overview/api";
import { parseIsoDate, toIsoDate } from "@shared/lib/iso-date";
import { useAsyncResource, type AsyncState } from "@shared/lib/use-async-resource";

// each chart card owns its period: refetches on its own pill switch or a global refresh
export function useChart<T>(
  fetchChart: (days: OverviewPeriodDays, signal: AbortSignal) => Promise<T>,
  days: OverviewPeriodDays,
  refreshKey: number,
): AsyncState<T> {
  const [state] = useAsyncResource((signal) => fetchChart(days, signal), {
    deps: [fetchChart, days, refreshKey],
    keepData: true,
  });
  return state;
}

export function fillDailySeries<T extends { day: string }>(
  sparse: T[],
  days: number,
  emptyValue: (day: string) => T,
  // the online chart's peaks are stored per UTC day
  utc = false,
): T[] {
  const byDay = new Map(sparse.map((item) => [item.day, item]));
  const result: T[] = [];
  const today = new Date();
  for (let i = days - 1; i >= 0; i--) {
    const day = utc
      ? new Date(Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate() - i))
      : new Date(today.getFullYear(), today.getMonth(), today.getDate() - i);
    const key = utc ? day.toISOString().slice(0, 10) : toIsoDate(day);
    result.push(byDay.get(key) ?? emptyValue(key));
  }
  return result;
}

export function formatChartDay(iso: string, language: string): string {
  return parseIsoDate(iso)?.toLocaleDateString(language, { day: "2-digit", month: "2-digit" }) ?? iso;
}

/** The tooltip's day: "4 ноября" / "November 4". */
export function formatChartDayLong(iso: string, language: string): string {
  return parseIsoDate(iso)?.toLocaleDateString(language, { day: "numeric", month: "long" }) ?? iso;
}

// theme tokens, not hex: --color-primary follows the dashboard's appearance settings
export const CHART_TICK = { fill: "var(--color-muted-foreground)", fontSize: 12 };
