export type RatioStatus = "ok" | "warning" | "risk";

export interface FinancialRatio {
  label: string;
  formatted: string;
  rawValue: number;
  benchmark: string;
  status: RatioStatus;
  audit_note: string;
  nia: string;
  category: "liquidez" | "solvencia" | "rentabilidad";
}

export function statusColors(status: RatioStatus): {
  card: string;
  value: string;
  badge: string;
} {
  if (status === "ok") {
    return {
      card: "bg-emerald-50 border-emerald-200",
      value: "text-emerald-700",
      badge: "bg-emerald-100 text-emerald-800",
    };
  }
  if (status === "warning") {
    return {
      card: "bg-amber-50 border-amber-200",
      value: "text-amber-700",
      badge: "bg-amber-100 text-amber-800",
    };
  }
  return {
    card: "bg-rose-50 border-rose-200",
    value: "text-rose-700",
    badge: "bg-rose-100 text-rose-800",
  };
}

export function statusLabel(status: RatioStatus): string {
  if (status === "ok") return "Normal";
  if (status === "warning") return "Atención";
  return "Riesgo";
}

export const CATEGORY_LABELS: Record<FinancialRatio["category"], string> = {
  liquidez: "Liquidez",
  solvencia: "Solvencia",
  rentabilidad: "Rentabilidad",
};

export const RATIO_FORMULAS: Record<string, string> = {
  "Liquidez Corriente": "Activo Corriente / Pasivo Corriente",
  "Prueba Ácida": "(Activo Corriente - Inventarios) / Pasivo Corriente",
  "Capital de Trabajo": "Activo Corriente - Pasivo Corriente",
  Endeudamiento: "Pasivo Total / Activo Total",
  Apalancamiento: "Pasivo Total / Patrimonio",
  ROA: "Resultado del Periodo / Activo Total",
  ROE: "Resultado del Periodo / Patrimonio",
  "Margen Neto": "Resultado del Periodo / Ingresos",
};
