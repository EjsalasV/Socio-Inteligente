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

export interface DashboardAreaMaterialidad {
  area_codigo: string;
  area_nombre: string;
  porcentaje_aplicado: number;
  base_referencia: number;
  materialidad_sugerida: number;
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
  balance_status: "cuadrado" | "resultado_periodo" | "descuadrado" | string;
  resultado_periodo: number;
  balance_delta: number;
  materialidad_detalle: {
    nia_base: string;
    base_usada: string;
    base_valor: number;
    porcentaje_aplicado: number;
    porcentaje_rango_min: number;
    porcentaje_rango_max: number;
    criterio_seleccion_pct: string;
    origen_regla: string;
    minimum_threshold_aplicado: number;
    minimum_threshold_origen: string;
  };
  materialidad_por_area: DashboardAreaMaterialidad[];
  top_areas_page: number;
  top_areas_page_size: number;
  top_areas_total: number;
  top_areas_has_more: boolean;
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
  balance_status: "cuadrado" | "resultado_periodo" | "descuadrado" | string;
  resultado_periodo: number;
  balance_delta: number;
  materialidad_detalle: {
    nia_base: string;
    base_usada: string;
    base_valor: number;
    porcentaje_aplicado: number;
    porcentaje_rango_min: number;
    porcentaje_rango_max: number;
    criterio_seleccion_pct: string;
    origen_regla: string;
    minimum_threshold_aplicado: number;
    minimum_threshold_origen: string;
  };
  materialidad_por_area: DashboardAreaMaterialidad[];
  top_areas: AreaRiesgo[];
  top_areas_page: number;
  top_areas_page_size: number;
  top_areas_total: number;
  top_areas_has_more: boolean;
}
