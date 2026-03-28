"use client";

import { useMemo, useState } from "react";

import { formatMoney } from "../../lib/formatters";
import type { AreaCuenta } from "../../types/area";

type Props = {
  cuentas: AreaCuenta[];
  currentYear: string;
  previousYear: string;
  title?: string;
  onToggleCheck?: (codigo: string, checked: boolean) => Promise<void>;
};

function moneyClass(value: number): string {
  return value < 0 ? "text-editorial-error" : "text-navy-900";
}

export default function LeadSchedule({ cuentas, currentYear, previousYear, title, onToggleCheck }: Props) {
  const [pending, setPending] = useState<Record<string, boolean>>({});

  const sorted = useMemo(() => {
    return [...cuentas].sort((a, b) => a.codigo.localeCompare(b.codigo));
  }, [cuentas]);

  async function handleCheck(codigo: string, checked: boolean): Promise<void> {
    if (!onToggleCheck) return;
    setPending((prev) => ({ ...prev, [codigo]: true }));
    try {
      await onToggleCheck(codigo, checked);
    } finally {
      setPending((prev) => ({ ...prev, [codigo]: false }));
    }
  }

  return (
    <section className="sovereign-card overflow-hidden">
      <header className="mb-4">
        <h3 className="font-headline text-2xl text-navy-900">{title || "Lead Schedule Editorial"}</h3>
        <p className="font-body text-sm text-slate-500 mt-1">Comparativo de cuentas y variaciones del área.</p>
      </header>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="text-left border-b border-slate-100">
              <th className="py-3 px-2 font-body text-xs uppercase tracking-[0.12em] text-slate-500">Código</th>
              <th className="py-3 px-2 font-body text-xs uppercase tracking-[0.12em] text-slate-500">Cuenta</th>
              <th className="py-3 px-2 text-right font-body text-xs uppercase tracking-[0.12em] text-slate-500">{currentYear}</th>
              <th className="py-3 px-2 text-right font-body text-xs uppercase tracking-[0.12em] text-slate-500">{previousYear}</th>
              <th className="py-3 px-2 text-right font-body text-xs uppercase tracking-[0.12em] text-slate-500">Monto Var.</th>
              <th className="py-3 px-2 text-right font-body text-xs uppercase tracking-[0.12em] text-slate-500">% Var.</th>
              <th className="py-3 px-2 text-center font-body text-xs uppercase tracking-[0.12em] text-slate-500">Check</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((row) => {
              const montoVar = row.saldo_actual - row.saldo_anterior;
              const pctVar = row.saldo_anterior !== 0 ? (montoVar / Math.abs(row.saldo_anterior)) * 100 : 0;
              const highVariation = Math.abs(pctVar) > 10;
              const loading = Boolean(pending[row.codigo]);

              return (
                <tr key={row.codigo} className="border-b border-black/5 hover:bg-[#f7fafc] transition-colors">
                  <td className="py-3 px-2 font-body text-sm text-slate-700">{row.codigo}</td>
                  <td
                    className={`py-3 px-2 ${
                      row.nivel <= 1
                        ? "font-headline text-lg font-semibold text-navy-900"
                        : "font-body text-sm text-slate-700 pl-6"
                    }`}
                  >
                    {row.nombre}
                  </td>
                  <td className={`py-3 px-2 text-right font-body text-sm ${moneyClass(row.saldo_actual)}`}>{formatMoney(row.saldo_actual)}</td>
                  <td className={`py-3 px-2 text-right font-body text-sm ${moneyClass(row.saldo_anterior)}`}>{formatMoney(row.saldo_anterior)}</td>
                  <td className={`py-3 px-2 text-right font-body text-sm ${moneyClass(montoVar)}`}>{formatMoney(montoVar)}</td>
                  <td className={`py-3 px-2 text-right font-body text-sm ${highVariation ? "text-amber-700 bg-amber-50/70 rounded" : moneyClass(pctVar)}`}>
                    {pctVar.toFixed(2)}%
                  </td>
                  <td className="py-3 px-2 text-center">
                    <button
                      type="button"
                      disabled={loading}
                      className={`w-7 h-7 rounded-full border border-ghost inline-flex items-center justify-center transition-colors ${
                        row.checked ? "bg-emerald-700/10 text-emerald-700" : "bg-white text-slate-400"
                      } ${loading ? "opacity-60" : ""}`}
                      onClick={() => void handleCheck(row.codigo, !row.checked)}
                      aria-label={`Marcar cuenta ${row.codigo}`}
                    >
                      <span className="material-symbols-outlined text-base">{row.checked ? "check_circle" : "radio_button_unchecked"}</span>
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
