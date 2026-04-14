"use client";

import { formatMoney } from "../../../lib/formatters";
import DashboardGrid from "../DashboardGrid";
import type { DashboardData } from "../../../types/dashboard";

type Props = { data: DashboardData };

function riskPct(score: number): number {
  if (score <= 1) return Math.max(0, Math.min(100, score * 100));
  return Math.max(0, Math.min(100, score));
}

function barColor(prioridad: string): string {
  const p = prioridad.toLowerCase();
  if (p === "alta") return "bg-rose-600";
  if (p === "media") return "bg-amber-500";
  return "bg-emerald-600";
}

export default function DashboardSenior({ data }: Props) {
  const progreso = Math.max(0, Math.min(100, data.progreso_auditoria ?? 0));
  const orderedAreas = [...(data.top_areas ?? [])].filter((a) => a.con_saldo).sort((a, b) => b.score_riesgo - a.score_riesgo);
  const mat = data.materialidad_ejecucion > 0 ? data.materialidad_ejecucion : data.materialidad_global;

  const fase = (data.workflow_phase || data.fase_actual || "").toLowerCase();
  const etapa =
    fase.includes("inform") || fase.includes("cierre") ? "Informe"
    : fase.includes("ejec") || fase.includes("visita") ? "Ejecución"
    : fase.includes("plan") ? "Planificación"
    : "Sin definir";

  const tbLabel: Record<string, string> = {
    final: "Corte Final", preliminar: "Corte Preliminar", inicial: "Corte Inicial", sin_saldos: "Sin saldos",
  };

  return (
    <div className="space-y-8 pb-8">

      {/* Header Senior */}
      <section className="rounded-xl p-7 shadow-md text-white bg-gradient-to-br from-[#041627] to-[#1a3550] border border-[#041627]/20">
        <div className="flex items-center gap-3 mb-1">
          <span className="text-xs uppercase tracking-[0.2em] text-[#a5eff0] font-semibold">Vista Senior</span>
          <span className="px-2 py-0.5 rounded-full bg-[#a5eff0]/20 text-[#a5eff0] text-[10px] font-bold uppercase tracking-wider">Análisis Técnico</span>
        </div>
        <h2 className="font-headline text-4xl text-white mt-1">Dashboard de Auditoría</h2>
        <p className="text-slate-300 mt-2 text-sm">
          <span className="font-semibold text-white">{data.nombre_cliente}</span>
          {" · "}TB: <span className="font-semibold text-white">{tbLabel[data.tb_stage] ?? data.tb_stage}</span>
          {" · "}Fase: <span className="font-semibold text-white">{etapa}</span>
          {" · "}Riesgo: <span className="font-semibold text-white">{(data.riesgo_global || "N/D").toUpperCase()}</span>
        </p>
      </section>

      {/* Balance KPIs completos */}
      <DashboardGrid data={data} />

      {/* Avance y materialidad técnica */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-200/50 md:col-span-2">
          <p className="text-[10px] uppercase tracking-[0.15em] text-slate-500 font-bold mb-2">Avance del Encargo</p>
          <div className="flex items-end gap-3 mb-3">
            <span className="font-headline text-4xl text-[#041627] font-semibold">{Math.round(progreso)}%</span>
            <span className="text-sm text-slate-500 pb-1">completado</span>
          </div>
          <div className="h-3 rounded-full bg-slate-100 overflow-hidden">
            <div className="h-full bg-[#041627] rounded-full transition-all" style={{ width: `${progreso}%` }} />
          </div>
          <div className="flex justify-between text-[11px] text-slate-400 mt-2">
            <span>Planificación</span><span>Ejecución</span><span>Informe</span>
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-200/50">
          <p className="text-[10px] uppercase tracking-[0.15em] text-slate-500 font-bold mb-3">Materialidad NIA 320</p>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-500">Global</span>
              <span className="font-semibold text-[#041627]">{data.materialidad_global > 0 ? formatMoney(data.materialidad_global, "USD", 0) : "N/D"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Ejecución</span>
              <span className="font-semibold text-[#041627]">{mat > 0 ? formatMoney(mat, "USD", 0) : "N/D"}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Trivial</span>
              <span className="font-semibold text-[#041627]">{data.umbral_trivial > 0 ? formatMoney(data.umbral_trivial, "USD", 0) : "N/D"}</span>
            </div>
            <div className="pt-1 border-t border-slate-100 flex justify-between text-[11px] text-slate-400">
              <span>Base</span>
              <span>{data.materialidad_detalle?.base_usada || "N/D"} · {(data.materialidad_detalle?.porcentaje_aplicado ?? 0).toFixed(2)}%</span>
            </div>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">

        {/* Ranking completo top 5 */}
        <section className="xl:col-span-8 bg-white rounded-xl p-7 shadow-sm border border-slate-200/50">
          <div className="flex items-center justify-between mb-5">
            <h3 className="font-headline text-2xl text-[#041627] font-semibold">Ranking de Riesgos por Área</h3>
            <span className="text-[10px] uppercase tracking-[0.15em] text-slate-500 font-bold">Score auditado</span>
          </div>
          <div className="space-y-4">
            {orderedAreas.slice(0, 5).map((area) => {
              const pct = Math.max(8, riskPct(area.score_riesgo));
              return (
                <div key={`${area.codigo}-${area.nombre}`} className="space-y-1.5">
                  <div className="flex items-center justify-between text-sm">
                    <div>
                      <span className="font-semibold text-[#041627]">{area.codigo} — {area.nombre}</span>
                      <span className="ml-3 text-xs text-slate-400">{formatMoney(area.saldo_total, "USD", 0)}</span>
                    </div>
                    <span className="font-mono text-slate-600 text-xs">{riskPct(area.score_riesgo).toFixed(1)}</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                    <div className={`h-full ${barColor(area.prioridad)} rounded-full`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
            {orderedAreas.length === 0 && <p className="text-sm text-slate-400">Sin áreas con saldo.</p>}
          </div>
        </section>

        {/* Panel derecho */}
        <div className="xl:col-span-4 space-y-5">

          {/* Quality Gates técnicos */}
          {data.workflow_gates?.length ? (
            <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-200/50">
              <h4 className="font-headline text-xl text-[#041627] mb-4">Quality Gates</h4>
              <div className="space-y-3">
                {data.workflow_gates.map((gate) => (
                  <div key={gate.code} className="space-y-0.5">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-[#041627]">{gate.code}</span>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${gate.status === "ok" ? "bg-emerald-100 text-emerald-800" : "bg-rose-100 text-rose-800"}`}>
                        {gate.status === "ok" ? "OK" : "Bloqueado"}
                      </span>
                    </div>
                    {gate.detail && <p className="text-[11px] text-slate-500">{gate.detail}</p>}
                  </div>
                ))}
              </div>
            </section>
          ) : null}

          {/* Balance status técnico */}
          <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-200/50">
            <h4 className="font-headline text-xl text-[#041627] mb-4">Estado del Balance</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Estado</span>
                <span className={`font-semibold ${data.balance_status === "cuadrado" ? "text-emerald-700" : "text-rose-700"}`}>
                  {data.balance_status === "cuadrado" ? "Cuadrado" : data.balance_status === "resultado_periodo" ? "Con resultado" : "Descuadrado"}
                </span>
              </div>
              {data.balance_delta !== 0 && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Delta</span>
                  <span className="font-mono text-xs text-slate-700">{formatMoney(Math.abs(data.balance_delta), "USD", 0)}</span>
                </div>
              )}
              {data.resultado_periodo !== 0 && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Resultado</span>
                  <span className={`font-mono text-xs ${data.resultado_periodo >= 0 ? "text-emerald-700" : "text-rose-700"}`}>
                    {formatMoney(data.resultado_periodo, "USD", 0)}
                  </span>
                </div>
              )}
            </div>
          </section>

        </div>
      </div>
    </div>
  );
}
