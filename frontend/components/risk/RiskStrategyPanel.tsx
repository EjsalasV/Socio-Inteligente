import type { RiskCriticalArea, RiskStrategy } from "../../types/risk";
import { summarizeRiskSignals } from "../../lib/riskSignals";

type Props = {
  areas: RiskCriticalArea[];
  strategy: RiskStrategy;
};

export default function RiskStrategyPanel({ areas, strategy }: Props) {
  const top = areas[0];
  const signalSummary = summarizeRiskSignals(areas);
  const topSignal = signalSummary.withAnyBoost.sort((a, b) => b.totalBoost - a.totalBoost)[0];

  return (
    <section className="col-span-12 lg:col-span-5 flex flex-col space-y-6">
      <div className="bg-[#1a2b3c] p-8 rounded-xl text-white relative overflow-hidden">
        <div className="relative z-10">
          <span className="text-[#a5eff0] text-[10px] font-bold tracking-widest uppercase">Estrategia Recomendada</span>
          <h3 className="font-headline text-3xl mt-2 mb-6">
            Enfoque de Auditoría: <span className="text-[#89d3d4] italic">{strategy.approach}</span>
          </h3>

          <div className="space-y-4">
            <div className="flex justify-between items-center border-b border-white/10 pb-2">
              <span className="text-sm text-slate-300">Pruebas de Control</span>
              <span className="font-bold text-[#89d3d4]">{strategy.control_pct}%</span>
            </div>
            <div className="flex justify-between items-center border-b border-white/10 pb-2">
              <span className="text-sm text-slate-300">Procedimientos Sustantivos</span>
              <span className="font-bold text-[#89d3d4]">{strategy.substantive_pct}%</span>
            </div>
          </div>

          <p className="mt-6 text-sm text-slate-300 leading-relaxed">{strategy.rationale}</p>
        </div>
        <div className="absolute -right-10 -bottom-10 opacity-10">
          <span className="material-symbols-outlined text-[200px]" style={{ fontVariationSettings: "'FILL' 1" }}>
            security
          </span>
        </div>
      </div>

      <div className="bg-[#002f30] p-6 rounded-xl border border-[#89d3d4]/20">
        <div className="flex items-start space-x-4">
          <span className="material-symbols-outlined text-[#a5eff0] text-3xl">psychology</span>
          <div>
            <h4 className="text-[#a5eff0] font-semibold text-lg">AI Insight</h4>
            <p className="text-[#89d3d4]/80 text-sm mt-1">
              {top
                ? `La mayor exposición actual está en ${top.area_nombre} (score ${top.score.toFixed(2)}), por lo que conviene reforzar pruebas de corte y consistencia de soporte.`
                : "No hay hallazgos críticos activos. Se recomienda monitoreo preventivo y revisión analítica."}
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-xl border border-[#041627]/10 shadow-sm">
        <div className="flex items-start gap-3">
          <span className="material-symbols-outlined text-[#0d9488] text-3xl">insights</span>
          <div className="min-w-0">
            <h4 className="text-[#041627] font-semibold text-lg">Señales determinísticas activas</h4>
            <p className="text-slate-600 text-sm mt-1">
              {signalSummary.withIndustry.length > 0
                ? `${signalSummary.withIndustry.length} área(s) recibieron ajuste por industria y ${signalSummary.withMayor.length} por comportamiento del mayor.`
                : "Aún no hay reglas de industria activas impactando el score."}
            </p>
            {topSignal ? (
              <div className="mt-4 rounded-lg bg-[#f1f4f6] border border-slate-200 px-4 py-3">
                <p className="text-[10px] uppercase tracking-[0.12em] text-slate-500 font-bold">Señal dominante</p>
                <p className="text-sm text-[#041627] mt-1 font-semibold">{topSignal.areaName}</p>
                <p className="text-sm text-slate-600 mt-1">
                  Boost total de +{topSignal.totalBoost.toFixed(1)}
                  {topSignal.industryBoost > 0 ? ` · industria +${topSignal.industryBoost.toFixed(1)}` : ""}
                  {topSignal.mayorBoost > 0 ? ` · mayor +${topSignal.mayorBoost.toFixed(1)}` : ""}
                </p>
                {topSignal.drivers[0] ? <p className="text-sm text-slate-700 mt-2">{topSignal.drivers[0]}</p> : null}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </section>
  );
}
