import type { RiskCriticalArea } from "../../types/risk";
import { getLsShortName } from "../../lib/lsCatalog";

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
  const list = areas.slice(0, 3);

  return (
    <section id={id} className="col-span-12 lg:col-span-5 space-y-4 scroll-mt-28">
      <h2 className="font-headline text-2xl text-[#041627] font-semibold mb-6 px-2">Riesgos Criticos Detectados</h2>

      {list.map((item) => {
        const ui = levelChip(item.nivel);
        return (
          <article
            key={item.area_id}
            className={`bg-[#f1f4f6] p-6 rounded-xl border-l-4 flex justify-between items-center ${ui.borderClass}`}
          >
            <div>
              <h4 className="font-bold text-[#041627]">{item.area_nombre}</h4>
              <div className="flex items-center space-x-2 mt-1">
                <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${ui.chipClass}`}>{item.nivel}</span>
                <span className="text-[10px] text-slate-500 font-medium uppercase tracking-tight">{getLsShortName(item.area_id)}</span>
              </div>
            </div>
            <div className="text-right">
              <div className={`text-2xl font-black ${ui.scoreClass}`}>{item.score.toFixed(2)}</div>
              <div className="text-[10px] font-bold text-slate-400 uppercase">Score</div>
            </div>
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
