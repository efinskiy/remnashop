import { apiGet } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";

// Read-only: feeds the promocode reward picker (TRAFFIC/DEVICES rewards point at an add-on).
export type AddOnType = ApiSchema<"AddOnType">;

export type AddOnListItem = ApiSchema<"AddOnResponse">;

export function listAddons(signal?: AbortSignal): Promise<AddOnListItem[]> {
  return apiGet<ApiSchema<"AddOnListResponse">>("/addons", signal).then((response) => response.items);
}
