"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

type AreaOption = {
  codigo: string;
  nombre: string;
};

type Props = {
  clienteId: string;
  areas: AreaOption[];
  isBusy: boolean;
  onGenerateDraft: () => void;
  onGenerateMemo: () => void;
  onViewSample: () => void;
};

export default function ReportesJunior({
  clienteId,
  areas,
  isBusy,
  onGenerateDraft,
  onGenerateMemo,
  onViewSample,
}: Props) {
  const [selectedArea, setSelectedArea] = useState<string>(areas[0]?.codigo ?? "");

  const activeArea = useMemo(
    () => areas.find((area) => area.codigo === selectedArea) ?? areas[0] ?? null,
    [areas, selectedArea],
  );

  return (
    <section className="space-y-5">
      <div className="sovereign-card">
        <h2 className="font-headline text-3xl text-[#041627]">Reportes - Guía Paso a Paso</h2>
        <p className="mt-2 text-sm text-slate-600">
          Flujo asistido para construir el informe con estructura clara y trazabilidad mínima.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <article className="sovereign-card space-y-4">
          <div>
            <p className="text-[10px] uppercase tracking-[0.12em] text-slate-500 font-bold">Mi Primer Reporte</p>
            <h3 className="font-headline text-2xl text-[#041627] mt-2">Wizard guiado en 3 pasos</h3>
          </div>

          <ol className="space-y-3 text-sm text-slate-700 list-decimal list-inside">
            <li>Elegir área prioritaria</li>
            <li>Seleccionar hallazgos y evidencia disponible</li>
            <li>Generar borrador para revisión</li>
          </ol>

          <label className="block text-[11px] uppercase tracking-[0.12em] text-slate-500 font-bold">
            Área del encargo
            <select
              value={selectedArea}
              onChange={(event) => setSelectedArea(event.target.value)}
              className="mt-1 w-full rounded-lg border border-[#041627]/15 bg-[#f1f4f6] px-3 py-2 text-sm text-slate-900 focus:border-[#89d3d4] focus:outline-none"
            >
              {areas.map((area) => (
                <option key={area.codigo} value={area.codigo}>
                  {area.codigo} · {area.nombre}
                </option>
              ))}
            </select>
          </label>

          <div className="rounded-lg border border-[#041627]/10 bg-[#f8fafc] p-3 text-xs text-slate-700">
            Área activa: <b>{activeArea ? `${activeArea.codigo} · ${activeArea.nombre}` : "Sin área"}</b>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={onGenerateDraft}
              disabled={isBusy}
              className="rounded-lg bg-[#041627] px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-white disabled:opacity-60"
            >
              {isBusy ? "Procesando..." : "Generar borrador"}
            </button>
            <button
              type="button"
              onClick={onViewSample}
              className="rounded-lg border border-[#041627]/20 px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-[#041627]"
            >
              Ver ejemplo
            </button>
          </div>

          <p className="text-[11px] text-slate-500">Basado en NIA 700 para estructura y emisión del informe.</p>
        </article>

        <article className="sovereign-card space-y-4">
          <div>
            <p className="text-[10px] uppercase tracking-[0.12em] text-slate-500 font-bold">Resumen para Dirección</p>
            <h3 className="font-headline text-2xl text-[#041627] mt-2">Template prellenado</h3>
          </div>
          <p className="text-sm text-slate-700 leading-relaxed">
            Genera un memo ejecutivo con foco en riesgos, hallazgos y recomendaciones accionables para gerencia.
          </p>
          <button
            type="button"
            onClick={onGenerateMemo}
            disabled={isBusy}
            className="rounded-lg border border-[#041627]/20 px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-[#041627] disabled:opacity-60"
          >
            {isBusy ? "Procesando..." : "Generar resumen"}
          </button>
          <div className="rounded-lg border border-[#a5eff0]/40 bg-[#a5eff0]/15 p-3 text-xs text-[#041627]">
            Consejo: vincula primero evidencia crítica para evitar bloqueos al pasar a revisión senior.
          </div>
          <Link
            href={`/areas/${clienteId}`}
            className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.12em] text-[#041627] underline"
          >
            <span className="material-symbols-outlined text-sm">arrow_forward</span>
            Ir a workspace de áreas
          </Link>
        </article>
      </div>
    </section>
  );
}
