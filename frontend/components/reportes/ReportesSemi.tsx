"use client";

import { useMemo, useState } from "react";

type ReportArea = {
  codigo: string;
  nombre: string;
  estado: "Borrador" | "Finalizado" | "Pendiente revisión senior";
  auditor: string;
  fecha: string;
  hallazgosCount: number;
};

type Props = {
  areas: ReportArea[];
  onGenerateMissing: () => void;
};

function statusTone(status: ReportArea["estado"]): string {
  if (status === "Finalizado") return "bg-emerald-100 text-emerald-800 border-emerald-200";
  if (status === "Borrador") return "bg-amber-100 text-amber-800 border-amber-200";
  return "bg-slate-100 text-slate-700 border-slate-200";
}

export default function ReportesSemi({ areas, onGenerateMissing }: Props) {
  const [onlyPending, setOnlyPending] = useState<boolean>(false);
  const [selected, setSelected] = useState<Record<string, boolean>>({});

  const visible = useMemo(
    () => areas.filter((area) => (onlyPending ? area.estado !== "Finalizado" : true)),
    [areas, onlyPending],
  );

  const selectedCount = Object.values(selected).filter(Boolean).length;

  return (
    <section className="space-y-5">
      <div className="sovereign-card">
        <h2 className="font-headline text-3xl text-[#041627]">Reportes por Área</h2>
        <p className="mt-2 text-sm text-slate-600">
          Selecciona áreas para generar reportes de forma operativa y controlar pendientes de revisión senior.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => setOnlyPending((prev) => !prev)}
          className="rounded-lg border border-[#041627]/20 px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-[#041627]"
        >
          {onlyPending ? "Ver todas las áreas" : "Reportes pendientes"}
        </button>
        <button
          type="button"
          onClick={onGenerateMissing}
          className="rounded-lg bg-[#041627] px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-white"
        >
          Generar reportes faltantes
        </button>
        <span className="inline-flex items-center rounded-lg bg-[#f1f4f6] px-3 py-2 text-xs text-slate-600">
          Seleccionadas: {selectedCount}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {visible.map((area) => (
          <article key={`${area.codigo}-${area.nombre}`} className="sovereign-card">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-[10px] uppercase tracking-[0.12em] text-slate-500 font-bold">{area.codigo}</p>
                <h3 className="font-headline text-2xl text-[#041627] mt-1">{area.nombre}</h3>
              </div>
              <span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.1em] ${statusTone(area.estado)}`}>
                {area.estado}
              </span>
            </div>
            <p className="mt-2 text-xs text-slate-600">Auditor: {area.auditor} · Fecha: {area.fecha}</p>
            <p className="mt-1 text-xs text-slate-600">Hallazgos: {area.hallazgosCount}</p>

            <div className="mt-4 flex items-center justify-between gap-2">
              <label className="inline-flex items-center gap-2 text-xs text-slate-700">
                <input
                  type="checkbox"
                  checked={Boolean(selected[area.codigo])}
                  onChange={(event) =>
                    setSelected((prev) => ({
                      ...prev,
                      [area.codigo]: event.target.checked,
                    }))
                  }
                  className="h-4 w-4 rounded border-[#041627]/30"
                />
                Generar reporte de esta área
              </label>
              <button type="button" className="rounded-lg border border-[#041627]/20 px-3 py-2 text-xs text-[#041627]">
                Abrir
              </button>
            </div>
          </article>
        ))}
      </div>

      <section className="sovereign-card">
        <h3 className="font-headline text-2xl text-[#041627]">Resumen operativo</h3>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[760px] border-collapse text-sm">
            <thead>
              <tr className="border-b border-black/10 text-[10px] uppercase tracking-[0.12em] text-slate-500">
                <th className="py-2 pr-4 text-left">Área</th>
                <th className="py-2 pr-4 text-left">Estado</th>
                <th className="py-2 pr-4 text-left">Auditor</th>
                <th className="py-2 pr-4 text-left">Fecha</th>
                <th className="py-2 text-left">Acción sugerida</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((area) => (
                <tr key={`summary-${area.codigo}`} className="border-b border-black/5">
                  <td className="py-3 pr-4 text-[#041627] font-medium">{area.codigo} · {area.nombre}</td>
                  <td className="py-3 pr-4">{area.estado}</td>
                  <td className="py-3 pr-4">{area.auditor}</td>
                  <td className="py-3 pr-4">{area.fecha}</td>
                  <td className="py-3 text-slate-700">
                    {area.estado === "Finalizado" ? "Listo para revisión final" : "Completar y enviar a revisión senior"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </section>
  );
}
