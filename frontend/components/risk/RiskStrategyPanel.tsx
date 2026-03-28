import type { RiskCriticalArea } from "../../types/risk";

type Props = {
  areas: RiskCriticalArea[];
};

function calculateMix(areas: RiskCriticalArea[]): { control: number; substantive: number; insight: string } {
  if (areas.length === 0) {
    return {
      control: 50,
      substantive: 50,
      insight: "Sin datos suficientes. Se sugiere iniciar con una evaluación mixta de controles y sustantivos.",
    };
  }

  const average = areas.reduce((acc, area) => acc + area.score, 0) / areas.length;
  if (average >= 75) {
    return {
      control: 35,
      substantive: 65,
      insight:
        "El perfil de riesgo es elevado. Conviene priorizar procedimientos sustantivos y confirmaciones externas en las áreas más expuestas.",
    };
  }
  if (average >= 55) {
    return {
      control: 40,
      substantive: 60,
      insight:
        "El riesgo se concentra en rubros específicos. Recomendable mantener enfoque mixto con mayor peso en pruebas sustantivas.",
    };
  }
  return {
    control: 55,
    substantive: 45,
    insight: "El riesgo es moderado-bajo. Se puede sostener el trabajo en controles con pruebas sustantivas selectivas.",
  };
}

export default function RiskStrategyPanel({ areas }: Props) {
  const top = areas[0];
  const mix = calculateMix(areas);

  return (
    <section className="col-span-12 lg:col-span-5 flex flex-col space-y-8">
      <div className="bg-[#1a2b3c] p-8 rounded-xl text-white relative overflow-hidden">
        <div className="relative z-10">
          <span className="text-[#a5eff0] text-[10px] font-bold tracking-widest uppercase">Estrategia Recomendada</span>
          <h3 className="font-headline text-3xl mt-2 mb-6">
            Enfoque de Auditoría: <span className="text-[#89d3d4] italic">Mixto</span>
          </h3>

          <div className="space-y-4">
            <div className="flex justify-between items-center border-b border-white/10 pb-2">
              <span className="text-sm text-slate-300">Pruebas de Control</span>
              <span className="font-bold text-[#89d3d4]">{mix.control}%</span>
            </div>
            <div className="flex justify-between items-center border-b border-white/10 pb-2">
              <span className="text-sm text-slate-300">Procedimientos Sustantivos</span>
              <span className="font-bold text-[#89d3d4]">{mix.substantive}%</span>
            </div>
          </div>

          <p className="mt-6 text-sm text-slate-300 leading-relaxed">{mix.insight}</p>
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
    </section>
  );
}
