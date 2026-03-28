import type { components } from "./types";

export type ApiResponseSchema = components["schemas"]["ApiResponse"];
export type ChatRequest = components["schemas"]["ChatRequest"];
export type MetodoRequest = components["schemas"]["MetodoRequest"];

export type ChatResponse = {
  cliente_id: string;
  answer: string;
  context_sources: string[];
};

export type MetodoResponse = {
  cliente_id: string;
  area: string;
  explanation: string;
  context_sources: string[];
};

export type ApiEnvelope<T> = {
  status: "ok" | "error";
  data: T;
  meta: {
    timestamp: string;
  };
};
