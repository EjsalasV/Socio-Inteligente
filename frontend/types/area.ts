import type { operations } from "../lib/types";

export type AreaApiOperation = operations["get_area_areas__cliente_id___area_code__get"];

export interface AreaEncabezado {
  area_code: string;
  nombre: string;
  responsable: string;
  estatus: string;
  actual_year: string;
  anterior_year: string;
}

export interface AreaCuenta {
  codigo: string;
  nombre: string;
  saldo_actual: number;
  saldo_anterior: number;
  nivel: number;
  checked: boolean;
}

export interface AreaAseveracion {
  nombre: string;
  descripcion: string;
  riesgo_tipico: string;
  procedimiento_clave: string;
}

export interface AreaDetailData {
  encabezado: AreaEncabezado;
  cuentas: AreaCuenta[];
  aseveraciones: AreaAseveracion[];
  briefing_context: {
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
}
