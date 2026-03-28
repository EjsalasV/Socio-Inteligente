import { authFetchJson, TokenExpiredError } from "../api";
import type { ApiEnvelope } from "../contracts";
import type { RiskCriticalArea, RiskEngineResponse, RiskMatrixCell } from "../../types/risk";

function asNumber(value: unknown, fallback: number = 0): number {
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function asString(value: unknown, fallback: string = ""): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function normalizeCell(value: unknown): RiskMatrixCell {
  const record = typeof value === "object" && value !== null ? (value as Record<string, unknown>) : {};
  return {
    row: asNumber(record.row, 0),
    col: asNumber(record.col, 0),
    frecuencia: asNumber(record.frecuencia, 1),
    impacto: asNumber(record.impacto, 1),
    score: asNumber(record.score, 0),
    nivel: asString(record.nivel, "BAJO"),
    area_id: asString(record.area_id, "") || null,
    area_nombre: asString(record.area_nombre, "") || null,
  };
}

function normalizeCriticalArea(value: unknown): RiskCriticalArea | null {
  const record = typeof value === "object" && value !== null ? (value as Record<string, unknown>) : null;
  if (!record) return null;
  const area_id = asString(record.area_id);
  if (!area_id) return null;
  return {
    area_id,
    area_nombre: asString(record.area_nombre, area_id),
    score: asNumber(record.score, 0),
    nivel: asString(record.nivel, "BAJO"),
    frecuencia: asNumber(record.frecuencia, 1),
    impacto: asNumber(record.impacto, 1),
    hallazgos_abiertos: asNumber(record.hallazgos_abiertos, 0),
  };
}

export async function getRiskEngineData(clienteId: string): Promise<RiskEngineResponse> {
  try {
    const response = await authFetchJson<ApiEnvelope<unknown>>(`/risk-engine/${clienteId}`);
    const raw = typeof response?.data === "object" && response?.data !== null ? (response.data as Record<string, unknown>) : {};

    const quadrantsRaw = Array.isArray(raw.quadrants) ? raw.quadrants : [];
    const quadrants = quadrantsRaw.map((row) => (Array.isArray(row) ? row.map(normalizeCell) : []));

    const criticalRaw = Array.isArray(raw.areas_criticas) ? raw.areas_criticas : [];
    const areas_criticas = criticalRaw
      .map(normalizeCriticalArea)
      .filter((item): item is RiskCriticalArea => item !== null)
      .sort((a, b) => b.score - a.score);

    return {
      cliente_id: asString(raw.cliente_id, clienteId),
      eje_x: asString(raw.eje_x, "Impacto"),
      eje_y: asString(raw.eje_y, "Frecuencia"),
      quadrants,
      areas_criticas,
    };
  } catch (error) {
    if (error instanceof TokenExpiredError) {
      throw new TokenExpiredError("La sesión expiró. Vuelve a iniciar sesión.");
    }
    throw error;
  }
}
