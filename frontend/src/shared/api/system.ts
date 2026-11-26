import { apiGet } from "./http";
import type { ApiSchema } from "@shared/api/schemas";

export type SystemMetadata = ApiSchema<"SystemMetadataResponse">;

export function getSystemMetadata(signal?: AbortSignal): Promise<SystemMetadata> {
  return apiGet<SystemMetadata>("/system/metadata", signal);
}
