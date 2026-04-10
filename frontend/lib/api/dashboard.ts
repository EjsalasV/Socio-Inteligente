import { authFetchJson, TokenExpiredError } from "../api";
import type { ApiEnvelope } from "../contracts";
import type { DashboardData, DashboardResponse } from "../../types/dashboard";

type UnknownRecord = Record<string, unknown>;

function asNumber(value: unknown, fallback: number = 0): number {
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function asString(value: unknown, fallback: string = ""): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null;
}

function normalizeDashboardPayload(clienteId: string, raw: UnknownRecord): DashboardData {
  const balance = isRecord(raw.balance) ? raw.balance : {};
  const progreso = isRecord(raw.progreso) ? raw.progreso : {};
  const topAreasRaw = Array.isArray(raw.top_areas) ? raw.top_areas : [];

  return {
    activo: asNumber(balance.activo, 0),
    pasivo: asNumber(balance.pasivo, 0),
    patrimonio: asNumber(balance.patrimonio, 0),
    ingresos: asNumber(balance.ingresos, 0),
    gastos: asNumber(balance.gastos, 0),
    riesgo_global: asString(raw.riesgo_global, "MEDIO"),
    progreso_auditoria: asNumber(progreso.pct_completado, 0),
    cliente_id: asString(raw.cliente_id, clienteId),
    periodo: asString(raw.periodo, "Actual"),
    nombre_cliente: asString(raw.nombre_cliente, clienteId),
    sector: asString(raw.sector, ""),
    materialidad_global: asNumber(raw.materialidad_global, 0),
    materialidad_ejecucion: asNumber(raw.materialidad_ejecucion, 0),
    umbral_trivial: asNumber(raw.umbral_trivial, 0),
    materialidad_origen: asString(raw.materialidad_origen, ""),
    tb_stage: asString(raw.tb_stage, "sin_saldos"),
    fase_actual: asString(raw.fase_actual, ""),
    workflow_phase: asString(raw.workflow_phase, "planificacion"),
    workflow_gates: Array.isArray(raw.workflow_gates)
      ? raw.workflow_gates
          .map((gate) => {
            if (!isRecord(gate)) return null;
            const status = asString(gate.status, "blocked");
            return {
              code: asString(gate.code, ""),
              title: asString(gate.title, ""),
              status: status === "ok" ? "ok" : "blocked",
              detail: asString(gate.detail, ""),
            };
          })
          .filter((gate): gate is DashboardData["workflow_gates"][number] => gate !== null)
      : [],
    balance_status: asString(raw.balance_status, "cuadrado"),
    resultado_periodo: asNumber(raw.resultado_periodo, 0),
    balance_delta: asNumber(raw.balance_delta, 0),
    materialidad_detalle:
      isRecord(raw.materialidad_detalle)
        ? {
            nia_base: asString(raw.materialidad_detalle.nia_base, "NIA 320"),
            base_usada: asString(raw.materialidad_detalle.base_usada, ""),
            base_valor: asNumber(raw.materialidad_detalle.base_valor, 0),
            porcentaje_aplicado: asNumber(raw.materialidad_detalle.porcentaje_aplicado, 0),
            porcentaje_rango_min: asNumber(raw.materialidad_detalle.porcentaje_rango_min, 0),
            porcentaje_rango_max: asNumber(raw.materialidad_detalle.porcentaje_rango_max, 0),
            criterio_seleccion_pct: asString(raw.materialidad_detalle.criterio_seleccion_pct, ""),
            origen_regla: asString(raw.materialidad_detalle.origen_regla, ""),
            minimum_threshold_aplicado: asNumber(raw.materialidad_detalle.minimum_threshold_aplicado, 0),
            minimum_threshold_origen: asString(raw.materialidad_detalle.minimum_threshold_origen, ""),
          }
        : {
            nia_base: "NIA 320",
            base_usada: "",
            base_valor: 0,
            porcentaje_aplicado: 0,
            porcentaje_rango_min: 0,
            porcentaje_rango_max: 0,
            criterio_seleccion_pct: "",
            origen_regla: "",
            minimum_threshold_aplicado: 0,
            minimum_threshold_origen: "",
          },
    top_areas: topAreasRaw
      .map((item) => {
        if (!isRecord(item)) return null;
        return {
          codigo: asString(item.codigo, ""),
          nombre: asString(item.nombre, ""),
          score_riesgo: asNumber(item.score_riesgo, 0),
          prioridad: asString(item.prioridad, "baja"),
          saldo_total: asNumber(item.saldo_total, 0),
          con_saldo: Boolean(item.con_saldo),
        };
      })
      .filter((item): item is DashboardData["top_areas"][number] => item !== null),
    top_areas_page: asNumber(raw.top_areas_page, 1),
    top_areas_page_size: asNumber(raw.top_areas_page_size, topAreasRaw.length),
    top_areas_total: asNumber(raw.top_areas_total, topAreasRaw.length),
    top_areas_has_more: Boolean(raw.top_areas_has_more),
  };
}

type DashboardQueryOptions = {
  areasPage?: number;
  areasPageSize?: number;
};

function buildDashboardPath(clienteId: string, options?: DashboardQueryOptions): string {
  const areasPage = options?.areasPage ?? 1;
  const areasPageSize = options?.areasPageSize ?? 8;
  return `/dashboard/${clienteId}?areas_page=${encodeURIComponent(String(areasPage))}&areas_page_size=${encodeURIComponent(String(areasPageSize))}`;
}

export async function getDashboardData(clienteId: string, options?: DashboardQueryOptions): Promise<DashboardData> {
  try {
    const response = await authFetchJson<ApiEnvelope<DashboardResponse> | DashboardResponse>(
      buildDashboardPath(clienteId, options),
    );

    const payload = isRecord(response) && "data" in response && isRecord(response.data)
      ? (response.data as UnknownRecord)
      : (response as UnknownRecord);

    return normalizeDashboardPayload(clienteId, payload);
  } catch (error) {
    if (error instanceof TokenExpiredError) {
      throw new TokenExpiredError("La sesión expiró. Vuelve a iniciar sesión.");
    }
    throw error;
  }
}
