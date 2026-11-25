import { apiGet, apiPatch, apiPost, apiPut } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";

export type Gateway = ApiSchema<"GatewayResponse">;

export type GatewayChannels = Partial<Pick<Gateway, "telegram_enabled" | "cabinet_enabled">>;

export type GatewayFieldSpec = ApiSchema<"GatewayFieldSpecResponse">;

export type GatewayCatalogEntry = ApiSchema<"GatewayCatalogEntryResponse">;

export function listGateways(signal?: AbortSignal): Promise<Gateway[]> {
  return apiGet<ApiSchema<"GatewayListResponse">>("/gateways", signal).then((response) => response.items);
}

export function getGatewayCatalog(signal?: AbortSignal): Promise<GatewayCatalogEntry[]> {
  return apiGet<ApiSchema<"GatewayCatalogResponse">>("/gateways/catalog", signal).then(
    (response) => response.items,
  );
}

export function updateGatewaySettings(
  type: string,
  values: Record<string, string>,
): Promise<Gateway> {
  return apiPut<Gateway, ApiSchema<"UpdateGatewaySettingsRequest">>(`/gateways/${type}/settings`, {
    values,
  });
}

export function updateGatewayChannels(type: PaymentGatewayType, channels: GatewayChannels): Promise<Gateway> {
  return apiPatch<Gateway, ApiSchema<"UpdateGatewayRequest">>(`/gateways/${type}`, channels);
}

export function setGatewayActive(type: PaymentGatewayType, active: boolean): Promise<Gateway> {
  const action = active ? "enable" : "disable";
  return apiPost<Gateway, Record<string, never>>(`/gateways/${type}/actions/${action}`, {});
}

export type TestPayment = ApiSchema<"TestPaymentResponse">;

export type TestPaymentStatus = ApiSchema<"TransactionStatus">;

export type PaymentGatewayType = ApiSchema<"PaymentGatewayType">;

export type TestPaymentChannel = ApiSchema<"PurchaseChannel">;

export function createTestPayment(type: PaymentGatewayType, channel: TestPaymentChannel): Promise<TestPayment> {
  return apiPost<TestPayment, ApiSchema<"CreateTestPaymentRequest">>(
    "/transactions/test-payments",
    { gateway_type: type, channel },
  );
}

export function getTestPaymentStatus(orderId: number): Promise<{ status: TestPaymentStatus }> {
  return apiGet<ApiSchema<"TestPaymentStatusResponse">>(`/transactions/test-payments/${orderId}`);
}

/** @public reorder UI not built yet */
export function reorderGateways(types: PaymentGatewayType[]): Promise<Gateway[]> {
  return apiPost<ApiSchema<"GatewayListResponse">, ApiSchema<"ReorderGatewaysRequest">>("/gateways/actions/reorder", { types }).then(
    (response) => response.items,
  );
}
