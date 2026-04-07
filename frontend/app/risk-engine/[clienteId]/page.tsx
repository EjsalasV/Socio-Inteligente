"use client";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import CriticalRisks from "../../../components/risk/CriticalRisks";
import RiskMatrix from "../../../components/risk/RiskMatrix";
import RiskProcedureSuggestions from "../../../components/risk/RiskProcedureSuggestions";
import RiskStrategyPanel from "../../../components/risk/RiskStrategyPanel";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import { useRiskEngine } from "../../../lib/hooks/useRiskEngine";

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
          Motor de Riesgos - Mapa de Calor de Auditoría
        </h1>
      </header>

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
