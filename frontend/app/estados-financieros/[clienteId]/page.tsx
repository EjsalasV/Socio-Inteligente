"use client";

import { useMemo } from "react";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import { formatMoney } from "../../../lib/formatters";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import { useDashboard } from "../../../lib/hooks/useDashboard";
import { useLearningRole } from "../../../lib/hooks/useLearningRole";

// Clasificación de códigos LS por tipo de balance
const AC_CODES = new Set(["140", "141", "130", "130.1", "130.2", "120", "110", "135", "136"]);
const PC_CODES = new Set(["425", "300.1", "324", "410", "420"]);
const INV_CODES = new Set(["110"]);

type RatioStatus = "ok" | "warning" | "risk";

interface Ratio {
  label: string;
  formatted: string;
  rawValue: number;
  benchmark: string;
  status: RatioStatus;
  audit_note: string;
  nia: string;
  category: "liquidez" | "solvencia" | "rentabilidad";
}

function statusColors(s: RatioStatus) {
  if (s === "ok") return { card: "bg-emerald-50 border-emerald-200", value: "text-emerald-700", badge: "bg-emerald-100 text-emerald-800", dot: "bg-emerald-500" };
  if (s === "warning") return { card: "bg-amber-50 border-amber-200", value: "text-amber-700", badge: "bg-amber-100 text-amber-800", dot: "bg-amber-500" };
  return { card: "bg-rose-50 border-rose-200", value: "text-rose-700", badge: "bg-rose-100 text-rose-800", dot: "bg-rose-600" };
}

function statusLabel(s: RatioStatus) {
  if (s === "ok") return "Normal";
  if (s === "warning") return "Atención";
  return "Riesgo";
}

function buildRatios(params: {
  activo: number; pasivo: number; patrimonio: number;
  ingresos: number; resultado_periodo: number;
  ac: number; pc: number; inventarios: number;
}): Ratio[] {
  const { activo, pasivo, patrimonio, ingresos, resultado_periodo, ac, pc, inventarios } = params;
  const list: Ratio[] = [];

  // --- Liquidez ---
  if (ac > 0 && pc > 0) {
    const v = ac / pc;
    list.push({
      label: "Liquidez Corriente",
      formatted: v.toFixed(2) + "x",
      rawValue: v,
      benchmark: "> 1.5x óptimo",
      status: v >= 1.5 ? "ok" : v >= 1.0 ? "warning" : "risk",
      audit_note: v < 1.0
        ? "Activo corriente no cubre pasivo corriente. Evaluar going concern (NIA 570)."
        : v < 1.5
        ? "Liquidez ajustada. Revisar plazos de cobro y pago."
        : "Liquidez suficiente para cubrir obligaciones de corto plazo.",
      nia: "NIA 570",
      category: "liquidez",
    });

    const prueba = (ac - inventarios) / pc;
    list.push({
      label: "Prueba Ácida",
      formatted: prueba.toFixed(2) + "x",
      rawValue: prueba,
      benchmark: "> 1.0x óptimo",
      status: prueba >= 1.0 ? "ok" : prueba >= 0.7 ? "warning" : "risk",
      audit_note: prueba < 0.7
        ? "Alta dependencia de inventarios para cubrir deuda corriente. Revisar valuación y rotación."
        : prueba < 1.0
        ? "Liquidez inmediata ajustada. Monitorear rotación de cartera."
        : "Liquidez inmediata adecuada sin depender de inventarios.",
      nia: "NIA 500",
      category: "liquidez",
    });
  }

  if (ac > 0 || pc > 0) {
    const kt = ac - pc;
    list.push({
      label: "Capital de Trabajo",
      formatted: formatMoney(kt, "USD", 0),
      rawValue: kt,
      benchmark: "Debe ser positivo",
      status: kt > 0 ? "ok" : "risk",
      audit_note: kt < 0
        ? "Capital de trabajo negativo: obligaciones corrientes superan activos líquidos. Going concern en evaluación."
        : "La empresa mantiene colchón operativo positivo.",
      nia: "NIA 570",
      category: "liquidez",
    });
  }

  // --- Solvencia ---
  if (activo > 0) {
    const v = pasivo / activo;
    list.push({
      label: "Endeudamiento",
      formatted: (v * 100).toFixed(1) + "%",
      rawValue: v,
      benchmark: "< 60% óptimo",
      status: v < 0.6 ? "ok" : v < 0.75 ? "warning" : "risk",
      audit_note: v > 0.75
        ? "Alta dependencia de deuda. Presión sobre la gerencia — revisar incentivos de fraude (NIA 240)."
        : v > 0.6
        ? "Endeudamiento elevado. Verificar cumplimiento de covenants bancarios."
        : "Nivel de deuda manejable dentro del activo total.",
      nia: "NIA 240",
      category: "solvencia",
    });
  }

  if (patrimonio > 0) {
    const v = pasivo / patrimonio;
    list.push({
      label: "Apalancamiento",
      formatted: v.toFixed(2) + "x",
      rawValue: v,
      benchmark: "< 1.0x óptimo",
      status: v < 1.0 ? "ok" : v < 2.0 ? "warning" : "risk",
      audit_note: v > 2.0
        ? "Deuda más del doble del patrimonio. Riesgo significativo de incumplimiento de obligaciones."
        : v > 1.0
        ? "Pasivos superan al patrimonio. Vigilar estructura de financiamiento."
        : "Estructura de capital equilibrada.",
      nia: "NIA 315",
      category: "solvencia",
    });
  }

  // --- Rentabilidad ---
  if (activo > 0 && resultado_periodo !== 0) {
    const v = resultado_periodo / activo;
    list.push({
      label: "ROA",
      formatted: (v * 100).toFixed(1) + "%",
      rawValue: v,
      benchmark: "> 3% óptimo",
      status: v >= 0.03 ? "ok" : v >= 0 ? "warning" : "risk",
      audit_note: v < 0
        ? "Resultado negativo: destruye valor sobre activos. Evaluar going concern y presión sobre resultados."
        : v < 0.03
        ? "Rentabilidad baja sobre activos. Posible presión de gerencia para manipular cifras."
        : "Rentabilidad sobre activos aceptable.",
      nia: "NIA 240",
      category: "rentabilidad",
    });
  }

  if (patrimonio > 0 && resultado_periodo !== 0) {
    const v = resultado_periodo / patrimonio;
    list.push({
      label: "ROE",
      formatted: (v * 100).toFixed(1) + "%",
      rawValue: v,
      benchmark: "> 5% óptimo",
      status: v >= 0.05 ? "ok" : v >= 0 ? "warning" : "risk",
      audit_note: v < 0
        ? "Resultado negativo: erosiona el patrimonio. Evaluar continuidad del negocio."
        : v < 0.05
        ? "Retorno bajo para los accionistas. Riesgo de presión sobre resultados."
        : "Retorno al accionista adecuado.",
      nia: "NIA 570",
      category: "rentabilidad",
    });
  }

  if (ingresos > 0) {
    const v = resultado_periodo / ingresos;
    list.push({
      label: "Margen Neto",
      formatted: (v * 100).toFixed(1) + "%",
      rawValue: v,
      benchmark: "> 5% óptimo",
      status: v >= 0.05 ? "ok" : v >= 0 ? "warning" : "risk",
      audit_note: v < 0
        ? "Empresa opera a pérdida. Revisar reconocimiento de ingresos y gastos (NIA 540)."
        : v < 0.05
        ? "Margen muy ajustado. Errores en ingresos/gastos impactan materialmente el resultado."
        : "Margen neto saludable.",
      nia: "NIA 540",
      category: "rentabilidad",
    });
  }

  return list;
}

const CATEGORY_LABELS: Record<string, string> = {
  liquidez: "Liquidez",
  solvencia: "Solvencia",
  rentabilidad: "Rentabilidad",
};

export default function IndicesFinancierosPage() {
  const { clienteId } = useAuditContext();
  const { data, isLoading, error } = useDashboard(clienteId);
  const { role } = useLearningRole();

  const { ac, pc, inventarios } = useMemo(() => {
    let ac = 0, pc = 0, inv = 0;
    for (const area of (data?.top_areas ?? [])) {
      if (!area.con_saldo) continue;
      const code = area.codigo.toString().trim();
      const base = code.includes(".") ? code.split(".")[0] : code;
      if (AC_CODES.has(code) || AC_CODES.has(base)) ac += Math.abs(area.saldo_total);
      if (PC_CODES.has(code) || PC_CODES.has(base)) pc += Math.abs(area.saldo_total);
      if (INV_CODES.has(code) || INV_CODES.has(base)) inv += Math.abs(area.saldo_total);
    }
    return { ac, pc, inventarios: inv };
  }, [data]);

  const ratios = useMemo(() => {
    if (!data) return [];
    return buildRatios({
      activo: data.activo,
      pasivo: data.pasivo,
      patrimonio: data.patrimonio,
      ingresos: data.ingresos,
      resultado_periodo: data.resultado_periodo,
      ac, pc, inventarios,
    });
  }, [data, ac, pc, inventarios]);

  const riskRatios = ratios.filter(r => r.status === "risk");
  const warningRatios = ratios.filter(r => r.status === "warning");

  const categories = ["liquidez", "solvencia", "rentabilidad"] as const;

  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorMessage message={error} />;
  if (!data) return <ErrorMessage message="No hay datos para analizar." />;

  return (
    <div className="pt-4 pb-10 space-y-8 max-w-screen-2xl">

      {/* Header */}
      <header className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          <p className="text-[10px] uppercase tracking-[0.16em] text-slate-500 font-bold">Análisis Financiero</p>
          <h1 className="font-headline text-4xl text-[#041627] mt-1">Índices Financieros</h1>
          <p className="text-sm text-slate-500 mt-2">
            {data.nombre_cliente} · {data.periodo || "Periodo actual"} · Sector: {data.sector || "N/D"}
          </p>
        </div>
        <div className="flex gap-3">
          {riskRatios.length > 0 && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-rose-100 text-rose-800 text-xs font-bold">
              <span className="h-2 w-2 rounded-full bg-rose-600 inline-block" />
              {riskRatios.length} señal{riskRatios.length > 1 ? "es" : ""} de riesgo
            </span>
          )}
          {warningRatios.length > 0 && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-amber-100 text-amber-800 text-xs font-bold">
              <span className="h-2 w-2 rounded-full bg-amber-500 inline-block" />
              {warningRatios.length} en atención
            </span>
          )}
        </div>
      </header>

      {/* Panel de rol */}
      {role === "junior" && (
        <section className="bg-[#a5eff0]/10 border border-[#a5eff0]/30 rounded-xl p-6">
          <div className="flex items-start gap-4">
            <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#041627] text-[#a5eff0] text-xs font-bold mt-0.5">NIA</span>
            <div>
              <p className="text-xs uppercase tracking-[0.15em] text-[#041627]/60 font-bold mb-1">Cómo usar los índices — Vista Junior</p>
              <p className="text-sm text-[#041627] leading-relaxed">
                Los índices financieros te dicen si el cliente tiene problemas de liquidez, demasiada deuda o resultados que justifican presión sobre la gerencia.
                Cualquier índice en <strong>rojo</strong> es una señal que debes investigar: puede indicar riesgo de fraude (NIA 240), going concern (NIA 570) o errores en el reconocimiento de cifras (NIA 540).
              </p>
            </div>
          </div>
        </section>
      )}

      {role === "socio" && (riskRatios.length > 0 || warningRatios.length > 0) && (
        <section className="rounded-xl p-6 bg-[#001919] border border-[#a5eff0]/20 shadow-md text-white">
          <p className="text-[10px] uppercase tracking-[0.2em] text-[#a5eff0] font-bold mb-3">Señales Ejecutivas — Vista Socio</p>
          <div className="flex flex-wrap gap-3">
            {[...riskRatios, ...warningRatios].map(r => (
              <div key={r.label} className={`px-4 py-3 rounded-lg ${r.status === "risk" ? "bg-rose-900/40 border border-rose-700/50" : "bg-amber-900/40 border border-amber-700/50"}`}>
                <p className="text-xs font-bold text-white">{r.label}: <span className={r.status === "risk" ? "text-rose-300" : "text-amber-300"}>{r.formatted}</span></p>
                <p className="text-[11px] text-slate-300 mt-0.5">{r.nia}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Totales del balance */}
      <section className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {[
          { label: "Activo Total", value: formatMoney(data.activo, "USD", 0) },
          { label: "Pasivo Total", value: formatMoney(data.pasivo, "USD", 0) },
          { label: "Patrimonio", value: formatMoney(data.patrimonio, "USD", 0) },
          { label: "Ingresos", value: formatMoney(data.ingresos, "USD", 0) },
          { label: "Resultado", value: formatMoney(data.resultado_periodo, "USD", 0), highlight: data.resultado_periodo < 0 },
        ].map(kpi => (
          <div key={kpi.label} className="bg-white rounded-xl p-5 shadow-sm border border-slate-200/60">
            <p className="text-[10px] uppercase tracking-[0.15em] text-slate-500 font-bold">{kpi.label}</p>
            <p className={`font-headline text-2xl mt-1 font-semibold ${kpi.highlight ? "text-rose-700" : "text-[#041627]"}`}>{kpi.value}</p>
          </div>
        ))}
      </section>

      {/* Ratios por categoría */}
      {categories.map(cat => {
        const catRatios = ratios.filter(r => r.category === cat);
        if (catRatios.length === 0) return null;
        return (
          <section key={cat}>
            <h2 className="font-headline text-2xl text-[#041627] mb-4">{CATEGORY_LABELS[cat]}</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {catRatios.map(ratio => {
                const c = statusColors(ratio.status);
                return (
                  <article key={ratio.label} className={`rounded-xl p-6 border ${c.card} shadow-sm`}>
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <p className="font-semibold text-[#041627] text-sm">{ratio.label}</p>
                      <span className={`shrink-0 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${c.badge}`}>
                        {statusLabel(ratio.status)}
                      </span>
                    </div>
                    <p className={`font-headline text-3xl font-semibold mb-1 ${c.value}`}>{ratio.formatted}</p>
                    <p className="text-[11px] text-slate-500 mb-3">{ratio.benchmark}</p>
                    <div className="border-t border-black/5 pt-3">
                      <p className="text-xs text-slate-600 leading-relaxed">{ratio.audit_note}</p>
                      <span className="inline-block mt-2 px-2 py-0.5 rounded-full bg-[#041627]/8 text-[#041627] text-[10px] font-bold">{ratio.nia}</span>
                    </div>
                  </article>
                );
              })}
            </div>
          </section>
        );
      })}

      {ratios.length === 0 && (
        <section className="bg-white rounded-xl p-10 text-center border border-slate-200/50 shadow-sm">
          <p className="text-slate-500 text-sm">No hay suficientes datos para calcular índices.</p>
          <p className="text-xs text-slate-400 mt-2">Carga el Trial Balance y configura la materialidad en el Perfil para habilitar el análisis.</p>
        </section>
      )}

      {/* Nota metodológica */}
      {ratios.length > 0 && (
        <p className="text-[11px] text-slate-400">
          Los índices de liquidez (corriente y prueba ácida) se estiman a partir de las áreas con saldo cargadas en el Trial Balance clasificadas por código LS.
          Los valores de activo, pasivo, patrimonio e ingresos provienen del balance auditado.
        </p>
      )}
    </div>
  );
}
