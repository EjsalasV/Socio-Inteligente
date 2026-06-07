import type { RiskCriticalArea } from "../../types/risk";
import { getLsShortName } from "../../lib/lsCatalog";
import { getRiskSignalSummary } from "../../lib/riskSignals";

type Props = {
  areas: RiskCriticalArea[];
  id?: string;
};

function levelChip(level: string): { chipClass: string; borderClass: string; scoreClass: string } {
  const normalized = level.toUpperCase();
  if (normalized === "ALTO") {
    return {
      chipClass: "bg-[#ba1a1a] text-white",
      borderClass: "border-l-[#ba1a1a]",
      scoreClass: "text-[#ba1a1a]",
    };
  }
  if (normalized === "MEDIO") {
    return {
      chipClass: "bg-orange-500 text-white",
      borderClass: "border-l-orange-500",
      scoreClass: "text-orange-500",
    };
  }
  return {
    chipClass: "bg-slate-400 text-white",
    borderClass: "border-l-slate-400",
    scoreClass: "text-slate-500",
  };
}

export default function CriticalRisks({ areas, id = "riesgos-criticos" }: Props) {
  const list = areas.slice(0, 8);

  return (
    <section id={id} className="col-span-12 lg:col-span-5 space-y-4 scroll-mt-28">
      <h2 className="font-headline text-2xl text-[#041627] font-semibold mb-6 px-2">Riesgos Detectados por Area</h2>

      {list.map((item) => {
        const ui = levelChip(item.nivel);
        const signal = getRiskSignalSummary(item);
        return (
          <article key={item.area_id} className={`bg-[#f1f4f6] p-6 rounded-xl border-l-4 ${ui.borderClass}`}>
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <h4 className="font-bold text-[#041627]">{item.area_nombre}</h4>
                <div className="flex flex-wrap items-center gap-2 mt-1">
                  <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${ui.chipClass}`}>{item.nivel}</span>
                  <span className="text-[10px] text-slate-500 font-medium uppercase tracking-tight">{getLsShortName(item.area_id)}</span>
                  {signal.industryBoost > 0 ? (
                    <span className="text-[10px] px-2 py-0.5 rounded font-bold border border-teal-200 bg-teal-50 text-teal-800">
                      Industria +{signal.industryBoost.toFixed(1)}
                    </span>
                  ) : null}
                  {signal.mayorBoost > 0 ? (
                    <span className="text-[10px] px-2 py-0.5 rounded font-bold border border-blue-200 bg-blue-50 text-blue-800">
                      Mayor +{signal.mayorBoost.toFixed(1)}
                    </span>
                  ) : null}
                </div>
              </div>
              <div className="text-right shrink-0">
                <div className={`text-2xl font-black ${ui.scoreClass}`}>{item.score.toFixed(2)}</div>
                <div className="text-[10px] font-bold text-slate-400 uppercase">Score</div>
              </div>
            </div>

            {signal.drivers.length > 0 ? (
              <div className="mt-4 space-y-2">
                {signal.drivers.slice(0, 2).map((driver) => (
                  <p key={driver} className="text-sm text-slate-700 flex items-start gap-2">
                    <span className="material-symbols-outlined text-base text-[#0d9488]">subdirectory_arrow_right</span>
                    <span>{driver}</span>
                  </p>
                ))}
              </div>
            ) : null}

            {signal.topComponents.length > 0 ? (
              <div className="mt-4 flex flex-wrap gap-2">
                {signal.topComponents.slice(0, 2).map((component) => (
                  <span key={component.key} className="text-[11px] rounded-lg bg-white/80 border border-slate-200 px-2.5 py-1 text-slate-700">
                    {component.label}: +{component.value.toFixed(1)}
                  </span>
                ))}
              </div>
            ) : null}
          </article>
        );
      })}

      {list.length === 0 ? (
        <article className="bg-[#f1f4f6] p-6 rounded-xl border border-slate-200 text-sm text-slate-500">
          No hay riesgos criticos registrados para este cliente.
        </article>
      ) : null}
    </section>
  );
}
