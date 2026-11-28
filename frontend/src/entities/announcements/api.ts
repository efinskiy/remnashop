import { apiGet, apiPost } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";

export type Announcement = ApiSchema<"AnnouncementResponse">;

export function listAnnouncements(signal?: AbortSignal): Promise<ApiSchema<"AnnouncementListResponse">> {
  return apiGet<ApiSchema<"AnnouncementListResponse">>("/announcements", signal);
}

export function markAnnouncementsSeen(ids: string[]): Promise<void> {
  return apiPost<void, ApiSchema<"AnnouncementIdsRequest">>("/announcements/actions/mark-seen", { ids });
}

export function dismissAnnouncements(ids: string[]): Promise<void> {
  return apiPost<void, ApiSchema<"AnnouncementIdsRequest">>("/announcements/actions/dismiss", { ids });
}

/** The maintainer writes each text per locale; fall back to English, then to whatever exists. */
export function localized(map: Record<string, string>, language: string): string {
  return map[language] ?? map.en ?? Object.values(map)[0] ?? "";
}
