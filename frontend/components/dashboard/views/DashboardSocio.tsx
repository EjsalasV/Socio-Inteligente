"use client";

import { formatMoney } from "../../../lib/formatters";
import type { DashboardData } from "../../../types/dashboard";

type Props = { data: DashboardData };

function riskColor(nivel: string) {
  const n = nivel.toLowerCase();
  if (n === "alto" || n === "critico") return { bg: "bg-rose-100", text: "text-rose-800", dot: "bg-rose-600" };
  if (n === "media" || n === "medio") return { bg: "bg-amber-100", text: "text-amber-800", dot: "bg-amber-500" };
  return { bg: "bg-emerald-100", text: "text-emerald-800", dot: "bg-emerald-600" };
}

function buildPerspective(data: DashboardData): string {
  const riesgo = (data.riesgo_global || "medio").toUpperCase();
  const mat = data.materialidad_ejecucion > 0 ? data.materialidad_ejecucion : data.materialidad_global;
  const topArea = data.top_areas?.filter((a) => a.con_saldo)[0];
  const topNombre = topArea ? `${topArea.codigo} - ${topArea.nombre}` : "No determinado";
  const fase = (data.workflow_phase || data.fase_actual || "planificación");
  const textoRiesgo: Record<string, string> = {
    ALTO: "elevado — se requieren procedimientos sustantivos extensos",
    MEDIO: "moderado — enfoque en pruebas de controles clave",
    BAJO: "controlado — mayor confianza en controles internos",
  };
  const desc = textoRiesgo[riesgo] ?? "en evaluación";
  return (
    `El encargo de ${data.nombre_cliente || "este cliente"} presenta riesgo ${desc}. ` +
    `Avance ${Math.round(data.progreso_auditoria ?? 0)}% en fase de ${fase}. ` +
    `Área con mayor exposición: ${topNombre}. ` +
    (mat > 0 ? `Materialidad de ejecución $${mat.toLocaleString("es-CO")}. ` : "") +
    `Focalizar esfuerzo restante en evidencia sustantiva para aseveraciones de integridad y exactitud.`
  );
}

export default function DashboardSocio({ data }: Props) {
  const progreso = Math.max(0, Math.min(100, data.progreso_auditoria ?? 0));
  const orderedAreas = [...(data.top_areas ?? [])].filter((a) => a.con_saldo).sort((a, b) => b.score_riesgo - a.score_riesgo);
  const mat = data.materialidad_ejecucion > 0 ? data.materialidad_ejecucion : data.materialidad_global;
  const perspective = buildPerspective(data);

  const fase = (data.workflow_phase || data.fase_actual || "").toLowerCase();
  const etapa =
    fase.includes("inform") || fase.includes("cierre") ? "Informe"
    : fase.includes("ejec") || fase.includes("visita") ? "Ejecución"
    : fase.includes("plan") ? "Planificación"
    : "Sin definir";

  return (
    <div className="space-y-8 pb-8">

      {/* Header Socio */}
      <section className="rounded-xl p-7 shadow-md text-white bg-gradient-to-br from-[#041627] to-[#1a2b3c] border border-[#041627]/20">
        <div className="flex items-center gap-3 mb-1">
          <span className="text-xs uppercase tracking-[0.2em] text-[#a5eff0] font-semibold">Vista Socio</span>
          <span className="px-2 py-0.5 rounded-full bg-[#a5eff0]/20 text-[#a5eff0] text-[10px] font-bold uppercase tracking-wider">Ejecutivo</span>
        </div>
        <h2 className="font-headline text-4xl text-white mt-1">Dashboard del Encargo</h2>
        <p className="text-slate-300 mt-2 text-sm">
          <span className="font-semibold text-white">{data.nombre_cliente}</span>
          {" · "}Período <span className="font-semibold text-white">{data.periodo || "Actual"}</span>
          {" · "}Sector <span className="font-semibold text-white">{data.sector || "N/D"}</span>
        </p>
      </section>

      {/* Perspectiva del Socio — prominente */}
      <section className="rounded-xl p-6 bg-[#001919] border border-[#a5eff0]/20 shadow-md">
        <p className="text-[10px] uppercase tracking-[0.2em] text-[#a5eff0] font-bold mb-2">Criterio AI — Perspectiva del Socio</p>
        <p className="text-white font-headline italic text-lg leading-relaxed">{perspective}</p>
        <p className="text-xs text-slate-400 mt-3">
          NIA 320 · Base: <strong className="text-slate-200">{data.materialidad_detalle?.base_usada || "N/D"}</strong>
          {" · "}% aplicado: <strong className="text-slate-200">{(data.materialidad_detalle?.porcentaje_aplicado ?? 0).toFixed(2)}%</strong>
        </p>
      </section>

      {/* KPIs ejecutivos — 4 métricas clave */}
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Riesgo Global", value: (data.riesgo_global || "N/D").toUpperCase(), sub: "Inherente + Control" },
          { label: "Materialidad", value: mat > 0 ? formatMoney(mat, "USD", 0) : "N/D", sub: "Ejecución NIA 320" },
          { label: "Avance", value: `${Math.round(progreso)}%`, sub: `Fase: ${etapa}` },
          { label: "Activo Total", value: formatMoney(data.activo, "USD", 0), sub: "Balance auditado" },
        ].map((kpi) => (
          <div key={kpi.label} className="bg-white rounded-xl p-5 shadow-sm border border-slate-200/60">
            <p className="text-[10px] uppercase tracking-[0.15em] text-slate-500 font-bold">{kpi.label}</p>
            <p className="font-headline text-2xl text-[#041627] mt-1 font-semibold">{kpi.value}</p>
            <p className="text-xs text-slate-400 mt-0.5">{kpi.sub}</p>
          </div>
        ))}
      </section>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">

        {/* Áreas de riesgo — vista ejecutiva top 3 */}
        <section className="xl:col-span-7 bg-white rounded-xl p-7 shadow-sm border border-slate-200/50">
          <div className="flex items-center justify-between mb-5">
            <h3 className="font-headline text-2xl text-[#041627] font-semibold">Áreas Críticas del Encargo</h3>
            <span className="text-[10px] uppercase tracking-[0.15em] text-slate-500 font-bold">Top {Math.min(3, orderedAreas.length)}</span>
          </div>
          <div className="space-y-4">
            {orderedAreas.slice(0, 3).map((area) => {
              const c = riskColor(area.prioridad);
              return (
                <div key={`${area.codigo}-${area.nombre}`} className="flex items-center justify-between p-4 rounded-lg bg-slate-50 border border-slate-100">
                  <div>
                    <p className="font-semibold text-[#041627] text-sm">{area.codigo} — {area.nombre}</p>
                    <p className="text-xs text-slate-500 mt-0.5">Saldo: {formatMoney(area.saldo_total, "USD", 0)}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${c.bg} ${c.text}`}>
                    {area.prioridad}
                  </span>
                </div>
              );
            })}
            {orderedAreas.length === 0 && (
              <p className="text-sm text-slate-400">Sin áreas con saldo relevante.</p>
            )}
          </div>
        </section>

        {/* Panel derecho: Quality Gates + Ciclo de vida */}
        <div className="xl:col-span-5 space-y-5">

          {/* Quality Gates */}
          {data.workflow_gates?.length ? (
            <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-200/50">
              <h4 className="font-headline text-xl text-[#041627] mb-4">Quality Gates</h4>
              <div className="space-y-3">
                {data.workflow_gates.map((gate) => (
                  <div key={gate.code} className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-semibold text-[#041627]">{gate.code}</p>
                      <p className="text-[11px] text-slate-500">{gate.title}</p>
                    </div>
                    <span className={`px-2.5 py-1 rounded-full text-[11px] font-bold uppercase ${gate.status === "ok" ? "bg-emerald-100 text-emerald-800" : "bg-rose-100 text-rose-800"}`}>
                      {gate.status === "ok" ? "OK" : "Bloqueado"}
                    </span>
                  </div>
                ))}
              </div>
            </section>
          ) : null}

          {/* Ciclo de vida */}
          <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-200/50">
            <h4 className="font-headline text-xl text-[#041627] mb-4">Fase del Encargo</h4>
            <div className="space-y-3">
              {["Planificación", "Ejecución", "Informe"].map((step) => {
                const done = (step === "Planificación" && ["Planificación","Ejecución","Informe"].includes(etapa))
                  || (step === "Ejecución" && ["Ejecución","Informe"].includes(etapa))
                  || (step === "Informe" && etapa === "Informe");
                const active = step === etapa;
                return (
                  <div key={step} className={`flex items-center gap-3 p-3 rounded-lg ${active ? "bg-[#041627]/5 border border-[#041627]/10" : ""}`}>
                    <span className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${done ? "bg-emerald-600 text-white" : "bg-slate-200 text-slate-400"}`}>
                      {done ? "✓" : ""}
                    </span>
                    <span className={`text-sm ${active ? "font-bold text-[#041627]" : done ? "text-[#041627]" : "text-slate-400"}`}>{step}</span>
                    {active && <span className="ml-auto text-[10px] uppercase tracking-wide text-[#041627]/60 font-bold">Actual</span>}
                  </div>
                );
              })}
            </div>
          </section>

        </div>
      </div>
    </div>
  );
}
