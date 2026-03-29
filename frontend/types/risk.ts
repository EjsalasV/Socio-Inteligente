import type { operations } from "../lib/types";

export type RiskEngineApiOperation = operations["get_risk_engine_risk_engine__cliente_id__get"];

export interface RiskMatrixCell {
  row: number;
  col: number;
  frecuencia: number;
  impacto: number;
  score: number;
  nivel: "ALTO" | "MEDIO" | "BAJO" | string;
  area_id: string | null;
  area_nombre: string | null;
}

export interface RiskCriticalArea {
  area_id: string;
  area_nombre: string;
  score: number;
  nivel: "ALTO" | "MEDIO" | "BAJO" | string;
  frecuencia: number;
  impacto: number;
  hallazgos_abiertos: number;
  drivers?: string[];
  score_components?: Record<string, number>;
}

export interface RiskEngineResponse {
  cliente_id: string;
  eje_x: string;
  eje_y: string;
  quadrants: RiskMatrixCell[][];
  areas_criticas: RiskCriticalArea[];
}

export type RiskMatrixData = RiskEngineResponse;
