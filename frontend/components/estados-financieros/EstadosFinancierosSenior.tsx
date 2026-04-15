"use client";

import Link from "next/link";

import type { FinancialRatio } from "./types";
import { CATEGORY_LABELS, RATIO_FORMULAS, statusColors, statusLabel } from "./types";

type Props = {
  ratios: FinancialRatio[];
};

export default function EstadosFinancierosSenior({ ratios }: Props) {
  const categories: FinancialRatio["category"][] = ["liquidez", "solvencia", "rentabilidad"];

  return (
    <section className="space-y-6">
      <div className="sovereign-card">
        <h2 className="font-headline text-3xl text-[#041627]">Índices Financieros - Análisis Técnico</h2>
        <p className="mt-2 text-sm text-slate-600">
          Vista completa con los 9 indicadores, fórmulas y notas de auditoría para soporte técnico del equipo.
        </p>
      </div>

      {categories.map((category) => {
        const categoryRatios = ratios.filter((ratio) => ratio.category === category);
        if (categoryRatios.length === 0) return null;

        return (
          <section key={category}>
            <h3 className="font-headline text-2xl text-[#041627] mb-4">{CATEGORY_LABELS[category]}</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
              {categoryRatios.map((ratio) => {
                const colors = statusColors(ratio.status);
                return (
                  <article key={ratio.label} className={`rounded-xl border p-5 shadow-sm ${colors.card}`}>
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-semibold text-[#041627] text-sm">{ratio.label}</p>
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${colors.badge}`}>
                        {statusLabel(ratio.status)}
                      </span>
                    </div>
                    <p className={`mt-2 font-headline text-3xl ${colors.value}`}>{ratio.formatted}</p>
                    <p className="mt-1 text-[11px] text-slate-500">Benchmark: {ratio.benchmark}</p>
                    <p className="mt-2 text-xs text-slate-600">Fórmula: {RATIO_FORMULAS[ratio.label] ?? "Definición técnica"}</p>
                    <p className="mt-2 text-xs text-slate-700">{ratio.audit_note}</p>
                    <p className="mt-2 text-[10px] uppercase tracking-[0.1em] text-slate-500">{ratio.nia}</p>
                  </article>
                );
              })}
            </div>
          </section>
        );
      })}

      <section className="sovereign-card">
        <h3 className="font-headline text-2xl text-[#041627]">Tabla técnica consolidada</h3>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[860px] border-collapse text-sm">
            <thead>
              <tr className="border-b border-black/10 text-[10px] uppercase tracking-[0.12em] text-slate-500">
                <th className="py-2 pr-4 text-left">Ratio</th>
                <th className="py-2 pr-4 text-left">Valor</th>
                <th className="py-2 pr-4 text-left">Fórmula</th>
                <th className="py-2 pr-4 text-left">Benchmark</th>
                <th className="py-2 pr-4 text-left">Estado</th>
                <th className="py-2 text-left">NIA</th>
              </tr>
            </thead>
            <tbody>
              {ratios.map((ratio) => (
                <tr key={`full-${ratio.label}`} className="border-b border-black/5">
                  <td className="py-3 pr-4 font-medium text-[#041627]">{ratio.label}</td>
                  <td className="py-3 pr-4">{ratio.formatted}</td>
                  <td className="py-3 pr-4 text-slate-600">{RATIO_FORMULAS[ratio.label] ?? "N/D"}</td>
                  <td className="py-3 pr-4 text-slate-600">{ratio.benchmark}</td>
                  <td className="py-3 pr-4">{statusLabel(ratio.status)}</td>
                  <td className="py-3">{ratio.nia}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="sovereign-card">
        <h3 className="font-headline text-2xl text-[#041627]">Tendencias</h3>
        <p className="mt-2 text-sm text-slate-600">
          Histórico no disponible en este corte. Cuando existan períodos comparativos, aquí se mostrará la tendencia (↑/↓) por ratio.
        </p>
      </section>

      <section className="rounded-xl border border-[#041627]/15 bg-[#f8fafc] p-4 text-sm text-slate-700">
        <p>
          Referencias clave: <Link className="underline" href="/biblioteca">NIA 320</Link> para materialidad y <Link className="underline" href="/biblioteca">NIA 540</Link> para estimaciones contables.
        </p>
      </section>
    </section>
  );
}

