import DashboardGrid from "./DashboardGrid";
import type { DashboardData } from "../../types/dashboard";

type Props = {
  data: DashboardData;
};

export default function DashboardContent({ data }: Props) {
  const progreso = Math.max(0, Math.min(100, data.progreso_auditoria));
  const orderedAreas = [...(data.top_areas ?? [])].sort((a, b) => b.score_riesgo - a.score_riesgo);

  const riesgoTone =
    data.riesgo_global.toUpperCase() === "ALTO"
      ? "text-[#ba1a1a]"
      : data.riesgo_global.toUpperCase() === "MEDIO"
        ? "text-amber-700"
        : "text-emerald-700";

  const etapa =
    progreso >= 85 ? "Informe" : progreso >= 45 ? "Ejecucion" : "Planificacion";

  return (
    <div className="space-y-8 pb-8">
      <section className="rounded-editorial p-7 shadow-editorial text-white border border-[#041627]/20 bg-gradient-to-br from-[#041627] to-[#1a2b3c]">
        <p className="text-xs uppercase tracking-[0.2em] text-[#a5eff0] font-body">Centro de Mando de Auditoria - Socio AI</p>
        <h2 className="font-headline text-5xl text-white mt-2">Dashboard Ejecutivo</h2>
        <p className="font-body text-slate-200 mt-3 leading-relaxed text-base">
          Cliente: <span className="font-semibold text-white">{data.nombre_cliente}</span> ·
          Periodo: <span className="font-semibold text-white"> {data.periodo || "Actual"}</span> ·
          Sector: <span className="font-semibold text-white"> {data.sector || "N/D"}</span>
        </p>
      </section>

      <DashboardGrid data={data} />

      <section className="grid grid-cols-1 xl:grid-cols-12 gap-8">
        <div className="xl:col-span-8 space-y-6">
          <article className="sovereign-card">
            <div className="flex items-center justify-between gap-3 mb-5">
              <h3 className="font-headline text-3xl text-navy-900">Ranking de Riesgos por Area</h3>
              <span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Top Areas</span>
            </div>

            <div className="space-y-4">
              {orderedAreas.slice(0, 5).map((area) => {
                const pct = Math.max(8, Math.min(100, area.score_riesgo * 100));
                const bar =
                  area.prioridad.toLowerCase() === "alta"
                    ? "bg-[#ba1a1a]"
                    : area.prioridad.toLowerCase() === "media"
                      ? "bg-amber-500"
                      : "bg-emerald-600";

                return (
                  <div key={`${area.codigo}-${area.nombre}`} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-semibold text-navy-900">{area.codigo} - {area.nombre}</span>
                      <span className="text-slate-500 font-medium">{(area.score_riesgo * 100).toFixed(1)}%</span>
                    </div>
                    <div className="h-2 rounded-full bg-[#ebeef0] overflow-hidden">
                      <div className={`h-full ${bar}`} style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </article>

          <article className="risk-high">
            <div className="flex items-center gap-2 mb-2">
              <span className="material-symbols-outlined text-[#ba1a1a]" style={{ fontVariationSettings: "'FILL' 1" }}>
                warning
              </span>
              <h4 className="font-headline text-2xl text-[#93000a]">Anomalias y alertas de cumplimiento</h4>
            </div>
            <p className="text-sm text-[#93000a] leading-relaxed">
              Se observan variaciones relevantes en areas de mayor riesgo. Priorizar pruebas sustantivas en
              cuentas con mayor exposicion y revisar soportes de cierre para evitar desviaciones materiales.
            </p>
          </article>
        </div>

        <div className="xl:col-span-4 space-y-6">
          <article className="sovereign-card">
            <h4 className="font-headline text-2xl text-navy-900 mb-4">Ciclo de Vida de Auditoria</h4>
            <div className="space-y-4">
              {[
                { label: "Planificacion", done: progreso >= 30 },
                { label: "Ejecucion", done: progreso >= 60 },
                { label: "Informe", done: progreso >= 90 },
              ].map((step) => (
                <div key={step.label} className="flex items-center gap-3">
                  <span className={`material-symbols-outlined ${step.done ? "text-emerald-700" : "text-slate-400"}`}>
                    {step.done ? "check_circle" : "radio_button_unchecked"}
                  </span>
                  <span className={`text-sm ${step.done ? "text-navy-900 font-semibold" : "text-slate-500"}`}>{step.label}</span>
                </div>
              ))}
            </div>
            <div className="mt-5 pt-4 border-t border-black/5 text-xs uppercase tracking-[0.12em] text-slate-500">
              Etapa actual: <span className="font-bold text-navy-900">{etapa}</span>
            </div>
          </article>

          <article className="ai-memo">
            <div className="text-xs uppercase tracking-[0.2em] font-body font-bold opacity-90">Perspectiva del Auditor</div>
            <p className="font-headline italic text-lg mt-2 leading-relaxed text-white">
              Riesgo global <span className={riesgoTone}>{data.riesgo_global}</span> con avance de <b>{progreso.toFixed(1)}%</b>.
              Se recomienda cerrar areas criticas antes del informe final.
            </p>
          </article>
        </div>
      </section>
    </div>
  );
}

