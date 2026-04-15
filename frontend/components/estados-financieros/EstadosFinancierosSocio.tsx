"use client";

import { useMemo, useState } from "react";

import type { FinancialRatio } from "./types";
import { statusLabel } from "./types";

type Props = {
  ratios: FinancialRatio[];
};

function trafficLabel(ratios: FinancialRatio[]): { label: string; tone: string } {
  const hasRisk = ratios.some((ratio) => ratio.status === "risk");
  if (hasRisk) {
    return { label: "Requiere atención", tone: "bg-rose-100 text-rose-800 border-rose-200" };
  }
  const hasWarning = ratios.some((ratio) => ratio.status === "warning");
  if (hasWarning) {
    return { label: "Atención moderada", tone: "bg-amber-100 text-amber-800 border-amber-200" };
  }
  return { label: "Financieramente sano", tone: "bg-emerald-100 text-emerald-800 border-emerald-200" };
}

export default function EstadosFinancierosSocio({ ratios }: Props) {
  const [showTechnical, setShowTechnical] = useState<boolean>(false);

  const liquidity = useMemo(() => ratios.find((ratio) => ratio.label === "Liquidez Corriente") ?? null, [ratios]);
  const debt = useMemo(() => ratios.find((ratio) => ratio.label === "Endeudamiento") ?? null, [ratios]);
  const profitability = useMemo(() => ratios.find((ratio) => ratio.label === "Margen Neto") ?? ratios.find((ratio) => ratio.label === "ROE") ?? null, [ratios]);

  const executiveSet = [liquidity, debt, profitability].filter((ratio): ratio is FinancialRatio => Boolean(ratio));
  const traffic = trafficLabel(executiveSet);

  const rationale = useMemo(() => {
    if (executiveSet.length === 0) {
      return "No hay datos suficientes para emitir una lectura ejecutiva de salud financiera en este corte.";
    }

    const parts = executiveSet.map((ratio) => {
      if (ratio.status === "risk") {
        return `${ratio.label.toLowerCase()} en nivel crítico`;
      }
      if (ratio.status === "warning") {
        return `${ratio.label.toLowerCase()} en vigilancia`;
      }
      return `${ratio.label.toLowerCase()} estable`;
    });

    return `La condición financiera se explica por ${parts.join(", ")}. Se recomienda mantener foco en la evidencia que soporte continuidad, cumplimiento de obligaciones y consistencia del resultado del periodo.`;
  }, [executiveSet]);

  return (
    <section className="space-y-6">
      <div className="sovereign-card">
        <h2 className="font-headline text-3xl text-[#041627]">Resumen Ejecutivo - Salud Financiera</h2>
        <p className="mt-2 text-sm text-slate-600">
          Lectura ejecutiva de liquidez, deuda y rentabilidad para decisión de cierre.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[liquidity, debt, profitability].map((ratio, idx) => (
          <article key={ratio?.label ?? `kpi-${idx}`} className="sovereign-card min-h-[132px]">
            <p className="text-[10px] uppercase tracking-[0.12em] text-slate-500 font-bold">
              {idx === 0 ? "Liquidez" : idx === 1 ? "Endeudamiento" : "Rentabilidad"}
            </p>
            <p className="mt-2 font-headline text-3xl text-[#041627]">{ratio?.formatted ?? "N/D"}</p>
            <span
              className={`mt-2 inline-flex rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.1em] ${{
                ok: "bg-emerald-100 text-emerald-800 border-emerald-200",
                warning: "bg-amber-100 text-amber-800 border-amber-200",
                risk: "bg-rose-100 text-rose-800 border-rose-200",
              }[(ratio?.status ?? "warning") as "ok" | "warning" | "risk"]}`}
            >
              {ratio ? statusLabel(ratio.status) : "Sin dato"}
            </span>
          </article>
        ))}
      </div>

      <article className="rounded-xl border p-4 text-sm font-semibold uppercase tracking-[0.12em] w-fit">
        <span className={`rounded-full border px-3 py-1 ${traffic.tone}`}>{traffic.label}</span>
      </article>

      <article className="rounded-xl bg-[#041627] border border-[#89d3d4]/25 p-6 text-white">
        <p className="text-[10px] uppercase tracking-[0.16em] text-[#89d3d4] font-bold mb-2">¿Por qué está así?</p>
        <p className="text-sm leading-relaxed">{rationale}</p>
      </article>

      <section className="sovereign-card">
        <button
          type="button"
          onClick={() => setShowTechnical((prev) => !prev)}
          className="inline-flex items-center gap-2 rounded-lg border border-[#041627]/20 px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-[#041627]"
        >
          <span className="material-symbols-outlined text-base">{showTechnical ? "expand_less" : "expand_more"}</span>
          {showTechnical ? "Ocultar análisis técnico" : "Ver análisis técnico"}
        </button>

        {showTechnical ? (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[700px] border-collapse text-sm">
              <thead>
                <tr className="border-b border-black/10 text-[10px] uppercase tracking-[0.12em] text-slate-500">
                  <th className="py-2 pr-4 text-left">Ratio</th>
                  <th className="py-2 pr-4 text-left">Valor</th>
                  <th className="py-2 pr-4 text-left">Estado</th>
                  <th className="py-2 text-left">NIA</th>
                </tr>
              </thead>
              <tbody>
                {ratios.map((ratio) => (
                  <tr key={`exec-${ratio.label}`} className="border-b border-black/5">
                    <td className="py-3 pr-4 text-[#041627] font-medium">{ratio.label}</td>
                    <td className="py-3 pr-4">{ratio.formatted}</td>
                    <td className="py-3 pr-4">{statusLabel(ratio.status)}</td>
                    <td className="py-3">{ratio.nia}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </section>
  );
}
