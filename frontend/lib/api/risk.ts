import { authFetchJson, TokenExpiredError } from "../api";
import type { ApiEnvelope } from "../contracts";
import type { RiskCriticalArea, RiskEngineResponse, RiskMatrixCell, RiskStrategy, RiskStrategyTest } from "../../types/risk";

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
    drivers: Array.isArray(record.drivers) ? record.drivers.map((x) => asString(x)).filter(Boolean) : [],
    score_components:
      typeof record.score_components === "object" && record.score_components !== null
        ? Object.fromEntries(
            Object.entries(record.score_components as Record<string, unknown>).map(([k, v]) => [k, asNumber(v)]),
          )
        : {},
  };
}

function normalizeStrategyTest(value: unknown, fallbackType: "control" | "sustantiva"): RiskStrategyTest | null {
  const record = typeof value === "object" && value !== null ? (value as Record<string, unknown>) : null;
  if (!record) return null;
  const test_id = asString(record.test_id);
  const area_id = asString(record.area_id);
  const title = asString(record.title);
  if (!test_id || !area_id || !title) return null;
  const test_type = asString(record.test_type, fallbackType) as "control" | "sustantiva";
  const where = asString(record.where_to_execute, "workpapers") as "workpapers";
  const priority = asString(record.priority, "media") as "alta" | "media" | "baja";
  return {
    test_id,
    test_type,
    area_id,
    area_nombre: asString(record.area_nombre, area_id),
    nia_ref: asString(record.nia_ref, ""),
    title,
    description: asString(record.description, ""),
    where_to_execute: where,
    priority,
    workpaper_linkable: Boolean(record.workpaper_linkable ?? true),
  };
}

function normalizeStrategy(value: unknown): RiskStrategy {
  const record = typeof value === "object" && value !== null ? (value as Record<string, unknown>) : {};
  const controlRaw = Array.isArray(record.control_tests) ? record.control_tests : [];
  const subRaw = Array.isArray(record.substantive_tests) ? record.substantive_tests : [];
  return {
    approach: asString(record.approach, "Mixto"),
    control_pct: asNumber(record.control_pct, 50),
    substantive_pct: asNumber(record.substantive_pct, 50),
    rationale: asString(
      record.rationale,
      "Sin estrategia definida. Completa datos de riesgo para obtener recomendacion.",
    ),
    control_tests: controlRaw
      .map((x) => normalizeStrategyTest(x, "control"))
      .filter((item): item is RiskStrategyTest => item !== null),
    substantive_tests: subRaw
      .map((x) => normalizeStrategyTest(x, "sustantiva"))
      .filter((item): item is RiskStrategyTest => item !== null),
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

    const recommendedRaw = Array.isArray(raw.recommended_tests) ? raw.recommended_tests : [];

    return {
      cliente_id: asString(raw.cliente_id, clienteId),
      eje_x: asString(raw.eje_x, "Impacto"),
      eje_y: asString(raw.eje_y, "Frecuencia"),
      quadrants,
      areas_criticas,
      strategy: normalizeStrategy(raw.strategy),
      recommended_tests: recommendedRaw
        .map((x) => normalizeStrategyTest(x, "control"))
        .filter((item): item is RiskStrategyTest => item !== null),
    };
  } catch (error) {
    if (error instanceof TokenExpiredError) {
      throw new TokenExpiredError("La sesión expiró. Vuelve a iniciar sesión.");
    }
    throw error;
  }
}
