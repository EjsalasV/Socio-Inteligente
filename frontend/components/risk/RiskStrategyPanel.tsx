import type { RiskCriticalArea, RiskStrategy } from "../../types/risk";

type Props = {
  areas: RiskCriticalArea[];
  strategy: RiskStrategy;
};

export default function RiskStrategyPanel({ areas, strategy }: Props) {
  const top = areas[0];

  return (
    <section className="col-span-12 lg:col-span-5 flex flex-col space-y-6">
      <div className="bg-[#1a2b3c] p-8 rounded-xl text-white relative overflow-hidden">
        <div className="relative z-10">
          <span className="text-[#a5eff0] text-[10px] font-bold tracking-widest uppercase">Estrategia Recomendada</span>
          <h3 className="font-headline text-3xl mt-2 mb-6">
            Enfoque de Auditoria: <span className="text-[#89d3d4] italic">{strategy.approach}</span>
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
                ? `La mayor exposicion actual esta en ${top.area_nombre} (score ${top.score.toFixed(2)}), por lo que conviene reforzar pruebas de corte y consistencia de soporte.`
                : "No hay hallazgos criticos activos. Se recomienda monitoreo preventivo y revision analitica."}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
