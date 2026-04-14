"use client";

import dynamic from "next/dynamic";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import ContextualHelp from "../../../components/help/ContextualHelp";
import RiskProcedureSuggestions from "../../../components/risk/RiskProcedureSuggestions";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import { useLearningRole } from "../../../lib/hooks/useLearningRole";
import { useRiskEngine } from "../../../lib/hooks/useRiskEngine";

const CriticalRisks = dynamic(() => import("../../../components/risk/CriticalRisks"), {
  loading: () => <DashboardSkeleton />,
});
const RiskMatrix = dynamic(() => import("../../../components/risk/RiskMatrix"), {
  loading: () => <DashboardSkeleton />,
});
const RiskStrategyPanel = dynamic(() => import("../../../components/risk/RiskStrategyPanel"), {
  loading: () => <DashboardSkeleton />,
});

export default function RiskEnginePage() {
  const { clienteId } = useAuditContext();
  const { data, isLoading, error } = useRiskEngine(clienteId);
  const { role } = useLearningRole();
  const strategy = data?.strategy ?? {
    approach: "mixto",
    control_pct: 50,
    substantive_pct: 50,
    rationale: "",
    control_tests: [],
    substantive_tests: [],
  };
  const criticalAreas = data?.areas_criticas ?? [];

  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorMessage message={error} />;
  if (!data) return <ErrorMessage message="No hay datos del motor de riesgos para este cliente." />;

  return (
    <div className="pt-4 pb-8 space-y-8 max-w-screen-2xl">
      <header className="mb-4">
        <span className="text-[#001919] font-label text-xs tracking-[0.2em] uppercase font-bold mb-2 block">
          Risk Intelligence Dashboard
        </span>
        <h1 data-tour="risk-title" className="font-headline text-4xl font-bold text-[#041627] tracking-tight">
          Motor de Riesgos - Mapa de Calor de Auditoria
        </h1>
      </header>

      <ContextualHelp
        title="Ayuda del modulo Risk Engine"
        items={[
          {
            label: "Matriz de calor",
            byRole: {
              junior:
                "Empieza por los cuadrantes altos: esas areas tienen mayor probabilidad de error material.",
              semi:
                "Cruza impacto y frecuencia para ubicar las areas de mayor exposicion.",
              senior:
                "Usa la matriz para validar alcance y reasignar recursos a riesgos altos.",
              socio:
                "Usa la matriz para confirmar foco de auditoria, riesgo de emision y necesidad de escalamiento.",
            },
          },
          {
            label: "Areas criticas",
            byRole: {
              junior:
                "Toma la primera area del ranking y pasa a Workspace Areas para ejecutar pruebas.",
              semi:
                "Lista priorizada para decidir donde ejecutar pruebas primero.",
              senior:
                "Valida consistencia del ranking contra conocimiento del negocio y riesgos emergentes.",
              socio:
                "Confirma que las areas criticas soporten la estrategia global y la opinion esperada.",
            },
          },
          {
            label: "Sugerencias de procedimientos",
            byRole: {
              junior:
                "Usa el boton + para convertir sugerencias en tareas concretas en Papeles de Trabajo.",
              semi:
                "Puedes agregar pruebas propuestas directamente a Papeles de Trabajo.",
              senior:
                "Revisa pertinencia y cobertura antes de aprobar la carga masiva de procedimientos.",
              socio:
                "Define solo pruebas de mayor retorno de aseguramiento y evita sobre-auditar areas no materiales.",
            },
          },
        ]}
      />

      {/* Panel de rol */}
      {role === "junior" && (
        <section className="bg-[#a5eff0]/10 border border-[#a5eff0]/30 rounded-xl p-6 space-y-4">
          <div className="flex items-start gap-4">
            <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#041627] text-[#a5eff0] text-xs font-bold mt-0.5">NIA</span>
            <div>
              <p className="text-xs uppercase tracking-[0.15em] text-[#041627]/60 font-bold mb-1">Cómo usar el Risk Engine — Vista Junior</p>
              <p className="text-sm text-[#041627] leading-relaxed">
                El Risk Engine te dice <strong>dónde trabajar primero</strong>. Las áreas con mayor score tienen mayor probabilidad de contener errores materiales. No empieces por orden alfabético — empieza por la primera del ranking.
              </p>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {[
              {
                num: 1,
                accion: criticalAreas[0] ? `Ve al Workspace de ${criticalAreas[0].area_nombre}` : "Ve al área de mayor riesgo",
                nia: "NIA 315",
                detalle: "El área con mayor score es tu punto de partida. Abre el Workspace para ver las cuentas y generar el briefing de procedimientos.",
              },
              {
                num: 2,
                accion: `Estrategia recomendada: ${strategy.approach}`,
                nia: "NIA 330",
                detalle: `${strategy.substantive_pct}% pruebas sustantivas · ${strategy.control_pct}% pruebas de controles. ${strategy.substantive_pct > 50 ? "Enfócate en pruebas directas de saldos y transacciones." : "Confía más en controles internos probados."}`,
              },
              {
                num: 3,
                accion: "Convierte sugerencias en papeles de trabajo",
                nia: "NIA 500",
                detalle: "Usa el botón + en las Sugerencias de Procedimientos para crear tareas en Papeles de Trabajo y ejecutarlas con evidencia documentada.",
              },
            ].map((step) => (
              <div key={step.nia} className="flex gap-3 p-4 bg-white rounded-lg border border-slate-100">
                <span className="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#041627] text-white text-xs font-bold mt-0.5">{step.num}</span>
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <p className="font-semibold text-[#041627] text-sm">{step.accion}</p>
                    <span className="shrink-0 px-2 py-0.5 rounded-full bg-[#041627]/10 text-[#041627] text-[10px] font-bold uppercase">{step.nia}</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1 leading-relaxed">{step.detalle}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {role === "socio" && criticalAreas.length > 0 && (
        <section className="rounded-xl p-6 bg-[#001919] border border-[#a5eff0]/20 shadow-md text-white">
          <p className="text-[10px] uppercase tracking-[0.2em] text-[#a5eff0] font-bold mb-3">Resumen Ejecutivo — Vista Socio</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="bg-white/10 rounded-lg p-4">
              <p className="text-[10px] uppercase tracking-[0.12em] text-slate-300">Enfoque aprobado</p>
              <p className="font-headline text-xl mt-1 font-semibold text-white">{strategy.approach}</p>
              <p className="text-xs text-slate-400 mt-1">{strategy.control_pct}% control · {strategy.substantive_pct}% sustantiva</p>
            </div>
            {criticalAreas.slice(0, 2).map((area) => (
              <div key={area.area_id} className={`rounded-lg p-4 ${area.nivel === "ALTO" || area.nivel === "CRITICO" ? "bg-rose-900/40 border border-rose-700/40" : "bg-amber-900/30 border border-amber-700/30"}`}>
                <p className="text-[10px] uppercase tracking-[0.12em] text-slate-300">Área crítica</p>
                <p className="font-semibold text-sm text-white mt-1">{area.area_nombre}</p>
                <p className="text-xs text-slate-400 mt-1">Score: {area.score.toFixed(1)} · {area.nivel}</p>
                {area.hallazgos_abiertos > 0 && <p className="text-xs text-amber-300 mt-1">{area.hallazgos_abiertos} hallazgo(s) abierto(s)</p>}
              </div>
            ))}
          </div>
          {strategy.rationale && (
            <p className="text-xs text-slate-300 border-t border-white/10 pt-3">{strategy.rationale}</p>
          )}
        </section>
      )}

      <div className="grid grid-cols-12 gap-8">
        <div data-tour="risk-matrix" className="col-span-12 lg:col-span-7">
          <RiskMatrix data={data} />
        </div>
        <RiskStrategyPanel areas={criticalAreas} strategy={strategy} />
        <div data-tour="risk-critical" className="col-span-12 lg:col-span-5">
          <CriticalRisks areas={criticalAreas} />
        </div>
        <div data-tour="risk-suggestions" className="col-span-12 lg:col-span-7">
          <RiskProcedureSuggestions
            clienteId={clienteId}
            areas={criticalAreas}
            controlTests={strategy.control_tests ?? []}
            substantiveTests={strategy.substantive_tests ?? []}
          />
        </div>
      </div>

      <footer className="mt-8 border-t border-slate-200 pt-8 flex justify-between items-center text-[10px] font-bold text-slate-400 tracking-widest uppercase">
        <div>Socio AI Risk Engine v2.4.0</div>
        <div className="flex space-x-8">
          <a className="hover:text-[#041627] transition-colors" href={`/metodologia/${clienteId}`}>Documentation</a>
          <a className="hover:text-[#041627] transition-colors" href={`/socio-chat/${clienteId}`}>Methodology</a>
          <a className="hover:text-[#041627] transition-colors" href={`/reportes/${clienteId}`}>Audit Standards</a>
        </div>
      </footer>
    </div>
  );
}
