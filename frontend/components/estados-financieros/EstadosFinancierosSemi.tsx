"use client";

import { useMemo } from "react";

import type { FinancialRatio } from "./types";
import { statusColors, statusLabel } from "./types";

const SEMI_RATIO_ORDER = ["Liquidez Corriente", "Prueba Ácida", "Endeudamiento", "Apalancamiento", "ROA", "ROE"] as const;

function actionIfRed(label: string): string {
  if (label === "Liquidez Corriente" || label === "Prueba Ácida") {
    return "Revisar envejecimiento de cartera, plazos de proveedores y capacidad de caja proyectada.";
  }
  if (label === "Endeudamiento" || label === "Apalancamiento") {
    return "Validar covenants, clasificación de pasivos y divulgaciones de riesgo financiero.";
  }
  return "Profundizar pruebas sustantivas en ingresos, costos y estimaciones de cierre.";
}

type Props = {
  ratios: FinancialRatio[];
};

export default function EstadosFinancierosSemi({ ratios }: Props) {
  const selected = useMemo(
    () =>
      SEMI_RATIO_ORDER.map((label) => ratios.find((ratio) => ratio.label === label)).filter(
        (ratio): ratio is FinancialRatio => Boolean(ratio),
      ),
    [ratios],
  );

  return (
    <section className="space-y-6">
      <div className="sovereign-card">
        <h2 className="font-headline text-3xl text-[#041627]">Análisis de Índices Financieros</h2>
        <p className="mt-2 text-sm text-slate-600">
          Vista operativa para priorizar pruebas con base en liquidez, solvencia y rentabilidad.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {selected.map((ratio) => {
          const colors = statusColors(ratio.status);
          return (
            <article key={ratio.label} className={`rounded-xl border p-5 shadow-sm ${colors.card}`}>
              <div className="flex items-center justify-between gap-2">
                <h3 className="font-semibold text-[#041627] text-sm">{ratio.label}</h3>
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${colors.badge}`}>
                  {statusLabel(ratio.status)}
                </span>
              </div>
              <p className={`mt-2 font-headline text-3xl ${colors.value}`}>{ratio.formatted}</p>
              <p className="mt-1 text-[11px] text-slate-500">Benchmark: {ratio.benchmark}</p>

              <div className="mt-3 rounded-lg border border-white/80 bg-white/70 p-3">
                <p className="text-[11px] uppercase tracking-[0.12em] text-slate-500 font-bold">Qué hacer si está en rojo</p>
                <p className="mt-1 text-xs text-slate-700">{actionIfRed(ratio.label)}</p>
              </div>

              <p className="mt-2 text-[10px] text-slate-500">Referencia {ratio.nia}</p>
            </article>
          );
        })}
      </div>

      <section className="sovereign-card">
        <h3 className="font-headline text-2xl text-[#041627]">Resumen de acción</h3>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[680px] border-collapse text-sm">
            <thead>
              <tr className="border-b border-black/10 text-[10px] uppercase tracking-[0.12em] text-slate-500">
                <th className="py-2 pr-4 text-left">Ratio</th>
                <th className="py-2 pr-4 text-left">Valor</th>
                <th className="py-2 pr-4 text-left">Benchmark</th>
                <th className="py-2 pr-4 text-left">Estado</th>
                <th className="py-2 text-left">Acción sugerida</th>
              </tr>
            </thead>
            <tbody>
              {selected.map((ratio) => (
                <tr key={`row-${ratio.label}`} className="border-b border-black/5">
                  <td className="py-3 pr-4 text-[#041627] font-medium">{ratio.label}</td>
                  <td className="py-3 pr-4">{ratio.formatted}</td>
                  <td className="py-3 pr-4 text-slate-600">{ratio.benchmark}</td>
                  <td className="py-3 pr-4">{statusLabel(ratio.status)}</td>
                  <td className="py-3 text-slate-700">{actionIfRed(ratio.label)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </section>
  );
}

