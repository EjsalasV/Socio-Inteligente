import { authFetchJson } from "../api";
import type { ApiEnvelope } from "../contracts";

export type BriefingAreaRequest = {
  cliente_id: string;
  area_codigo: string;
  area_nombre: string;
  marco: string;
  riesgo: string;
  afirmaciones_criticas: string[];
  materialidad: number;
  patrones_historicos: string[];
  hallazgos_previos: string[];
  etapa: string;
};

export type BriefingChunk = {
  norma: string;
  fuente: string;
  excerpt: string;
};

export type BriefingAreaResponse = {
  area_codigo: string;
  area_nombre: string;
  briefing: string;
  normas_activadas: string[];
  chunks_usados: BriefingChunk[];
  generado_en: string;
};

export async function postAreaBriefing(payload: BriefingAreaRequest): Promise<BriefingAreaResponse> {
  const response = await authFetchJson<ApiEnvelope<BriefingAreaResponse>>("/api/briefing/area", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return response.data;
}

