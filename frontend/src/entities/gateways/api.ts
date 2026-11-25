import { apiGet, apiPatch, apiPost, apiPut } from "@shared/api/http";
import type { ListResponse } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";

export type Gateway = ApiSchema<"GatewayResponse">;

export type GatewayChannels = Partial<Pick<Gateway, "telegram_enabled" | "cabinet_enabled">>;

export type GatewayFieldKind = "text" | "secret" | "number" | "boolean" | "url";

export interface GatewayFieldSpec {
  key: string;
  kind: GatewayFieldKind;
  required: boolean;
  /** the boolean field that shows this one (its own key, for that switch); null: always shown */
  group: string | null;
  /** a group's switch shown only while every channel is on (or the switch is) */
  requires_all_channels: boolean;
  /** asked for while this switch is off; a grouped value field is asked for while shown */
  required_unless: string | null;
}

export interface GatewayCatalogEntry {
  type: string;
  webhook_url: string | null;
  fields: GatewayFieldSpec[];
}

interface GatewayCatalogResponse {
  items: GatewayCatalogEntry[];
  total: number;
}

export function listGateways(signal?: AbortSignal): Promise<Gateway[]> {
  return apiGet<ListResponse<Gateway>>("/gateways", signal).then((response) => response.items);
}

export function getGatewayCatalog(signal?: AbortSignal): Promise<GatewayCatalogEntry[]> {
  return apiGet<GatewayCatalogResponse>("/gateways/catalog", signal).then(
    (response) => response.items,
  );
}

export function updateGatewaySettings(
  type: string,
  values: Record<string, string>,
): Promise<Gateway> {
  return apiPut<Gateway, { values: Record<string, string> }>(`/gateways/${type}/settings`, {
    values,
  });
}

export function updateGatewayChannels(type: string, channels: GatewayChannels): Promise<Gateway> {
  return apiPatch<Gateway, GatewayChannels>(`/gateways/${type}`, channels);
}

export function setGatewayActive(type: string, active: boolean): Promise<Gateway> {
  const action = active ? "enable" : "disable";
  return apiPost<Gateway, Record<string, never>>(`/gateways/${type}/actions/${action}`, {});
}

export type TestPayment = ApiSchema<"TestPaymentResponse">;

export type TestPaymentStatus = ApiSchema<"TransactionStatus">;

export type TestPaymentChannel = ApiSchema<"PurchaseChannel">;

export function createTestPayment(type: string, channel: TestPaymentChannel): Promise<TestPayment> {
  return apiPost<TestPayment, { gateway_type: string; channel: TestPaymentChannel }>(
    "/transactions/test-payments",
    { gateway_type: type, channel },
  );
}

export function getTestPaymentStatus(orderId: number): Promise<{ status: TestPaymentStatus }> {
  return apiGet<{ status: TestPaymentStatus }>(`/transactions/test-payments/${orderId}`);
}

/** @public reorder UI not built yet */
export function reorderGateways(types: string[]): Promise<Gateway[]> {
  return apiPost<ListResponse<Gateway>, { types: string[] }>("/gateways/actions/reorder", { types }).then(
    (response) => response.items,
  );
}
