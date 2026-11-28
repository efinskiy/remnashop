export function toIsoDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function parseIsoDate(value: string): Date | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) return null;
  return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
}

// a picked day range as an instant range: both bounds are local midnights,
// the end one the day after the picked last day
export function startToIso(day: string): string | null {
  return parseIsoDate(day)?.toISOString() ?? null;
}

export function lastDayToIso(day: string): string | null {
  const date = parseIsoDate(day);
  if (!date) return null;
  date.setDate(date.getDate() + 1);
  return date.toISOString();
}

/** The picked day an exclusive end instant (or an end-of-day one) falls on, in local time. */
export function isoToLastDay(iso: string | null): string {
  return iso ? toIsoDate(new Date(new Date(iso).getTime() - 1)) : "";
}

/** The last millisecond of a picked local day: an inclusive end that still displays as that day. */
export function endOfDayToIso(day: string): string | null {
  const end = lastDayToIso(day);
  return end ? new Date(new Date(end).getTime() - 1).toISOString() : null;
}

/** Today's calendar day in `timeZone`, as a local-midnight Date; the browser's own day for a zone it doesn't know. */
export function todayIn(timeZone: string, now = new Date()): Date {
  try {
    const parts = new Intl.DateTimeFormat("en-US", { timeZone, year: "numeric", month: "numeric", day: "numeric" }).formatToParts(now);
    const part = (type: Intl.DateTimeFormatPartTypes) => Number(parts.find((p) => p.type === type)?.value);
    return new Date(part("year"), part("month") - 1, part("day"));
  } catch {
    return new Date(now.getFullYear(), now.getMonth(), now.getDate());
  }
}
