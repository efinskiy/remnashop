import type { components } from "./schema";

// a model of the API, generated from the backend's schema (npm run api:types)
export type ApiSchema<Name extends keyof components["schemas"]> = components["schemas"][Name];
