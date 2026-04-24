"use client";

import type { MayorSummary } from "../../types/mayor";
import { formatMoney } from "../../lib/formatters";

type Props = {
  summary: MayorSummary;
  globalSummary?: MayorSummary | null;
  isLoading?: boolean;
};

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <article className="sovereign-card !p-4">
      <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">{label}</p>
      <p className="font-headline text-2xl text-[#041627] mt-2">{value}</p>
    </article>
  );
}

export default function MayorSummaryPanel({ summary, globalSummary = null, isLoading = false }: Props) {
  if (isLoading) {
    return <div className="sovereign-card h-24 animate-pulse bg-[#edf2f7]" />;
  }

  return (
    <section className="space-y-4">
      <div>
        <h2 className="font-headline text-2xl text-[#041627]">Resumen del Mayor</h2>
        <p className="text-xs text-slate-500 mt-1">Los valores principales se calculan sobre el resultado filtrado.</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Metric label="Debe (filtrado)" value={formatMoney(summary.total_debe, "COP", 0)} />
        <Metric label="Haber (filtrado)" value={formatMoney(summary.total_haber, "COP", 0)} />
        <Metric label="Neto (filtrado)" value={formatMoney(summary.total_neto, "COP", 0)} />
      </div>
      <div className="sovereign-card !p-4">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
          <div>
            <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">Movimientos</p>
            <p className="mt-1 font-semibold text-slate-800">{summary.total_movimientos}</p>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">Cuentas</p>
            <p className="mt-1 font-semibold text-slate-800">{summary.cuentas_distintas}</p>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">Asientos</p>
            <p className="mt-1 font-semibold text-slate-800">{summary.asientos_distintos}</p>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">Rango</p>
            <p className="mt-1 font-semibold text-slate-800">
              {summary.fecha_min || "N/A"} - {summary.fecha_max || "N/A"}
            </p>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">Promedio</p>
            <p className="mt-1 font-semibold text-slate-800">{formatMoney(summary.monto_promedio, "COP", 0)}</p>
          </div>
        </div>
        {globalSummary ? (
          <p className="mt-3 text-xs text-slate-500">
            Total global de movimientos (sin filtros): {globalSummary.total_movimientos}
          </p>
        ) : null}
      </div>
    </section>
  );
}
