import type { ApiEnvelope } from "../contracts";
import { authFetchBlob, authFetchJson, TokenExpiredError } from "../api";
import type {
  MayorMovimientosParams,
  MayorMovimientosResponse,
  MayorResumenResponse,
  MayorValidacionesResponse,
} from "../../types/mayor";

function toNumber(value: unknown, fallback = 0): number {
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function toStringValue(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

export async function getMayorMovimientos(
  clienteId: string,
  params: MayorMovimientosParams = {},
): Promise<MayorMovimientosResponse> {
  const query = new URLSearchParams();
  if (params.fecha_desde) query.set("fecha_desde", params.fecha_desde);
  if (params.fecha_hasta) query.set("fecha_hasta", params.fecha_hasta);
  if (params.cuenta) query.set("cuenta", params.cuenta);
  if (params.ls) query.set("ls", params.ls);
  if (params.referencia) query.set("referencia", params.referencia);
  if (params.texto) query.set("texto", params.texto);
  if (typeof params.monto_min === "number" && params.monto_min > 0) query.set("monto_min", String(params.monto_min));
  if (typeof params.monto_max === "number" && params.monto_max > 0) query.set("monto_max", String(params.monto_max));
  if (typeof params.page === "number" && params.page > 0) query.set("page", String(params.page));
  if (typeof params.page_size === "number" && params.page_size > 0) query.set("page_size", String(params.page_size));

  const suffix = query.toString();
  const path = `/api/mayor/${clienteId}/movimientos${suffix ? `?${suffix}` : ""}`;
  try {
    const response = await authFetchJson<ApiEnvelope<MayorMovimientosResponse>>(path);
    return response.data;
  } catch (error) {
    if (error instanceof TokenExpiredError) throw error;
    throw error;
  }
}

export async function getMayorResumen(clienteId: string): Promise<MayorResumenResponse> {
  const response = await authFetchJson<ApiEnvelope<unknown>>(`/api/mayor/${clienteId}/resumen`);
  const data = (response?.data ?? {}) as Record<string, unknown>;
  const resumen = (data.resumen ?? {}) as Record<string, unknown>;
  const source = (data.source ?? {}) as Record<string, unknown>;
  return {
    resumen: {
      total_movimientos: toNumber(resumen.total_movimientos),
      total_debe: toNumber(resumen.total_debe),
      total_haber: toNumber(resumen.total_haber),
      total_neto: toNumber(resumen.total_neto),
      cuentas_distintas: toNumber(resumen.cuentas_distintas),
      asientos_distintos: toNumber(resumen.asientos_distintos),
      fecha_min: toStringValue(resumen.fecha_min),
      fecha_max: toStringValue(resumen.fecha_max),
      monto_promedio: toNumber(resumen.monto_promedio),
    },
    source: {
      cliente_id: toStringValue(source.cliente_id),
      source_file: toStringValue(source.source_file),
      source_path: toStringValue(source.source_path),
      source_format: toStringValue(source.source_format),
      signature: toStringValue(source.signature),
      rows: toNumber(source.rows),
      cache: toStringValue(source.cache),
    },
  };
}

export async function getMayorValidaciones(clienteId: string): Promise<MayorValidacionesResponse> {
  const response = await authFetchJson<ApiEnvelope<MayorValidacionesResponse>>(`/api/mayor/${clienteId}/validaciones`);
  return response.data;
}

type MayorExportParams = MayorMovimientosParams & {
  format: "csv" | "xlsx";
};

export async function exportMayorFile(
  clienteId: string,
  params: MayorExportParams,
): Promise<{ blob: Blob; filename: string; contentType: string }> {
  const query = new URLSearchParams();
  query.set("format", params.format);
  if (params.fecha_desde) query.set("fecha_desde", params.fecha_desde);
  if (params.fecha_hasta) query.set("fecha_hasta", params.fecha_hasta);
  if (params.cuenta) query.set("cuenta", params.cuenta);
  if (params.ls) query.set("ls", params.ls);
  if (params.referencia) query.set("referencia", params.referencia);
  if (params.texto) query.set("texto", params.texto);
  if (typeof params.monto_min === "number" && params.monto_min > 0) query.set("monto_min", String(params.monto_min));
  if (typeof params.monto_max === "number" && params.monto_max > 0) query.set("monto_max", String(params.monto_max));

  const response = await authFetchBlob(`/api/mayor/${clienteId}/export?${query.toString()}`);
  const blob = await response.blob();
  const contentType = String(response.headers.get("content-type") || "");
  const contentDisposition = String(response.headers.get("content-disposition") || "");
  const match = /filename="?([^";]+)"?/i.exec(contentDisposition);
  const fallback = `mayor_${clienteId}.${params.format}`;
  return {
    blob,
    contentType,
    filename: match?.[1] || fallback,
  };
}
