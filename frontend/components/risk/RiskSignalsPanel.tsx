import type { RiskCriticalArea } from "../../types/risk";
import { summarizeRiskSignals } from "../../lib/riskSignals";

type Props = {
  areas: RiskCriticalArea[];
};

function sourceLabel(source: "industry" | "mayor" | "mixed" | "base"): string {
  if (source === "industry") return "Regla de industria";
  if (source === "mayor") return "Señal del mayor";
  if (source === "mixed") return "Mixto";
  return "Base";
}

function sourceTone(source: "industry" | "mayor" | "mixed" | "base"): string {
  if (source === "industry") return "bg-teal-50 text-teal-800 border-teal-200";
  if (source === "mayor") return "bg-blue-50 text-blue-800 border-blue-200";
  if (source === "mixed") return "bg-amber-50 text-amber-800 border-amber-200";
  return "bg-slate-100 text-slate-700 border-slate-200";
}

export default function RiskSignalsPanel({ areas }: Props) {
  const { withIndustry, withAnyBoost, totalIndustryBoost, totalMayorBoost } = summarizeRiskSignals(areas);
  const highlights = withAnyBoost.sort((a, b) => b.totalBoost - a.totalBoost).slice(0, 4);

  return (
    <section className="space-y-4">
      <div className="sovereign-card">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-[10px] uppercase tracking-[0.16em] text-slate-500 font-bold">Señales activas</p>
            <h2 className="font-headline text-3xl text-[#041627] mt-2">Qué está moviendo el riesgo</h2>
            <p className="text-sm text-slate-600 mt-2">
              Estas señales combinan reglas de industria con comportamiento contable del mayor para explicar por qué sube la prioridad de cada área.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 min-w-0 lg:min-w-[520px]">
            <article className="rounded-xl border border-[#041627]/10 bg-[#f8fbfb] px-4 py-3">
              <p className="text-[10px] uppercase tracking-[0.12em] text-slate-500 font-bold">Áreas con industria</p>
              <p className="font-headline text-2xl text-[#041627] mt-1">{withIndustry.length}</p>
            </article>
            <article className="rounded-xl border border-[#041627]/10 bg-[#f8fbfb] px-4 py-3">
              <p className="text-[10px] uppercase tracking-[0.12em] text-slate-500 font-bold">Boost industria</p>
              <p className="font-headline text-2xl text-[#041627] mt-1">+{totalIndustryBoost.toFixed(1)}</p>
            </article>
            <article className="rounded-xl border border-[#041627]/10 bg-[#f8fbfb] px-4 py-3">
              <p className="text-[10px] uppercase tracking-[0.12em] text-slate-500 font-bold">Boost mayor</p>
              <p className="font-headline text-2xl text-[#041627] mt-1">+{totalMayorBoost.toFixed(1)}</p>
            </article>
          </div>
        </div>
      </div>

      {highlights.length > 0 ? (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {highlights.map((item) => (
            <article key={item.areaId} className="rounded-xl border border-[#041627]/10 bg-white px-5 py-4 shadow-sm">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="font-semibold text-[#041627] text-lg">{item.areaName}</h3>
                  <p className="text-xs text-slate-500 mt-1">
                    Score {item.score.toFixed(2)} · {item.nivel}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2 justify-end">
                  <span className={`inline-flex rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.12em] ${sourceTone(item.source)}`}>
                    {sourceLabel(item.source)}
                  </span>
                  <span className="inline-flex rounded-full border border-[#041627]/10 bg-slate-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-[#041627]">
                    Boost +{item.totalBoost.toFixed(1)}
                  </span>
                </div>
              </div>

              {item.drivers.length > 0 ? (
                <ul className="mt-4 space-y-2">
                  {item.drivers.slice(0, 2).map((driver) => (
                    <li key={driver} className="flex items-start gap-2 text-sm text-slate-700">
                      <span className="material-symbols-outlined text-base text-[#0d9488]">flare</span>
                      <span>{driver}</span>
                    </li>
                  ))}
                </ul>
              ) : null}

              {item.topComponents.length > 0 ? (
                <div className="mt-4 flex flex-wrap gap-2">
                  {item.topComponents.map((component) => (
                    <span
                      key={component.key}
                      className="inline-flex rounded-lg border border-[#041627]/10 bg-[#f1f4f6] px-2.5 py-1 text-xs text-slate-700"
                    >
                      {component.label}: +{component.value.toFixed(1)}
                    </span>
                  ))}
                </div>
              ) : null}
            </article>
          ))}
        </div>
      ) : (
        <article className="rounded-xl border border-[#041627]/10 bg-white px-5 py-4 text-sm text-slate-600">
          Todavía no hay señales adicionales activas. El ranking actual se está sosteniendo principalmente en el modelo base.
        </article>
      )}
    </section>
  );
}
