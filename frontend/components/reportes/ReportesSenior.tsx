"use client";

import { useMemo, useState } from "react";

type ReportSummary = {
  area: string;
  estado: string;
  auditor: string;
  fecha: string;
  hallazgosCount: number;
};

type Props = {
  reports: ReportSummary[];
};

export default function ReportesSenior({ reports }: Props) {
  const [statusFilter, setStatusFilter] = useState<string>("todos");
  const [auditorFilter, setAuditorFilter] = useState<string>("todos");

  const auditors = useMemo(() => {
    const unique = new Set(reports.map((report) => report.auditor));
    return Array.from(unique).sort();
  }, [reports]);

  const filtered = useMemo(
    () =>
      reports.filter((report) => {
        const statusOk = statusFilter === "todos" || report.estado === statusFilter;
        const auditorOk = auditorFilter === "todos" || report.auditor === auditorFilter;
        return statusOk && auditorOk;
      }),
    [reports, statusFilter, auditorFilter],
  );

  const stats = useMemo(() => {
    const listos = reports.filter((report) => report.estado === "Finalizado").length;
    const revision = reports.filter((report) => report.estado === "Pendiente revisión senior").length;
    const pendientes = reports.filter((report) => report.estado !== "Finalizado").length;
    return { listos, revision, pendientes };
  }, [reports]);

  return (
    <section className="space-y-5">
      <div className="sovereign-card">
        <h2 className="font-headline text-3xl text-[#041627]">Reportes de Auditoría</h2>
        <p className="mt-2 text-sm text-slate-600">
          Vista técnica completa para revisión, control de estados y exportación consolidada.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <article className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
          <p className="text-[10px] uppercase tracking-[0.12em] text-emerald-800 font-bold">Listos</p>
          <p className="mt-2 font-headline text-3xl text-emerald-800">{stats.listos}</p>
        </article>
        <article className="rounded-xl border border-amber-200 bg-amber-50 p-4">
          <p className="text-[10px] uppercase tracking-[0.12em] text-amber-800 font-bold">En revisión</p>
          <p className="mt-2 font-headline text-3xl text-amber-800">{stats.revision}</p>
        </article>
        <article className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-[10px] uppercase tracking-[0.12em] text-slate-700 font-bold">Pendientes</p>
          <p className="mt-2 font-headline text-3xl text-slate-700">{stats.pendientes}</p>
        </article>
      </div>

      <article className="sovereign-card">
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            className="rounded-lg border border-[#041627]/15 bg-[#f1f4f6] px-3 py-2 text-sm text-slate-900"
          >
            <option value="todos">Estado: todos</option>
            <option value="Finalizado">Finalizado</option>
            <option value="Borrador">Borrador</option>
            <option value="Pendiente revisión senior">Pendiente revisión senior</option>
          </select>
          <select
            value={auditorFilter}
            onChange={(event) => setAuditorFilter(event.target.value)}
            className="rounded-lg border border-[#041627]/15 bg-[#f1f4f6] px-3 py-2 text-sm text-slate-900"
          >
            <option value="todos">Auditor: todos</option>
            {auditors.map((auditor) => (
              <option key={auditor} value={auditor}>
                {auditor}
              </option>
            ))}
          </select>
          <button type="button" className="rounded-lg bg-[#041627] px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-white">
            Descargar todos en ZIP
          </button>
        </div>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[820px] border-collapse text-sm">
            <thead>
              <tr className="border-b border-black/10 text-[10px] uppercase tracking-[0.12em] text-slate-500">
                <th className="py-2 pr-4 text-left">Área</th>
                <th className="py-2 pr-4 text-left">Estado</th>
                <th className="py-2 pr-4 text-left">Auditor</th>
                <th className="py-2 pr-4 text-left">Fecha</th>
                <th className="py-2 pr-4 text-left">Hallazgos</th>
                <th className="py-2 text-left">Acción</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((report, idx) => (
                <tr key={`${report.area}-${idx}`} className="border-b border-black/5">
                  <td className="py-3 pr-4 text-[#041627] font-medium">{report.area}</td>
                  <td className="py-3 pr-4">{report.estado}</td>
                  <td className="py-3 pr-4">{report.auditor}</td>
                  <td className="py-3 pr-4">{report.fecha}</td>
                  <td className="py-3 pr-4">{report.hallazgosCount}</td>
                  <td className="py-3 text-slate-700">Revisar</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>
    </section>
  );
}
