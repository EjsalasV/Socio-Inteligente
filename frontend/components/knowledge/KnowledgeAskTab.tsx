"use client";

import type { KnowledgeAskResponse } from "../../types/knowledge";

type Props = {
  query: string;
  onQueryChange: (value: string) => void;
  onAsk: () => void;
  isLoading?: boolean;
  response: KnowledgeAskResponse | null;
};

export default function KnowledgeAskTab({
  query,
  onQueryChange,
  onAsk,
  isLoading = false,
  response,
}: Props) {
  return (
    <section className="sovereign-card p-5 space-y-4">
      <h2 className="font-headline text-2xl text-[#041627]">Ask</h2>
      <div className="space-y-2">
        <label className="text-xs uppercase tracking-[0.12em] text-slate-500 font-bold" htmlFor="knowledge-ask-input">
          Pregunta
        </label>
        <textarea
          id="knowledge-ask-input"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          className="w-full min-h-[120px] rounded-editorial border border-[#041627]/15 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#14b8a6]"
          placeholder="Pregunta sobre hallazgos, riesgos o evidencia..."
        />
        <button
          type="button"
          className="rounded-editorial px-4 py-2 text-xs uppercase tracking-[0.12em] font-bold text-white bg-[#0d9488] hover:bg-[#0b7e72] min-h-[44px] disabled:opacity-50"
          onClick={onAsk}
          disabled={isLoading || !query.trim()}
        >
          {isLoading ? "Consultando..." : "Consultar"}
        </button>
      </div>

      {response ? (
        <div className="space-y-3">
          <div className="border border-[#041627]/10 rounded-editorial p-3">
            <p className="text-sm font-semibold text-[#041627]">Respuesta</p>
            <p className="text-sm text-slate-700 mt-1">{response.answer}</p>
          </div>
          <div className="border border-[#041627]/10 rounded-editorial p-3">
            <p className="text-sm font-semibold text-[#041627]">Fuentes</p>
            <ul className="mt-2 space-y-2">
              {response.sources.map((source, idx) => (
                <li key={`${source.entity_id}-${idx}`} className="text-xs text-slate-600">
                  <span className="font-semibold">{source.title || source.entity_type || "Fuente"}</span> ·{" "}
                  {source.source_module} · score {source.score.toFixed(2)}
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
    </section>
  );
}

