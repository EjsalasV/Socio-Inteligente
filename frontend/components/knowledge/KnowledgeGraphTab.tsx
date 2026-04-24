"use client";

import type { KnowledgeGraphResponse } from "../../types/knowledge";

type Props = {
  graph: KnowledgeGraphResponse | null;
  isLoading?: boolean;
};

export default function KnowledgeGraphTab({ graph, isLoading = false }: Props) {
  return (
    <section className="sovereign-card p-5 space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h2 className="font-headline text-2xl text-[#041627]">Grafo</h2>
        <p className="text-xs text-slate-500">
          Nodos: {graph?.meta.total_nodes ?? 0} · Relaciones: {graph?.meta.total_edges ?? 0}
        </p>
      </div>

      {isLoading ? (
        <p className="text-sm text-slate-500">Cargando grafo...</p>
      ) : !graph ? (
        <p className="text-sm text-slate-500">Sin datos de grafo.</p>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="border border-[#041627]/10 rounded-editorial p-3">
            <h3 className="text-sm font-semibold text-[#041627] mb-2">Nodos</h3>
            <div className="space-y-2 max-h-[320px] overflow-y-auto">
              {graph.nodes.map((node) => (
                <div key={node.id} className="text-xs text-slate-700 border border-[#041627]/10 rounded px-2 py-2">
                  <p className="font-semibold">{node.title || `Entidad ${node.id}`}</p>
                  <p className="text-slate-500">{node.entity_type}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="border border-[#041627]/10 rounded-editorial p-3">
            <h3 className="text-sm font-semibold text-[#041627] mb-2">Relaciones</h3>
            <div className="space-y-2 max-h-[320px] overflow-y-auto">
              {graph.edges.map((edge) => (
                <div key={edge.id} className="text-xs text-slate-700 border border-[#041627]/10 rounded px-2 py-2">
                  <p className="font-semibold">{edge.relation_type}</p>
                  <p className="text-slate-500">
                    {edge.from_entity_id} {"->"} {edge.to_entity_id}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
