/**
 * @deprecated Use types from ./types (auto-generated from OpenAPI).
 * This file duplicated types from OpenAPI schema.
 * All types should be imported from generated ./types instead.
 */

import type { components } from "./types";

// Re-export OpenAPI types with clear naming
export type ApiResponseSchema = components["schemas"]["ApiResponse"];
export type ChatRequest = components["schemas"]["ChatRequest"];
export type MetodoRequest = components["schemas"]["MetodoRequest"];

// These response payloads are wrapped by ApiResponse.data and are not exported as standalone schemas.
export type ChatResponse = {
  answer?: string;
  citations?: Array<Record<string, unknown>>;
  confidence?: number;
  mode_used?: string;
  web_search_used?: boolean;
  expert_criteria_used?: boolean;
  [key: string]: unknown;
};

export type MetodoResponse = {
  [key: string]: unknown;
};

export type ApiEnvelope<T> = ApiResponseSchema & { data: T };
