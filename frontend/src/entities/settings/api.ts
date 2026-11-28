import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from "@shared/api/http";
import type { ApiSchema } from "@shared/api/schemas";

export type BotSettings = ApiSchema<"BotSettingsResponse">;

export type UpdateBotSettingsPayload = ApiSchema<"UpdateBotSettingsRequest">;

export function getBotSettings(signal?: AbortSignal): Promise<BotSettings> {
  return apiGet<BotSettings>("/settings/bot", signal);
}

export type BotStatus = ApiSchema<"BotStatusResponse">;

export function getBotStatus(signal?: AbortSignal): Promise<BotStatus> {
  return apiGet<BotStatus>("/settings/bot/status", signal);
}

export function getBotLogs(signal?: AbortSignal): Promise<string[]> {
  return apiGet<ApiSchema<"BotLogsResponse">>("/settings/bot/logs", signal).then((response) => response.lines);
}

export function updateBotSettings(payload: UpdateBotSettingsPayload): Promise<BotSettings> {
  return apiPatch<BotSettings, UpdateBotSettingsPayload>("/settings/bot", payload);
}

export function setBotProxy(proxyUrl: string): Promise<BotSettings> {
  return apiPut<BotSettings, ApiSchema<"SetBotProxyRequest">>("/settings/bot/proxy", { proxy_url: proxyUrl });
}

export function removeBotProxy(): Promise<BotSettings> {
  return apiDelete<BotSettings>("/settings/bot/proxy");
}

export function restartBot(): Promise<null> {
  return apiPost<null, Record<string, never>>("/settings/bot/actions/restart", {});
}

export type BotCommandItem = ApiSchema<"BotCommandRequest">;

export type UpdateBotCommandsResult = ApiSchema<"UpdateBotCommandsResponse">;

export function getBotCommands(
  signal?: AbortSignal,
  defaultOrder = false,
): Promise<BotCommandItem[]> {
  return apiGet<ApiSchema<"BotCommandsResponse">>(
    `/settings/bot/commands${defaultOrder ? "?default_order=true" : ""}`,
    signal,
  ).then((response) => response.commands);
}

export function updateBotCommands(commands: BotCommandItem[]): Promise<UpdateBotCommandsResult> {
  return apiPut<UpdateBotCommandsResult, ApiSchema<"UpdateBotCommandsRequest">>(
    "/settings/bot/commands",
    { commands },
  );
}

export type OAuthSettings = ApiSchema<"OAuthSettingsResponse">;

export type UpdateOAuthSettingsPayload = ApiSchema<"UpdateOAuthSettingsRequest">;

export function getOAuthSettings(signal?: AbortSignal): Promise<OAuthSettings> {
  return apiGet<OAuthSettings>("/settings/oauth", signal);
}

export function updateOAuthSettings(payload: UpdateOAuthSettingsPayload): Promise<OAuthSettings> {
  return apiPatch<OAuthSettings, UpdateOAuthSettingsPayload>("/settings/oauth", payload);
}

export type SmtpSecurity = ApiSchema<"SmtpSecurity">;

export type EmailSettings = ApiSchema<"EmailSettingsResponse">;

export type UpdateEmailSettingsPayload = ApiSchema<"UpdateEmailSettingsRequest">;

export function getEmailSettings(signal?: AbortSignal): Promise<EmailSettings> {
  return apiGet<EmailSettings>("/settings/email", signal);
}

export function updateEmailSettings(payload: UpdateEmailSettingsPayload): Promise<EmailSettings> {
  return apiPatch<EmailSettings, UpdateEmailSettingsPayload>("/settings/email", payload);
}

export function sendTestEmail(bulk = false): Promise<null> {
  return apiPost<null, ApiSchema<"SendTestEmailRequest">>("/settings/email/actions/test", { bulk });
}

export function resetEmailSettings(): Promise<EmailSettings> {
  return apiPost<EmailSettings, Record<string, never>>("/settings/email/actions/reset", {});
}

export function resetBulkEmailSettings(): Promise<EmailSettings> {
  return apiPost<EmailSettings, Record<string, never>>("/settings/email/bulk/actions/reset", {});
}

export type CabinetAuthSettings = ApiSchema<"CabinetAuthSettingsResponse">;

export type CaptchaProvider = ApiSchema<"CaptchaProvider">;

export type UpdateCabinetAuthSettingsPayload = ApiSchema<"UpdateCabinetAuthSettingsRequest">;

export function getCabinetAuthSettings(signal?: AbortSignal): Promise<CabinetAuthSettings> {
  return apiGet<CabinetAuthSettings>("/settings/cabinet-auth", signal);
}

export function updateCabinetAuthSettings(
  payload: UpdateCabinetAuthSettingsPayload,
): Promise<CabinetAuthSettings> {
  return apiPatch<CabinetAuthSettings, UpdateCabinetAuthSettingsPayload>("/settings/cabinet-auth", payload);
}

// support_telegram: a Telegram username without "@"; support_url: an https page;
// payment_email: sent to every gateway instead of the customer's email (null = ask the customer);
// plan_change_credit_enabled off: a plan change is paid in full, the old term's unused part is dropped;
// plan_change_traffic_cap_enabled: a never-resetting traffic limit caps the credit of the running term
export type ShopSettings = ApiSchema<"ShopSettingsResponse">;

// a PATCH: only the fields sent change (the support card saves its two on their own)
export type UpdateShopSettingsPayload = ApiSchema<"UpdateShopSettingsRequest">;

export function getShopSettings(signal?: AbortSignal): Promise<ShopSettings> {
  return apiGet<ShopSettings>("/settings/shop", signal);
}

export function updateShopSettings(payload: UpdateShopSettingsPayload): Promise<ShopSettings> {
  return apiPatch<ShopSettings, UpdateShopSettingsPayload>("/settings/shop", payload);
}

export type AccessMode = ApiSchema<"AccessMode">;

export type AccessSettings = ApiSchema<"AccessSettingsResponse">;

export function getAccessSettings(signal?: AbortSignal): Promise<AccessSettings> {
  return apiGet<AccessSettings>("/settings/access", signal);
}

export function updateAccessSettings(payload: ApiSchema<"UpdateAccessSettingsRequest">): Promise<AccessSettings> {
  return apiPatch<AccessSettings, ApiSchema<"UpdateAccessSettingsRequest">>("/settings/access", payload);
}

export type BotRequirements = ApiSchema<"BotRequirementsResponse">;

export function getBotRequirements(signal?: AbortSignal): Promise<BotRequirements> {
  return apiGet<BotRequirements>("/settings/bot/requirements", signal);
}

export function updateBotRequirements(payload: ApiSchema<"UpdateBotRequirementsRequest">): Promise<BotRequirements> {
  return apiPut<BotRequirements, ApiSchema<"UpdateBotRequirementsRequest">>("/settings/bot/requirements", payload);
}

export function getPaymentWaitlistCount(signal?: AbortSignal): Promise<ApiSchema<"PaymentWaitlistCountResponse">> {
  return apiGet<ApiSchema<"PaymentWaitlistCountResponse">>("/transactions/waitlist", signal);
}

// traffic_limit_mb: MB, 0 = unlimited; duration_days: 0 = no end; expiry_disable_warn_days: 0 = no warning
export type GraceSettings = ApiSchema<"GraceSettingsResponse">;

export type UpdateGraceSettingsPayload = ApiSchema<"UpdateGraceSettingsRequest">;

export function getGraceSettings(signal?: AbortSignal): Promise<GraceSettings> {
  return apiGet<GraceSettings>("/settings/grace", signal);
}

export function updateGraceSettings(payload: UpdateGraceSettingsPayload): Promise<GraceSettings> {
  return apiPatch<GraceSettings, UpdateGraceSettingsPayload>("/settings/grace", payload);
}
