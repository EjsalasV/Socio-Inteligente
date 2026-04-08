import DashboardGrid from "./DashboardGrid";
import ContextualHelp from "../help/ContextualHelp";
import type { DashboardData } from "../../types/dashboard";

type Props = {
  data: DashboardData;
};

export default function DashboardContent({ data }: Props) {
  const progreso = Math.max(0, Math.min(100, data.progreso_auditoria));
  const orderedAreas = [...(data.top_areas ?? [])]
    .filter((area) => area.con_saldo)
    .sort((a, b) => b.score_riesgo - a.score_riesgo);

  const riskPct = (score: number): number => {
    if (score <= 1) return Math.max(0, Math.min(100, score * 100));
    return Math.max(0, Math.min(100, score));
  };

  const riesgoTone =
    data.riesgo_global.toUpperCase() === "ALTO"
      ? "text-[#ba1a1a]"
      : data.riesgo_global.toUpperCase() === "MEDIO"
        ? "text-amber-700"
        : "text-emerald-700";

  const fase = (data.workflow_phase || data.fase_actual || "").toLowerCase();
  const etapa =
    fase.includes("inform") || fase.includes("cierre")
      ? "Informe"
      : fase.includes("ejec") || fase.includes("visita")
        ? "Ejecucion"
        : fase.includes("plan")
          ? "Planificacion"
          : "Sin definir";
  const tbStage = (data.tb_stage || "sin_saldos").toLowerCase();
  const tbStageLabel =
    tbStage === "final"
      ? "Corte Final"
      : tbStage === "preliminar"
        ? "Corte Preliminar"
        : tbStage === "inicial"
          ? "Corte Inicial"
          : "Sin saldos";

  return (
    <div className="space-y-8 pb-8">
      <section className="rounded-editorial p-7 shadow-editorial text-white border border-[#041627]/20 bg-gradient-to-br from-[#041627] to-[#1a2b3c]">
        <p className="text-xs uppercase tracking-[0.2em] text-[#a5eff0] font-body">Centro de Mando de Auditoria - Socio AI</p>
        <h2 data-tour="dashboard-title" className="font-headline text-5xl text-white mt-2">Dashboard Ejecutivo</h2>
        <p className="font-body text-slate-200 mt-3 leading-relaxed text-base">
          Cliente: <span className="font-semibold text-white">{data.nombre_cliente}</span> ·
          Periodo: <span className="font-semibold text-white"> {data.periodo || "Actual"}</span> ·
          Sector: <span className="font-semibold text-white"> {data.sector || "N/D"}</span> ·
          TB: <span className="font-semibold text-white"> {tbStageLabel}</span>
        </p>
      </section>

      <ContextualHelp
        title="Ayuda del modulo Dashboard"
        items={[
          {
            label: "KPIs",
            description:
              "Muestran estado general del cliente: riesgo global, materialidad, avance y consistencia de balance.",
          },
          {
            label: "Ranking de riesgos",
            description:
              "Te indica en que areas conviene empezar primero. Las de mayor score deben priorizarse en ejecucion.",
          },
          {
            label: "Ciclo de vida",
            description:
              "Resume fase actual (planificacion, ejecucion o informe) y te ayuda a no saltar pasos criticos.",
          },
        ]}
      />

      <div data-tour="dashboard-kpis">
        <DashboardGrid data={data} />
      </div>

      <section className="grid grid-cols-1 xl:grid-cols-12 gap-8">
        <div className="xl:col-span-8 space-y-6">
          <article data-tour="dashboard-risk-ranking" className="sovereign-card">
            <div className="flex items-center justify-between gap-3 mb-5">
              <h3 className="font-headline text-3xl text-navy-900">Ranking de Riesgos por Area</h3>
              <span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Top Areas</span>
            </div>

            <div className="space-y-4">
              {orderedAreas.slice(0, 5).map((area) => {
                const pct = Math.max(8, riskPct(area.score_riesgo));
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
                      <span className="text-slate-500 font-medium">{riskPct(area.score_riesgo).toFixed(1)}%</span>
                    </div>
                    <div className="h-2 rounded-full bg-[#ebeef0] overflow-hidden">
                      <div className={`h-full ${bar}`} style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
              {orderedAreas.length === 0 ? (
                <p className="text-sm text-slate-500">Aun no hay areas con saldo relevante para ranking.</p>
              ) : null}
            </div>
          </article>

          <article className="risk-high">
            <div className="flex items-center gap-2 mb-2">
              <span
                className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[#ba1a1a] text-white text-xs font-bold"
                aria-hidden="true"
              >
                !
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
                { label: "Planificacion", done: etapa === "Planificacion" || etapa === "Ejecucion" || etapa === "Informe" },
                { label: "Ejecucion", done: etapa === "Ejecucion" || etapa === "Informe" },
                { label: "Informe", done: etapa === "Informe" },
              ].map((step) => (
                <div key={step.label} className="flex items-center gap-3">
                  <span
                    className={`inline-flex h-5 w-5 items-center justify-center rounded-full border text-xs ${
                      step.done ? "border-emerald-700 bg-emerald-700 text-white" : "border-slate-300 text-slate-400"
                    }`}
                    aria-hidden="true"
                  >
                    {step.done ? "✓" : ""}
                  </span>
                  <span className={`text-sm ${step.done ? "text-navy-900 font-semibold" : "text-slate-500"}`}>{step.label}</span>
                </div>
              ))}
            </div>
            {data.workflow_gates?.length ? (
              <div className="mt-5 pt-4 border-t border-black/5 space-y-2">
                <p className="text-[11px] uppercase tracking-[0.12em] text-slate-500 font-semibold">Quality Gates</p>
                <div className="space-y-2">
                  {data.workflow_gates.map((gate) => (
                    <div key={gate.code} className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-navy-900">{gate.code}</span>
                      <span
                        className={
                          gate.status === "ok"
                            ? "rounded-full px-2 py-0.5 bg-emerald-100 text-emerald-800 font-semibold"
                            : "rounded-full px-2 py-0.5 bg-rose-100 text-rose-800 font-semibold"
                        }
                      >
                        {gate.status === "ok" ? "OK" : "BLOQUEADO"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
            <div
              className={`${
                data.workflow_gates?.length ? "mt-4 pt-1" : "mt-5 pt-4 border-t border-black/5"
              } text-xs uppercase tracking-[0.12em] text-slate-500`}
            >
              Etapa actual: <span className="font-bold text-navy-900">{etapa}</span>
            </div>
          </article>

          <article className="ai-memo">
            <div className="text-xs uppercase tracking-[0.2em] font-body font-bold opacity-90">Perspectiva del Auditor</div>
            <p className="font-headline italic text-lg mt-2 leading-relaxed text-white">
              Riesgo global <span className={riesgoTone}>{data.riesgo_global}</span> con avance de <b>{progreso.toFixed(1)}%</b>.
              Se recomienda cerrar areas criticas antes del informe final.
            </p>
            <p className="text-xs text-slate-200 mt-3">
              NIA 320 · Base: <b>{data.materialidad_detalle.base_usada || "N/D"}</b> ·
              % aplicado: <b>{data.materialidad_detalle.porcentaje_aplicado.toFixed(2)}%</b>
            </p>
          </article>
        </div>
      </section>
    </div>
  );
}


