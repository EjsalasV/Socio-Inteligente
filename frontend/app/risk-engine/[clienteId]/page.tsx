"use client";

import dynamic from "next/dynamic";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import ContextualHelp from "../../../components/help/ContextualHelp";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import { useRiskEngine } from "../../../lib/hooks/useRiskEngine";

const CriticalRisks = dynamic(() => import("../../../components/risk/CriticalRisks"), {
  loading: () => <DashboardSkeleton />,
});
const RiskMatrix = dynamic(() => import("../../../components/risk/RiskMatrix"), {
  loading: () => <DashboardSkeleton />,
});
const RiskProcedureSuggestions = dynamic(() => import("../../../components/risk/RiskProcedureSuggestions"), {
  loading: () => <DashboardSkeleton />,
});
const RiskStrategyPanel = dynamic(() => import("../../../components/risk/RiskStrategyPanel"), {
  loading: () => <DashboardSkeleton />,
});

export default function RiskEnginePage() {
  const { clienteId } = useAuditContext();
  const { data, isLoading, error } = useRiskEngine(clienteId);

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

      <div className="grid grid-cols-12 gap-8">
        <div data-tour="risk-matrix" className="col-span-12 lg:col-span-7">
          <RiskMatrix data={data} />
        </div>
        <RiskStrategyPanel areas={data.areas_criticas} strategy={data.strategy} />
        <div data-tour="risk-critical" className="col-span-12 lg:col-span-5">
          <CriticalRisks areas={data.areas_criticas} />
        </div>
        <div data-tour="risk-suggestions" className="col-span-12 lg:col-span-7">
          <RiskProcedureSuggestions
            clienteId={clienteId}
            areas={data.areas_criticas}
            controlTests={data.strategy.control_tests}
            substantiveTests={data.strategy.substantive_tests}
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
