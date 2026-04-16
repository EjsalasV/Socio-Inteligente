import { authFetchJson } from "../api";
import type { ApiEnvelope } from "../contracts";

type UnknownRecord = Record<string, unknown>;

function asString(value: unknown, fallback: string = ""): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function asBoolean(value: unknown, fallback: boolean = false): boolean {
  if (typeof value === "boolean") return value;
  if (typeof value === "number") return value !== 0;
  if (typeof value === "string") {
    const raw = value.trim().toLowerCase();
    if (["true", "1", "si", "sí", "yes"].includes(raw)) return true;
    if (["false", "0", "no"].includes(raw)) return false;
  }
  return fallback;
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null;
}

export type ProcedureAreaSummary = {
  area_codigo: string;
  area_nombre: string;
  procedures_count: number;
};

export type ProcedureItem = {
  id: string;
  descripcion: string;
  tipo: string;
  afirmacion: string;
  obligatorio: boolean;
  nia_ref: string;
};

export type AreaProcedureRisk = {
  id: string;
  descripcion: string;
  nivel: string;
  afirmacion: string;
};

export type AreaTaxAlert = {
  id: string;
  descripcion: string;
  nivel: string;
  norma: string;
  accion: string;
};

export type AreaProcedureDetail = {
  area_codigo: string;
  area_nombre: string;
  procedimientos: ProcedureItem[];
  riesgos_tipicos: AreaProcedureRisk[];
  alertas_tributarias: AreaTaxAlert[];
};

export async function getProcedureAreas(): Promise<ProcedureAreaSummary[]> {
  const response = await authFetchJson<ApiEnvelope<UnknownRecord>>("/api/areas");
  const payload = isRecord(response?.data) ? response.data : {};
  return asArray(payload.areas)
    .map((row) => {
      if (!isRecord(row)) return null;
      return {
        area_codigo: asString(row.area_codigo),
        area_nombre: asString(row.area_nombre),
        procedures_count: Number(row.procedures_count ?? 0) || 0,
      };
    })
    .filter((row): row is ProcedureAreaSummary => row !== null && row.area_codigo.length > 0);
}

export async function getAreaProcedures(areaCodigo: string): Promise<AreaProcedureDetail> {
  const response = await authFetchJson<ApiEnvelope<UnknownRecord>>(
    `/api/areas/${encodeURIComponent(areaCodigo)}/procedimientos`,
  );
  const payload = isRecord(response?.data) ? response.data : {};
  const procedimientos = asArray(payload.procedimientos)
    .map((row) => {
      if (!isRecord(row)) return null;
      return {
        id: asString(row.id),
        descripcion: asString(row.descripcion),
        tipo: asString(row.tipo),
        afirmacion: asString(row.afirmacion),
        obligatorio: asBoolean(row.obligatorio),
        nia_ref: asString(row.nia_ref, "NIA 500"),
      };
    })
    .filter((row): row is ProcedureItem => row !== null && row.id.length > 0);

  const riesgosTipicos = asArray(payload.riesgos_tipicos)
    .map((row) => {
      if (!isRecord(row)) return null;
      return {
        id: asString(row.id),
        descripcion: asString(row.descripcion),
        nivel: asString(row.nivel),
        afirmacion: asString(row.afirmacion),
      };
    })
    .filter((row): row is AreaProcedureRisk => row !== null);

  const alertasTributarias = asArray(payload.alertas_tributarias)
    .map((row) => {
      if (!isRecord(row)) return null;
      return {
        id: asString(row.id),
        descripcion: asString(row.descripcion),
        nivel: asString(row.nivel),
        norma: asString(row.norma),
        accion: asString(row.accion),
      };
    })
    .filter((row): row is AreaTaxAlert => row !== null);

  return {
    area_codigo: asString(payload.area_codigo, areaCodigo),
    area_nombre: asString(payload.area_nombre, `Área ${areaCodigo}`),
    procedimientos,
    riesgos_tipicos: riesgosTipicos,
    alertas_tributarias: alertasTributarias,
  };
}

