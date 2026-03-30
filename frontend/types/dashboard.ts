export interface BalanceKPIs {
  activo: number;
  pasivo: number;
  patrimonio: number;
  ingresos: number;
  gastos: number;
}

export interface ProgresoEncargo {
  pct_completado: number;
  areas_completas: number;
  areas_en_proceso: number;
  areas_no_iniciadas: number;
  total_areas: number;
}

export interface AreaRiesgo {
  codigo: string;
  nombre: string;
  score_riesgo: number;
  prioridad: "alta" | "media" | "baja" | string;
  saldo_total: number;
  con_saldo: boolean;
}

export interface DashboardWorkflowGate {
  code: string;
  title: string;
  status: "ok" | "blocked";
  detail: string;
}

export interface DashboardResponse {
  cliente_id: string;
  nombre_cliente: string;
  periodo: string;
  sector: string;
  riesgo_global: string;
  balance: BalanceKPIs;
  progreso: ProgresoEncargo;
  top_areas: AreaRiesgo[];
  materialidad_global: number;
  materialidad_ejecucion: number;
  umbral_trivial: number;
  materialidad_origen: string;
  tb_stage: "final" | "preliminar" | "inicial" | "sin_saldos" | string;
  fase_actual: string;
  workflow_phase: string;
  workflow_gates: DashboardWorkflowGate[];
}

export interface DashboardData {
  activo: number;
  pasivo: number;
  patrimonio: number;
  ingresos: number;
  gastos: number;
  riesgo_global: string;
  progreso_auditoria: number;
  cliente_id: string;
  periodo: string;
  nombre_cliente: string;
  sector: string;
  materialidad_global: number;
  materialidad_ejecucion: number;
  umbral_trivial: number;
  materialidad_origen: string;
  tb_stage: "final" | "preliminar" | "inicial" | "sin_saldos" | string;
  fase_actual: string;
  workflow_phase: string;
  workflow_gates: DashboardWorkflowGate[];
  top_areas: AreaRiesgo[];
}
