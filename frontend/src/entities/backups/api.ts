import { apiDelete, apiGet, apiGetRaw, apiPatch, apiPost } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";

export type BackupKind = ApiSchema<"BackupKind">;
export type BackupRunStatus = ApiSchema<"BackupRunStatus">;

export type BackupSettings = ApiSchema<"BackupSettingsResponse">;

export function getBackupSettings(signal?: AbortSignal): Promise<BackupSettings> {
  return apiGet<BackupSettings>("/backups/settings", signal);
}

export type UpdateBackupSettingsRequest = ApiSchema<"UpdateBackupSettingsRequest">;

export function updateBackupSettings(payload: UpdateBackupSettingsRequest): Promise<BackupSettings> {
  return apiPatch<BackupSettings, UpdateBackupSettingsRequest>("/backups/settings", payload);
}

// Drops the stored row, so every field reads back as its default.
export function resetBackupSettings(): Promise<BackupSettings> {
  return apiPost<BackupSettings, Record<string, never>>("/backups/settings/actions/reset", {});
}

export type BackupRun = ApiSchema<"BackupRunResponse">;

export const DEFAULT_PAGE_SIZE = 50;

export type BackupRunListPage = ApiSchema<"BackupRunPageResponse">;

export interface BackupRunListFilters {
  kind?: BackupKind;
  status?: BackupRunStatus;
  page?: number;
  pageSize?: number;
}

export function listBackupRuns(
  filters: BackupRunListFilters = {},
  signal?: AbortSignal,
): Promise<BackupRunListPage> {
  const params = new URLSearchParams();
  if (filters.kind) params.set("kind", filters.kind);
  if (filters.status) params.set("status", filters.status);
  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.pageSize ?? DEFAULT_PAGE_SIZE));

  return apiGet<BackupRunListPage>(`/backups/runs?${params.toString()}`, signal);
}

export type BackupStats = ApiSchema<"BackupStatsResponse">;

export function getBackupStats(signal?: AbortSignal): Promise<BackupStats> {
  return apiGet<BackupStats>("/backups/summary", signal);
}

export function cancelBackupRun(runId: number): Promise<BackupRun> {
  return apiPost<BackupRun, Record<string, never>>(`/backups/runs/${runId}/actions/cancel`, {});
}

export function createBackupRun(kind: BackupKind): Promise<BackupRun> {
  return apiPost<BackupRun, ApiSchema<"CreateBackupRunRequest">>("/backups/runs", { kind });
}

export function deleteBackupRun(runId: number): Promise<void> {
  return apiDelete<void>(`/backups/runs/${runId}`);
}

// the whole dump is buffered in the tab before the save dialog:
// fine for tens of MB; past that, a short-lived signed download URL the
// browser streams straight to disk.
export async function fetchBackupRunFile(runId: number): Promise<{ blob: Blob; filename: string }> {
  const response = await apiGetRaw(`/backups/runs/${runId}/download`);
  const disposition = response.headers.get("Content-Disposition") ?? "";
  const match = /filename="?([^"]+)"?/.exec(disposition);
  const filename = match ? match[1] : `backup-${runId}`;
  return { blob: await response.blob(), filename };
}
