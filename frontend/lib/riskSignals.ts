import type { RiskCriticalArea } from "../types/risk";

export type RiskSignalSource = "industry" | "mayor" | "mixed" | "base";

export type RiskSignalSummary = {
  areaId: string;
  areaName: string;
  score: number;
  nivel: string;
  drivers: string[];
  source: RiskSignalSource;
  industryBoost: number;
  mayorBoost: number;
  totalBoost: number;
  topComponents: Array<{ key: string; label: string; value: number }>;
};

const COMPONENT_LABELS: Record<string, string> = {
  industry_boost: "Ajuste por industria",
  mayor_boost: "Ajuste por mayor",
  base_model: "Modelo base",
  industry_overdue_policy: "Política de vencimiento",
  industry_provision_pressure: "Cobertura de provisiones",
  industry_liquidity_exposure: "Exposición de liquidez",
  industry_inventory_mix: "Mix de inventario",
  industry_inventory_rotation: "Rotación de inventario",
  industry_cutoff_consignment: "Consignaciones y corte",
  industry_retail_collections: "Cobranza retail",
  industry_project_accounting: "Contabilidad por proyectos",
  industry_customer_advances: "Anticipos de clientes",
  industry_service_warranty: "Garantías de servicio",
  industry_wip_exposure: "Exposición WIP",
  industry_wip_baseline: "Umbral WIP",
  industry_standard_costs: "Costos estándar",
  industry_capex_pipeline: "Capex en construcción",
  industry_related_parties: "Transacciones relacionadas",
  industry_control_changes: "Cambios de control",
  industry_group_guarantees: "Garantías del grupo",
  industry_insurer_exposure: "Dependencia de seguros",
  industry_medicine_obsolescence: "Obsolescencia de medicinas",
  industry_long_collections: "Cobranza extendida",
  industry_student_ar_window: "Ventana de cartera estudiantil",
  industry_scholarship_pressure: "Presión por becas",
  industry_endowment: "Fondo patrimonial",
  industry_research_revenue: "Ingresos de investigación",
  closing_entries: "Asientos de cierre",
  user_spike: "Concentración por usuario",
  reversals: "Reversiones y ajustes",
  dormant_accounts: "Cuentas concentradas",
  tb_mayor_gap: "Brecha TB vs Mayor",
};

function prettifyKey(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function getRiskSignalSource(area: RiskCriticalArea): RiskSignalSource {
  const industryBoost = Number(area.score_components?.industry_boost ?? 0);
  const mayorBoost = Number(area.score_components?.mayor_boost ?? 0);
  if (industryBoost > 0 && mayorBoost > 0) return "mixed";
  if (industryBoost > 0) return "industry";
  if (mayorBoost > 0) return "mayor";
  return "base";
}

export function getRiskSignalSummary(area: RiskCriticalArea): RiskSignalSummary {
  const components = area.score_components ?? {};
  const industryBoost = Number(components.industry_boost ?? 0);
  const mayorBoost = Number(components.mayor_boost ?? 0);

  const topComponents = Object.entries(components)
    .filter(([key, value]) => key !== "base_model" && key !== "industry_boost" && key !== "mayor_boost" && Number(value) > 0)
    .sort((a, b) => Number(b[1]) - Number(a[1]))
    .slice(0, 3)
    .map(([key, value]) => ({
      key,
      label: COMPONENT_LABELS[key] ?? prettifyKey(key),
      value: Number(value),
    }));

  return {
    areaId: area.area_id,
    areaName: area.area_nombre,
    score: area.score,
    nivel: area.nivel,
    drivers: area.drivers ?? [],
    source: getRiskSignalSource(area),
    industryBoost,
    mayorBoost,
    totalBoost: Number((industryBoost + mayorBoost).toFixed(2)),
    topComponents,
  };
}

export function summarizeRiskSignals(areas: RiskCriticalArea[]) {
  const summaries = areas.map(getRiskSignalSummary);
  const withIndustry = summaries.filter((item) => item.industryBoost > 0);
  const withMayor = summaries.filter((item) => item.mayorBoost > 0);
  const withAnyBoost = summaries.filter((item) => item.totalBoost > 0);

  return {
    summaries,
    withIndustry,
    withMayor,
    withAnyBoost,
    totalIndustryBoost: Number(withIndustry.reduce((acc, item) => acc + item.industryBoost, 0).toFixed(2)),
    totalMayorBoost: Number(withMayor.reduce((acc, item) => acc + item.mayorBoost, 0).toFixed(2)),
  };
}
