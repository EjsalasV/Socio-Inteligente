"use client";

import { useMemo, useState } from "react";

import type { FinancialRatio } from "./types";
import { statusColors, statusLabel } from "./types";

const JUNIOR_RATIO_ORDER = ["Liquidez Corriente", "Endeudamiento", "ROA", "Margen Neto"] as const;

function meaningText(label: string, raw: number): string {
  if (label === "Liquidez Corriente") {
    if (raw < 1) {
      return "Si liquidez < 1, significa que tienes menos efectivo y activos corrientes que deudas a pagar este año.";
    }
    if (raw < 1.5) {
      return "La liquidez alcanza para cubrir obligaciones de corto plazo, pero con poco margen de maniobra.";
    }
    return "La empresa tiene una posición cómoda para cubrir sus obligaciones de corto plazo.";
  }
  if (label === "Endeudamiento") {
    if (raw >= 0.75) return "La empresa depende fuertemente de deuda y esto eleva el riesgo financiero.";
    if (raw >= 0.6) return "La deuda es relevante y conviene revisar covenants y capacidad de pago.";
    return "La carga de deuda es manejable frente al tamaño del activo.";
  }
  if (label === "ROA") {
    if (raw < 0) return "La operación está destruyendo valor sobre los activos.";
    if (raw < 0.03) return "La rentabilidad sobre activos es baja y puede presionar decisiones contables.";
    return "La rentabilidad sobre activos es saludable para el nivel de riesgo actual.";
  }
  if (raw < 0) return "El margen neto negativo indica pérdidas y requiere atención inmediata.";
  if (raw < 0.05) return "El margen es estrecho; pequeñas desviaciones pueden afectar materialmente el resultado.";
  return "El margen neto permite absorber variaciones razonables sin presión excesiva.";
}

type Props = {
  ratios: FinancialRatio[];
};

export default function EstadosFinancierosJunior({ ratios }: Props) {
  const [openDetail, setOpenDetail] = useState<Record<string, boolean>>({});

  const selected = useMemo(
    () =>
      JUNIOR_RATIO_ORDER.map((label) => ratios.find((ratio) => ratio.label === label)).filter(
        (ratio): ratio is FinancialRatio => Boolean(ratio),
      ),
    [ratios],
  );

  if (selected.length === 0) {
    return (
      <section className="sovereign-card">
        <h2 className="font-headline text-3xl text-[#041627]">¿Cómo interpretar las señales financieras?</h2>
        <p className="mt-3 text-sm text-slate-600">Aún no hay datos suficientes para mostrar los indicadores clave.</p>
      </section>
    );
  }

  return (
    <section className="space-y-5">
      <div className="sovereign-card">
        <h2 className="font-headline text-3xl text-[#041627]">¿Cómo interpretar las señales financieras?</h2>
        <p className="mt-2 text-sm text-slate-600">
          Empieza por estos 4 indicadores para identificar si hay presión de liquidez, deuda o rentabilidad.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {selected.map((ratio) => {
          const colors = statusColors(ratio.status);
          const isOpen = Boolean(openDetail[ratio.label]);

          return (
            <article key={ratio.label} className={`rounded-xl border p-5 shadow-sm ${colors.card}`}>
              <div className="flex items-center justify-between gap-3">
                <h3 className="font-headline text-2xl text-[#041627]">{ratio.label}</h3>
                <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.1em] ${colors.badge}`}>
                  {statusLabel(ratio.status)}
                </span>
              </div>

              <p className={`mt-3 font-headline text-4xl ${colors.value}`}>{ratio.formatted}</p>

              <div className="mt-4 rounded-lg border border-white/80 bg-white/70 p-3">
                <p className="text-[11px] uppercase tracking-[0.12em] text-slate-500 font-bold">¿Qué significa?</p>
                <p className="mt-1 text-sm text-slate-700">{meaningText(ratio.label, ratio.rawValue)}</p>
              </div>

              <button
                type="button"
                onClick={() =>
                  setOpenDetail((prev) => ({
                    ...prev,
                    [ratio.label]: !prev[ratio.label],
                  }))
                }
                className="mt-4 inline-flex items-center gap-2 rounded-lg border border-[#041627]/20 bg-white px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-[#041627]"
              >
                <span className="material-symbols-outlined text-base">{isOpen ? "expand_less" : "expand_more"}</span>
                Ver detalle técnico
              </button>

              {isOpen ? (
                <div className="mt-3 rounded-lg border border-[#041627]/10 bg-white p-3 text-sm text-slate-700">
                  <p>
                    Benchmark: <b>{ratio.benchmark}</b>
                  </p>
                  <p className="mt-1">
                    Referencia: <b>{ratio.nia}</b>
                  </p>
                  <p className="mt-2 text-xs text-slate-600">{ratio.audit_note}</p>
                </div>
              ) : null}
            </article>
          );
        })}
      </div>
    </section>
  );
}
