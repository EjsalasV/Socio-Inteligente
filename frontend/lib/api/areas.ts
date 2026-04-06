import { authFetchJson, TokenExpiredError } from "../api";
import type { ApiEnvelope } from "../contracts";
import type { AreaAseveracion, AreaCuenta, AreaDetailData, AreaEncabezado } from "../../types/area";

function asNumber(value: unknown, fallback: number = 0): number {
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function asString(value: unknown, fallback: string = ""): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function normalizeEncabezado(value: unknown, areaCode: string): AreaEncabezado {
  const row = typeof value === "object" && value !== null ? (value as Record<string, unknown>) : {};
  return {
    area_code: asString(row.area_code, areaCode),
    nombre: asString(row.nombre, `Área ${areaCode}`),
    responsable: asString(row.responsable, "Sin asignar"),
    estatus: asString(row.estatus, "pendiente"),
    actual_year: asString(row.actual_year, "Actual"),
    anterior_year: asString(row.anterior_year, "Anterior"),
  };
}

function normalizeCuenta(value: unknown): AreaCuenta | null {
  const row = typeof value === "object" && value !== null ? (value as Record<string, unknown>) : null;
  if (!row) return null;
  const codigo = asString(row.codigo);
  if (!codigo) return null;

  return {
    codigo,
    nombre: asString(row.nombre),
    saldo_actual: asNumber(row.saldo_actual),
    saldo_anterior: asNumber(row.saldo_anterior),
    nivel: asNumber(row.nivel, 2),
    checked: Boolean(row.checked),
  };
}

function normalizeAseveracion(value: unknown): AreaAseveracion | null {
  const item = typeof value === "object" && value !== null ? (value as Record<string, unknown>) : null;
  if (!item) return null;
  return {
    nombre: asString(item.nombre),
    descripcion: asString(item.descripcion),
    riesgo_tipico: asString(item.riesgo_tipico, "medio"),
    procedimiento_clave: asString(item.procedimiento_clave),
  };
}

function normalizeBriefingContext(value: unknown, clienteId: string, areaCode: string, areaNombre: string) {
  const row = typeof value === "object" && value !== null ? (value as Record<string, unknown>) : {};
  const asStringList = (v: unknown): string[] =>
    Array.isArray(v) ? v.map((x) => asString(x)).filter((x) => x.length > 0) : [];
  return {
    cliente_id: asString(row.cliente_id, clienteId),
    area_codigo: asString(row.area_codigo, areaCode),
    area_nombre: asString(row.area_nombre, areaNombre),
    marco: asString(row.marco, "niif_pymes"),
    riesgo: asString(row.riesgo, "medio"),
    afirmaciones_criticas: asStringList(row.afirmaciones_criticas),
    materialidad: asNumber(row.materialidad, 0),
    patrones_historicos: asStringList(row.patrones_historicos),
    hallazgos_previos: asStringList(row.hallazgos_previos),
    etapa: asString(row.etapa, "ejecucion"),
  };
}

export async function getAreaDetail(clienteId: string, areaCode: string): Promise<AreaDetailData> {
  try {
    const response = await authFetchJson<ApiEnvelope<unknown>>(`/areas/${clienteId}/${areaCode}`);
    const raw = typeof response?.data === "object" && response?.data !== null ? (response.data as Record<string, unknown>) : {};

    const encabezado = normalizeEncabezado(raw.encabezado, areaCode);
    return {
      encabezado,
      cuentas: (Array.isArray(raw.cuentas) ? raw.cuentas : [])
        .map(normalizeCuenta)
        .filter((x): x is AreaCuenta => x !== null),
      aseveraciones: (Array.isArray(raw.aseveraciones) ? raw.aseveraciones : [])
        .map(normalizeAseveracion)
        .filter((x): x is AreaAseveracion => x !== null),
      briefing_context: normalizeBriefingContext(raw.briefing_context, clienteId, areaCode, encabezado.nombre),
    };
  } catch (error) {
    if (error instanceof TokenExpiredError) {
      throw new TokenExpiredError("La sesión expiró. Vuelve a iniciar sesión.");
    }
    throw error;
  }
}

export async function patchAreaCheck(
  clienteId: string,
  areaCode: string,
  cuentaCodigo: string,
  checked: boolean,
): Promise<void> {
  await authFetchJson<ApiEnvelope<unknown>>(`/areas/${clienteId}/${areaCode}/cuentas/${encodeURIComponent(cuentaCodigo)}/check`, {
    method: "PATCH",
    body: JSON.stringify({ checked }),
  });
}
