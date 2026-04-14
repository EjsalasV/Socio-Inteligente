"use client";

/**
 * Vista Semi Senior — intermedia entre Junior y Senior.
 * Muestra acciones concretas + análisis técnico sin la verbosidad del junior.
 */

import { formatMoney } from "../../../lib/formatters";
import DashboardGrid from "../DashboardGrid";
import type { DashboardData } from "../../../types/dashboard";

type Props = { data: DashboardData };

function barColor(p: string) {
  const n = p.toLowerCase();
  if (n === "alta") return "bg-rose-600";
  if (n === "media") return "bg-amber-500";
  return "bg-emerald-600";
}

function riskPct(score: number) {
  if (score <= 1) return Math.max(0, Math.min(100, score * 100));
  return Math.max(0, Math.min(100, score));
}

export default function DashboardSemi({ data }: Props) {
  const progreso = Math.max(0, Math.min(100, data.progreso_auditoria ?? 0));
  const orderedAreas = [...(data.top_areas ?? [])].filter((a) => a.con_saldo).sort((a, b) => b.score_riesgo - a.score_riesgo);
  const mat = data.materialidad_ejecucion > 0 ? data.materialidad_ejecucion : data.materialidad_global;

  const fase = (data.workflow_phase || data.fase_actual || "").toLowerCase();
  const etapa =
    fase.includes("inform") || fase.includes("cierre") ? "Informe"
    : fase.includes("ejec") || fase.includes("visita") ? "Ejecución"
    : fase.includes("plan") ? "Planificación"
    : "Sin definir";

  const topArea = orderedAreas[0];

  return (
    <div className="space-y-8 pb-8">

      {/* Header Semi */}
      <section className="rounded-xl p-7 shadow-md text-white bg-gradient-to-br from-[#041627] to-[#163550] border border-[#041627]/20">
        <div className="flex items-center gap-3 mb-1">
          <span className="text-xs uppercase tracking-[0.2em] text-[#a5eff0] font-semibold">Vista Semi Senior</span>
        </div>
        <h2 className="font-headline text-4xl text-white mt-1">Dashboard de Auditoría</h2>
        <p className="text-slate-300 mt-2 text-sm">
          <span className="font-semibold text-white">{data.nombre_cliente}</span>
          {" · "}Fase: <span className="font-semibold text-white">{etapa}</span>
          {" · "}Riesgo: <span className="font-semibold text-white">{(data.riesgo_global || "N/D").toUpperCase()}</span>
        </p>
      </section>

      {/* KPIs */}
      <DashboardGrid data={data} />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">

        {/* Ranking + foco de trabajo */}
        <div className="xl:col-span-8 space-y-6">

          <section className="bg-white rounded-xl p-7 shadow-sm border border-slate-200/50">
            <div className="flex items-center justify-between mb-5">
              <h3 className="font-headline text-2xl text-[#041627] font-semibold">Áreas por Riesgo</h3>
              <span className="text-[10px] uppercase tracking-[0.15em] text-slate-500 font-bold">Score de riesgo</span>
            </div>
            <div className="space-y-4">
              {orderedAreas.slice(0, 5).map((area) => {
                const pct = Math.max(8, riskPct(area.score_riesgo));
                return (
                  <div key={`${area.codigo}-${area.nombre}`} className="space-y-1.5">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-semibold text-[#041627]">{area.codigo} — {area.nombre}</span>
                      <span className="text-xs text-slate-400">{riskPct(area.score_riesgo).toFixed(1)}</span>
                    </div>
                    <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                      <div className={`h-full rounded-full ${barColor(area.prioridad)}`} style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
              {orderedAreas.length === 0 && <p className="text-sm text-slate-400">Sin áreas con saldo.</p>}
            </div>
          </section>

          {/* Foco de trabajo */}
          {topArea && (
            <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-200/50">
              <h4 className="font-headline text-xl text-[#041627] font-semibold mb-3">Foco prioritario</h4>
              <div className="flex items-start justify-between gap-4 p-4 rounded-lg bg-rose-50 border border-rose-100">
                <div>
                  <p className="font-bold text-[#041627] text-sm">{topArea.codigo} — {topArea.nombre}</p>
                  <p className="text-xs text-slate-500 mt-1">{formatMoney(topArea.saldo_total, "USD", 0)} · Prioridad {topArea.prioridad.toUpperCase()}</p>
                  <p className="text-xs text-slate-600 mt-2">Aplicar NIA 500 — obtener evidencia sustantiva suficiente y apropiada para afirmaciones en riesgo.</p>
                </div>
                <span className="shrink-0 px-2.5 py-1 rounded-full bg-rose-100 text-rose-800 text-[11px] font-bold uppercase">Alta</span>
              </div>
            </section>
          )}
        </div>

        {/* Panel derecho */}
        <div className="xl:col-span-4 space-y-5">

          {/* Avance */}
          <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-200/50">
            <h4 className="font-headline text-xl text-[#041627] mb-3">Avance</h4>
            <div className="flex items-end gap-2 mb-3">
              <span className="font-headline text-3xl text-[#041627] font-semibold">{Math.round(progreso)}%</span>
              <span className="text-xs text-slate-400 pb-1">{etapa}</span>
            </div>
            <div className="h-3 rounded-full bg-slate-100 overflow-hidden">
              <div className="h-full rounded-full bg-[#041627]" style={{ width: `${progreso}%` }} />
            </div>
          </section>

          {/* Materialidad */}
          <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-200/50">
            <h4 className="font-headline text-xl text-[#041627] mb-3">Materialidad</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Ejecución</span>
                <span className="font-semibold text-[#041627]">{mat > 0 ? formatMoney(mat, "USD", 0) : "N/D"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Trivial</span>
                <span className="font-semibold text-[#041627]">{data.umbral_trivial > 0 ? formatMoney(data.umbral_trivial, "USD", 0) : "N/D"}</span>
              </div>
            </div>
            <p className="text-[10px] text-slate-400 mt-3">NIA 320</p>
          </section>

          {/* Quality Gates si existen */}
          {data.workflow_gates?.length ? (
            <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-200/50">
              <h4 className="font-headline text-xl text-[#041627] mb-3">Quality Gates</h4>
              <div className="space-y-2">
                {data.workflow_gates.map((gate) => (
                  <div key={gate.code} className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-[#041627]">{gate.code}</span>
                    <span className={`px-2 py-0.5 rounded-full font-bold uppercase ${gate.status === "ok" ? "bg-emerald-100 text-emerald-800" : "bg-rose-100 text-rose-800"}`}>
                      {gate.status === "ok" ? "OK" : "Bloqueado"}
                    </span>
                  </div>
                ))}
              </div>
            </section>
          ) : null}

        </div>
      </div>
    </div>
  );
}
