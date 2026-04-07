import { authFetchJson } from "../api";
import type { ApiEnvelope } from "../contracts";

export type HallazgoEstructurarRequest = {
  cliente_id: string;
  area_codigo: string;
  area_nombre: string;
  marco: string;
  riesgo: string;
  afirmaciones_criticas: string[];
  etapa: string;
  condicion_detectada: string;
  monto_estimado?: number | null;
  causa_preliminar?: string;
  efecto_preliminar?: string;
  guardar_en_hallazgos?: boolean;
};

export type HallazgoEstructurarResponse = {
  area_codigo: string;
  area_nombre: string;
  hallazgo: string;
  normas_activadas: string[];
  chunks_usados: Array<{ norma: string; fuente: string; excerpt: string }>;
  trazabilidad?: Array<{
    norma: string;
    fuente_chunk: string;
    chunk_id: string;
    area_codigo: string;
    paper_id?: string | null;
    timestamp: string;
  }>;
  generado_en: string;
};

export type BriefingTiempoLogRequest = {
  cliente_id: string;
  area_codigo: string;
  area_nombre: string;
  tiempo_manual_min: number;
  tiempo_ai_min: number;
  notas?: string;
};

export type BriefingTiempoLogResponse = {
  saved: boolean;
  delta_min: number;
  ahorro_pct: number;
};

export async function postEstructurarHallazgo(payload: HallazgoEstructurarRequest): Promise<HallazgoEstructurarResponse> {
  const response = await authFetchJson<ApiEnvelope<HallazgoEstructurarResponse>>("/api/hallazgos/estructurar", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return response.data;
}

export async function postBriefingTiempo(payload: BriefingTiempoLogRequest): Promise<BriefingTiempoLogResponse> {
  const response = await authFetchJson<ApiEnvelope<BriefingTiempoLogResponse>>("/api/hallazgos/tiempo-briefing", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return response.data;
}
