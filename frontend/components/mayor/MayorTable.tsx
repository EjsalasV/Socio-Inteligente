"use client";

import type { MayorMovement } from "../../types/mayor";
import { formatMoney } from "../../lib/formatters";

type Props = {
  items: MayorMovement[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  isLoading?: boolean;
  onPageChange: (nextPage: number) => void;
};

export default function MayorTable({
  items,
  total,
  page,
  pageSize,
  totalPages,
  isLoading = false,
  onPageChange,
}: Props) {
  const canPrev = page > 1;
  const canNext = page < totalPages;
  const from = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const to = total === 0 ? 0 : Math.min(page * pageSize, total);

  return (
    <section className="sovereign-card !p-0 overflow-hidden">
      <div className="p-5 border-b border-black/5 flex items-center justify-between gap-3">
        <div>
          <h2 className="font-headline text-2xl text-[#041627]">Movimientos del Mayor</h2>
          <p className="text-xs text-slate-500 mt-1">
            Mostrando {from}-{to} de {total}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="rounded-editorial px-3 py-2 text-xs uppercase tracking-[0.12em] font-bold border border-[#041627]/15 text-slate-600 hover:bg-[#f5f8fb] min-h-[44px] disabled:opacity-50"
            onClick={() => onPageChange(page - 1)}
            disabled={!canPrev || isLoading}
          >
            Anterior
          </button>
          <span className="text-xs text-slate-500">
            Página {page} de {totalPages}
          </span>
          <button
            type="button"
            className="rounded-editorial px-3 py-2 text-xs uppercase tracking-[0.12em] font-bold border border-[#041627]/15 text-slate-600 hover:bg-[#f5f8fb] min-h-[44px] disabled:opacity-50"
            onClick={() => onPageChange(page + 1)}
            disabled={!canNext || isLoading}
          >
            Siguiente
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead className="bg-[#f1f4f6]/70">
            <tr>
              <th className="px-4 py-3 text-left text-[10px] uppercase tracking-[0.16em] text-slate-500">Fecha</th>
              <th className="px-4 py-3 text-left text-[10px] uppercase tracking-[0.16em] text-slate-500">Asiento</th>
              <th className="px-4 py-3 text-left text-[10px] uppercase tracking-[0.16em] text-slate-500">Cuenta</th>
              <th className="px-4 py-3 text-left text-[10px] uppercase tracking-[0.16em] text-slate-500">Nombre</th>
              <th className="px-4 py-3 text-left text-[10px] uppercase tracking-[0.16em] text-slate-500">L/S</th>
              <th className="px-4 py-3 text-left text-[10px] uppercase tracking-[0.16em] text-slate-500">Referencia</th>
              <th className="px-4 py-3 text-right text-[10px] uppercase tracking-[0.16em] text-slate-500">Debe</th>
              <th className="px-4 py-3 text-right text-[10px] uppercase tracking-[0.16em] text-slate-500">Haber</th>
              <th className="px-4 py-3 text-right text-[10px] uppercase tracking-[0.16em] text-slate-500">Neto</th>
            </tr>
          </thead>
          <tbody>
            {isLoading
              ? Array.from({ length: 6 }).map((_, idx) => (
                  <tr key={`sk-${idx}`} className="border-b border-black/5">
                    {Array.from({ length: 9 }).map((__, cidx) => (
                      <td key={`${idx}-${cidx}`} className="px-4 py-4">
                        <div className="h-3 w-full rounded bg-[#edf2f7] animate-pulse" />
                      </td>
                    ))}
                  </tr>
                ))
              : null}

            {!isLoading &&
              items.map((row) => (
                <tr key={row.row_hash} className="border-b border-black/5 hover:bg-[#f8fbff]">
                  <td className="px-4 py-3 text-slate-700">{row.fecha || "-"}</td>
                  <td className="px-4 py-3 text-slate-700">{row.asiento_ref || "-"}</td>
                  <td className="px-4 py-3 text-slate-700">{row.numero_cuenta || "-"}</td>
                  <td className="px-4 py-3 text-slate-700">{row.nombre_cuenta || "-"}</td>
                  <td className="px-4 py-3 text-slate-700">{row.ls || "-"}</td>
                  <td className="px-4 py-3 text-slate-700">{row.referencia || "-"}</td>
                  <td className="px-4 py-3 text-right text-emerald-700 font-medium">{formatMoney(row.debe, "COP", 0)}</td>
                  <td className="px-4 py-3 text-right text-rose-700 font-medium">{formatMoney(row.haber, "COP", 0)}</td>
                  <td className={`px-4 py-3 text-right font-semibold ${row.neto >= 0 ? "text-emerald-700" : "text-rose-700"}`}>
                    {formatMoney(row.neto, "COP", 0)}
                  </td>
                </tr>
              ))}

            {!isLoading && items.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-4 py-10 text-center text-slate-500">
                  No hay movimientos que cumplan los filtros actuales.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}
