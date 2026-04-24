import type { ApiEnvelope } from "../contracts";
import { authFetchJson } from "../api";
import type {
  KnowledgeAskResponse,
  KnowledgeEntitiesResponse,
  KnowledgeGraphResponse,
  KnowledgeTimelineResponse,
} from "../../types/knowledge";

export type KnowledgeEntitiesParams = {
  page?: number;
  page_size?: number;
  entity_type?: string;
  source_module?: string;
  q?: string;
};

export async function getKnowledgeEntities(
  clienteId: string,
  params: KnowledgeEntitiesParams = {},
): Promise<KnowledgeEntitiesResponse> {
  const query = new URLSearchParams();
  if (typeof params.page === "number" && params.page > 0) query.set("page", String(params.page));
  if (typeof params.page_size === "number" && params.page_size > 0) query.set("page_size", String(params.page_size));
  if (params.entity_type) query.set("entity_type", params.entity_type);
  if (params.source_module) query.set("source_module", params.source_module);
  if (params.q) query.set("q", params.q);

  const suffix = query.toString();
  const path = `/api/knowledge/${clienteId}/entities${suffix ? `?${suffix}` : ""}`;
  const response = await authFetchJson<ApiEnvelope<KnowledgeEntitiesResponse>>(path);
  return response.data;
}

export async function getKnowledgeGraph(clienteId: string): Promise<KnowledgeGraphResponse> {
  const response = await authFetchJson<ApiEnvelope<KnowledgeGraphResponse>>(`/api/knowledge/${clienteId}/graph`);
  return response.data;
}

export async function getKnowledgeTimeline(clienteId: string): Promise<KnowledgeTimelineResponse> {
  const response = await authFetchJson<ApiEnvelope<KnowledgeTimelineResponse>>(`/api/knowledge/${clienteId}/timeline`);
  return response.data;
}

export async function askKnowledge(
  clienteId: string,
  payload: { query: string; top_k?: number },
): Promise<KnowledgeAskResponse> {
  const response = await authFetchJson<ApiEnvelope<KnowledgeAskResponse>>(`/api/knowledge/${clienteId}/ask`, {
    method: "POST",
    body: JSON.stringify({
      query: payload.query,
      top_k: payload.top_k ?? 5,
    }),
  });
  return response.data;
}

