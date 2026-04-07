import { authFetchJson } from "../api";
import type { ApiEnvelope } from "../contracts";

export type PreEmitCheckRequest = {
  cliente_id: string;
  fase?: string;
  area_codigo?: string;
  document_type?: string;
};

export type PreEmitCheckResponse = {
  status: "ok" | "blocked";
  fase: string;
  document_type: string;
  blocking_reasons: string[];
  warnings: string[];
  score_calidad: number;
  coverage: {
    total_assertions: number;
    covered_assertions: number;
    coverage_pct: number;
    missing_by_area: Record<string, string[]>;
  };
};

export type QualityMetricsResponse = {
  scope: {
    cliente_id: string;
    area_codigo: string;
    date_from: string;
    date_to: string;
    events_count: number;
  };
  operativo: {
    uso_por_modulo: Record<string, number>;
    tiempo_manual_promedio_min: number;
    tiempo_ai_promedio_min: number;
    ahorro_promedio_min: number;
    ahorro_promedio_pct: number;
  };
  calidad_tecnica: {
    respuestas_total: number;
    chunks_valid_rate_pct: number;
    staleness_warning_rate_pct: number;
    llm_error_rate_pct: number;
  };
  top_blocking_reasons: Array<{ reason: string; count: number }>;
};

export async function postPreEmitCheck(payload: PreEmitCheckRequest): Promise<PreEmitCheckResponse> {
  const response = await authFetchJson<ApiEnvelope<PreEmitCheckResponse>>("/api/quality/pre-emit-check", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return response.data;
}

export async function getQualityMetrics(params: {
  cliente_id?: string;
  area_codigo?: string;
  date_from?: string;
  date_to?: string;
}): Promise<QualityMetricsResponse> {
  const q = new URLSearchParams();
  if (params.cliente_id) q.set("cliente_id", params.cliente_id);
  if (params.area_codigo) q.set("area_codigo", params.area_codigo);
  if (params.date_from) q.set("date_from", params.date_from);
  if (params.date_to) q.set("date_to", params.date_to);
  const suffix = q.toString() ? `?${q.toString()}` : "";
  const response = await authFetchJson<ApiEnvelope<QualityMetricsResponse>>(`/api/quality/metrics${suffix}`);
  return response.data;
}

