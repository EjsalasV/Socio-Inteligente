import { useState } from "react";

import { createWorkpaperTask } from "../../lib/api/workpapers";
import type { RiskCriticalArea, RiskStrategy } from "../../types/risk";

type Props = {
  clienteId: string;
  areas: RiskCriticalArea[];
  strategy: RiskStrategy;
};

function tonePriority(priority: string): string {
  const p = priority.toLowerCase();
  if (p === "alta") return "bg-red-100 text-red-700 border-red-200";
  if (p === "media") return "bg-amber-100 text-amber-700 border-amber-200";
  return "bg-slate-100 text-slate-600 border-slate-200";
}

export default function RiskStrategyPanel({ clienteId, areas, strategy }: Props) {
  const top = areas[0];
  const [savingKey, setSavingKey] = useState<string>("");
  const [feedback, setFeedback] = useState<string>("");

  async function addToWorkpapers(test: RiskStrategy["control_tests"][number]): Promise<void> {
    setSavingKey(test.test_id);
    setFeedback("");
    try {
      const result = await createWorkpaperTask(clienteId, {
        area_code: test.area_id,
        area_name: test.area_nombre,
        title: test.title,
        nia_ref: test.nia_ref,
        prioridad: test.priority,
        required: true,
        evidence_note: test.description,
      });
      setFeedback(result.created ? "Prueba agregada a Papeles de Trabajo." : "La prueba ya estaba creada.");
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : "No se pudo crear la tarea.");
    } finally {
      setSavingKey("");
    }
  }

  return (
    <section className="col-span-12 lg:col-span-5 flex flex-col space-y-8">
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

      <div className="bg-white border border-slate-200 rounded-xl p-5">
        <h4 className="text-sm font-bold text-[#041627] uppercase tracking-[0.1em]">Pruebas sugeridas (Control)</h4>
        <div className="mt-4 space-y-3">
          {strategy.control_tests.slice(0, 3).map((test) => (
            <article key={test.test_id} className="rounded-lg border border-slate-200 p-3">
              <div className="flex justify-between items-start gap-3">
                <div>
                  <p className="text-sm font-semibold text-slate-900">{test.title}</p>
                  <p className="text-xs text-slate-500 mt-1">
                    {test.area_nombre} · {test.nia_ref}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => void addToWorkpapers(test)}
                  disabled={savingKey === test.test_id}
                  className="text-xs px-2 py-1 rounded border border-slate-300 text-slate-700 disabled:opacity-60"
                >
                  +
                </button>
              </div>
              <p className="text-xs text-slate-600 mt-2">{test.description}</p>
              <span className={`inline-flex mt-2 px-2 py-0.5 text-[10px] rounded border ${tonePriority(test.priority)}`}>
                {test.priority}
              </span>
            </article>
          ))}
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-5">
        <h4 className="text-sm font-bold text-[#041627] uppercase tracking-[0.1em]">Pruebas sugeridas (Sustantivas)</h4>
        <div className="mt-4 space-y-3">
          {strategy.substantive_tests.slice(0, 3).map((test) => (
            <article key={test.test_id} className="rounded-lg border border-slate-200 p-3">
              <div className="flex justify-between items-start gap-3">
                <div>
                  <p className="text-sm font-semibold text-slate-900">{test.title}</p>
                  <p className="text-xs text-slate-500 mt-1">
                    {test.area_nombre} · {test.nia_ref}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => void addToWorkpapers(test)}
                  disabled={savingKey === test.test_id}
                  className="text-xs px-2 py-1 rounded border border-slate-300 text-slate-700 disabled:opacity-60"
                >
                  +
                </button>
              </div>
              <p className="text-xs text-slate-600 mt-2">{test.description}</p>
              <span className={`inline-flex mt-2 px-2 py-0.5 text-[10px] rounded border ${tonePriority(test.priority)}`}>
                {test.priority}
              </span>
            </article>
          ))}
        </div>
        {feedback ? <p className="mt-3 text-xs text-slate-600">{feedback}</p> : null}
      </div>
    </section>
  );
}
