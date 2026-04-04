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

export interface RiskStrategyTest {
  test_id: string;
  test_type: "control" | "sustantiva";
  area_id: string;
  area_nombre: string;
  nia_ref: string;
  title: string;
  description: string;
  where_to_execute: "workpapers";
  priority: "alta" | "media" | "baja";
  workpaper_linkable?: boolean;
}

export interface RiskStrategy {
  approach: string;
  control_pct: number;
  substantive_pct: number;
  rationale: string;
  control_tests: RiskStrategyTest[];
  substantive_tests: RiskStrategyTest[];
}

export interface RiskEngineResponse {
  cliente_id: string;
  eje_x: string;
  eje_y: string;
  quadrants: RiskMatrixCell[][];
  areas_criticas: RiskCriticalArea[];
  strategy: RiskStrategy;
  recommended_tests?: RiskStrategyTest[];
}

export type RiskMatrixData = RiskEngineResponse;
