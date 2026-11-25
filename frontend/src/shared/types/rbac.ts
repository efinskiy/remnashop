import type { ApiSchema } from "@shared/api/schemas";

// Mirrors backend/app/core/enums.py's Role and backend/app/core/security/permissions.py's Permission.
export type Role = "USER" | "ADMIN" | "OWNER" | "SYSTEM";

export type Permission = ApiSchema<"Permission">;
