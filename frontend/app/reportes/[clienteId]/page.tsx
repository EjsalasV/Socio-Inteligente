"use client";

import Link from "next/link";
import { useState } from "react";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import { generateExecutivePdf } from "../../../lib/api/reportes";
import { formatMoney } from "../../../lib/formatters";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import { useDashboard } from "../../../lib/hooks/useDashboard";

export default function ReportesPage() {
  const { clienteId } = useAuditContext();
  const { data, isLoading, error } = useDashboard(clienteId);
  const [reportMsg, setReportMsg] = useState<string>("");
  const [generating, setGenerating] = useState<boolean>(false);

  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorMessage message={error} />;
  if (!data) return <ErrorMessage message="No hay datos para generar reportes." />;

  async function handleGeneratePdf(): Promise<void> {
    setGenerating(true);
    setReportMsg("");
    try {
      const meta = await generateExecutivePdf(clienteId);
      setReportMsg(`PDF generado: ${meta.report_name} (${(meta.size_bytes / 1024).toFixed(1)} KB)`);
    } catch (err) {
      setReportMsg(err instanceof Error ? err.message : "No se pudo generar el PDF.");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="pt-4 pb-10 space-y-8 max-w-[1400px]">
      <section className="rounded-editorial p-7 shadow-editorial text-white border border-[#041627]/20 bg-gradient-to-br from-[#041627] to-[#1a2b3c]">
        <p className="text-xs uppercase tracking-[0.2em] text-[#a5eff0] font-body">Centro de Reportes</p>
        <h1 className="font-headline text-5xl text-white mt-2">Reportes de Auditoria</h1>
        <p className="font-body text-slate-200 mt-3 leading-relaxed text-base">
          Cliente: <span className="font-semibold text-white">{data.nombre_cliente}</span> ·
          Periodo: <span className="font-semibold text-white"> {data.periodo || "Actual"}</span>
        </p>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        <article className="sovereign-card">
          <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">Resumen ejecutivo</p>
          <h3 className="font-headline text-2xl text-[#041627] mt-2">Situacion del encargo</h3>
          <p className="text-sm text-slate-600 mt-3">
            Riesgo global: <b>{data.riesgo_global}</b>. Avance: <b>{data.progreso_auditoria.toFixed(1)}%</b>.
          </p>
          <button
            type="button"
            onClick={() => void handleGeneratePdf()}
            disabled={generating}
            className="mt-5 px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-[0.12em] bg-[#041627] text-white disabled:opacity-60"
          >
            {generating ? "Generando..." : "Exportar PDF"}
          </button>
        </article>

        <article className="sovereign-card">
          <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">Materialidad</p>
          <h3 className="font-headline text-2xl text-[#041627] mt-2">{formatMoney(data.materialidad_global)}</h3>
          <p className="text-sm text-slate-600 mt-3">Base para pruebas sustantivas y evaluacion de desviaciones.</p>
          <button className="mt-5 px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-[0.12em] border border-[#041627]/20 text-[#041627]">
            Descargar
          </button>
        </article>

        <article className="sovereign-card">
          <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">Hallazgos criticos</p>
          <h3 className="font-headline text-2xl text-[#041627] mt-2">Top de areas sensibles</h3>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {(data.top_areas ?? []).slice(0, 3).map((x) => (
              <li key={x.codigo}>- {x.codigo} - {x.nombre}</li>
            ))}
          </ul>
          <button className="mt-5 px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-[0.12em] border border-[#041627]/20 text-[#041627]">
            Generar memo
          </button>
        </article>
      </section>

      {reportMsg ? <section className="sovereign-card text-sm text-slate-600">{reportMsg}</section> : null}

      <section className="sovereign-card">
        <h2 className="font-headline text-3xl text-[#041627] mb-4">Acciones</h2>
        <div className="flex flex-wrap gap-3">
          <Link href={`/socio-chat/${clienteId}`} className="px-4 py-2 rounded-xl bg-[#f1f4f6] text-sm text-slate-700 border border-black/10">
            Ir a Socio Chat
          </Link>
          <Link href={`/client-memory/${clienteId}`} className="px-4 py-2 rounded-xl bg-[#f1f4f6] text-sm text-slate-700 border border-black/10">
            Ver Client Memory
          </Link>
          <Link href={`/dashboard/${clienteId}`} className="px-4 py-2 rounded-xl bg-[#041627] text-sm text-white">
            Volver al Dashboard
          </Link>
        </div>
      </section>
    </div>
  );
}
