"use client";

import type { KnowledgeEntity } from "../../types/knowledge";

type Props = {
  items: KnowledgeEntity[];
  total: number;
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  isLoading?: boolean;
};

export default function KnowledgeEntitiesTab({
  items,
  total,
  page,
  totalPages,
  onPageChange,
  isLoading = false,
}: Props) {
  return (
    <section className="sovereign-card p-5 space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h2 className="font-headline text-2xl text-[#041627]">Entidades</h2>
        <p className="text-xs text-slate-500">Total: {total}</p>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full border-separate border-spacing-0">
          <thead>
            <tr>
              <th className="text-left text-xs uppercase tracking-[0.1em] text-slate-500 px-3 py-2">Tipo</th>
              <th className="text-left text-xs uppercase tracking-[0.1em] text-slate-500 px-3 py-2">Titulo</th>
              <th className="text-left text-xs uppercase tracking-[0.1em] text-slate-500 px-3 py-2">Modulo</th>
              <th className="text-left text-xs uppercase tracking-[0.1em] text-slate-500 px-3 py-2">Actualizado</th>
            </tr>
          </thead>
          <tbody>
            {items.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-3 py-6 text-sm text-slate-500">
                  {isLoading ? "Cargando entidades..." : "Sin entidades para mostrar."}
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr key={item.id} className="border-t border-[#041627]/10">
                  <td className="px-3 py-3 text-xs text-slate-600">{item.entity_type}</td>
                  <td className="px-3 py-3 text-sm text-slate-800">{item.title || "-"}</td>
                  <td className="px-3 py-3 text-xs text-slate-600">{item.source_module}</td>
                  <td className="px-3 py-3 text-xs text-slate-600">{item.updated_at || "-"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-500">
          Pagina {page} de {Math.max(1, totalPages)}
        </p>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="rounded-editorial px-3 py-2 text-xs font-semibold border border-[#041627]/20 min-h-[44px] disabled:opacity-50"
            onClick={() => onPageChange(Math.max(1, page - 1))}
            disabled={page <= 1 || isLoading}
          >
            Anterior
          </button>
          <button
            type="button"
            className="rounded-editorial px-3 py-2 text-xs font-semibold border border-[#041627]/20 min-h-[44px] disabled:opacity-50"
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages || isLoading}
          >
            Siguiente
          </button>
        </div>
      </div>
    </section>
  );
}

