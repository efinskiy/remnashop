import { apiGet } from "@shared/api/http";
import type { ListResponse } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";

// Read-only: feeds the promocode reward picker (TRAFFIC/DEVICES rewards point at an add-on).
export type AddOnType = ApiSchema<"AddOnType">;

export interface AddOnListItem {
  id: number;
  name: string;
  type: AddOnType;
  amount: number;
  is_active: boolean;
}

export function listAddons(signal?: AbortSignal): Promise<AddOnListItem[]> {
  return apiGet<ListResponse<AddOnListItem>>("/addons", signal).then((response) => response.items);
}
