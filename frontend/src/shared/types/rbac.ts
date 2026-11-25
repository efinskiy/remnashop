import type { ApiSchema } from "@shared/api/schemas";

// the role names the API speaks
export type Role = ApiSchema<"UserResponse">["role"];

export type Permission = ApiSchema<"Permission">;
