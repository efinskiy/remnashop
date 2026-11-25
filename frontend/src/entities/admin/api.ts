import { apiDelete, apiGet, apiPatch, apiPost } from "@shared/api/http";
import type { UserBase } from "@entities/user/api";
import type { Permission } from "@shared/types/rbac";
import type { ApiSchema } from "@shared/api/schemas";

/** the user fields plus the permission breakdown */
export type Admin = ApiSchema<"AdminResponse">;

export type AdminWithPassword = ApiSchema<"AdminWithPasswordResponse">;

export type AdminPromoteResult = ApiSchema<"AdminPromoteResponse">;

export type CreateAdminPayload = ApiSchema<"CreateAdminRequest">;

export type PromoteAdminPayload = ApiSchema<"PromoteAdminRequest">;

export type UpdateAdminPayload = ApiSchema<"UpdateAdminRequest">;

export type AdminList = ApiSchema<"AdminListResponse">;

export function listAdmins(signal?: AbortSignal): Promise<AdminList> {
  return apiGet<AdminList>("/admins", signal);
}

export function createAdmin(payload: CreateAdminPayload): Promise<AdminWithPassword> {
  return apiPost<AdminWithPassword, CreateAdminPayload>("/admins", payload);
}

export function promoteAdmin(payload: PromoteAdminPayload): Promise<AdminPromoteResult> {
  return apiPost<AdminPromoteResult, PromoteAdminPayload>("/admins/actions/promote", payload);
}

export function updateAdmin(userId: number, payload: UpdateAdminPayload): Promise<Admin> {
  return apiPatch<Admin, UpdateAdminPayload>(`/admins/${userId}`, payload);
}

export type AdminDetail = ApiSchema<"AdminDetailResponse">;

export function getAdmin(userId: number, signal?: AbortSignal): Promise<AdminDetail> {
  return apiGet<AdminDetail>(`/admins/${userId}`, signal);
}

export function demoteAdmin(userId: number): Promise<UserBase> {
  return apiPost<UserBase, Record<string, never>>(`/admins/${userId}/actions/demote`, {});
}

export function deleteAdmin(userId: number): Promise<void> {
  return apiDelete<void>(`/admins/${userId}`);
}

export interface PermissionCatalogEntry {
  permission: Permission;
  resource: string;
  kind: "read" | "write";
  token_grantable: boolean;
  admin_default: boolean;
}

interface PermissionCatalogResponse {
  items: PermissionCatalogEntry[];
  total: number;
}

export function getPermissionCatalog(signal?: AbortSignal): Promise<PermissionCatalogEntry[]> {
  return apiGet<PermissionCatalogResponse>("/permissions/catalog", signal).then((response) => response.items);
}
