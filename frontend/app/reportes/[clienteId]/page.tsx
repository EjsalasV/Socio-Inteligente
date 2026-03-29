"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import {
  downloadExecutivePdf,
  downloadExecutivePdfByPath,
  generateExecutiveMemo,
  generateExecutivePdf,
  getExecutiveMemo,
  getReportHistory,
  type ReportHistoryPayload,
} from "../../../lib/api/reportes";
import { formatMoney } from "../../../lib/formatters";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import { useDashboard } from "../../../lib/hooks/useDashboard";

function gateTone(status: string): string {
  return status === "ok"
    ? "bg-emerald-50 text-emerald-700 border-emerald-200"
    : "bg-red-50 text-red-700 border-red-200";
}

function formatDateLabel(raw: string): string {
  if (!raw) return "N/D";
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return raw;
  return d.toLocaleString();
}

export default function ReportesPage() {
  const { clienteId } = useAuditContext();
  const { data, isLoading, error } = useDashboard(clienteId);

  const [reportMsg, setReportMsg] = useState<string>("");
  const [generatingPdf, setGeneratingPdf] = useState<boolean>(false);
  const [memoGenerating, setMemoGenerating] = useState<boolean>(false);
  const [historyLoading, setHistoryLoading] = useState<boolean>(true);
  const [historyError, setHistoryError] = useState<string>("");
  const [history, setHistory] = useState<ReportHistoryPayload | null>(null);
  const [lastMemo, setLastMemo] = useState<string>("");

  async function refreshHistory(): Promise<void> {
    setHistoryLoading(true);
    setHistoryError("");
    try {
      const [hist, memo] = await Promise.all([getReportHistory(clienteId), getExecutiveMemo(clienteId)]);
      setHistory(hist);
      setLastMemo(memo.memo || "");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "No se pudo cargar el centro operativo de reportes.";
      setHistoryError(msg);
      setHistory(null);
    } finally {
      setHistoryLoading(false);
    }
  }

  useEffect(() => {
    void refreshHistory();
  }, [clienteId]);

  const gateMap = useMemo(() => {
    const map = new Map<string, { title: string; status: string; detail: string }>();
    for (const gate of history?.gates ?? []) {
      map.set(gate.code, { title: gate.title, status: gate.status, detail: gate.detail });
    }
    return map;
  }, [history]);

  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorMessage message={error} />;
  if (!data) return <ErrorMessage message="No hay datos para generar reportes." />;

  async function handleGeneratePdf(finalMode: boolean): Promise<void> {
    setGeneratingPdf(true);
    setReportMsg("");
    try {
      if (finalMode && gateMap.get("REPORT")?.status !== "ok") {
        throw new Error("No se puede emitir informe final: Gate REPORT en estado bloqueado.");
      }
      const meta = await generateExecutivePdf(clienteId);
      setReportMsg(
        finalMode
          ? `Informe final generado: ${meta.report_name} (${(meta.size_bytes / 1024).toFixed(1)} KB)`
          : `Borrador interno generado: ${meta.report_name} (${(meta.size_bytes / 1024).toFixed(1)} KB)`,
      );
      await refreshHistory();
    } catch (err) {
      setReportMsg(err instanceof Error ? err.message : "No se pudo generar el PDF.");
    } finally {
      setGeneratingPdf(false);
    }
  }

  async function handleGenerateMemo(): Promise<void> {
    setMemoGenerating(true);
    setReportMsg("");
    try {
      const memo = await generateExecutiveMemo(clienteId);
      setLastMemo(memo.memo);
      setReportMsg("Memo ejecutivo generado y persistido en hallazgos.");
      await refreshHistory();
    } catch (err) {
      setReportMsg(err instanceof Error ? err.message : "No se pudo generar el memo.");
    } finally {
      setMemoGenerating(false);
    }
  }

  async function handleDownloadLatest(): Promise<void> {
    setGeneratingPdf(true);
    setReportMsg("");
    try {
      const { blob, filename } = await downloadExecutivePdf(clienteId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(url);
      setReportMsg(`PDF descargado: ${filename}`);
    } catch (err) {
      setReportMsg(err instanceof Error ? err.message : "No se pudo abrir el PDF.");
    } finally {
      setGeneratingPdf(false);
    }
  }

  async function handleDownloadFromHistory(path: string, filename: string): Promise<void> {
    setReportMsg("");
    try {
      const { blob } = await downloadExecutivePdfByPath(clienteId, path, filename);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(url);
      setReportMsg(`Archivo descargado: ${filename}`);
    } catch (err) {
      setReportMsg(err instanceof Error ? err.message : "No se pudo descargar el archivo de historial.");
    }
  }

  return (
    <div className="pt-4 pb-10 space-y-8 max-w-[1500px]">
      <section className="rounded-editorial p-7 shadow-editorial text-white border border-[#041627]/20 bg-gradient-to-br from-[#041627] to-[#1a2b3c]">
        <p className="text-xs uppercase tracking-[0.2em] text-[#a5eff0] font-body">Centro Operativo de Reportes</p>
        <h1 className="font-headline text-5xl text-white mt-2">Emision y Trazabilidad</h1>
        <p className="font-body text-slate-200 mt-3 leading-relaxed text-base">
          Cliente: <span className="font-semibold text-white">{data.nombre_cliente}</span> ·
          Periodo: <span className="font-semibold text-white"> {data.periodo || "Actual"}</span>
        </p>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <article className="sovereign-card lg:col-span-2">
          <h3 className="font-headline text-2xl text-[#041627] mb-4">Quality Gates de Emision</h3>
          {historyLoading ? <p className="text-sm text-slate-500">Cargando estado de gates...</p> : null}
          {historyError ? <p className="text-sm text-red-700">{historyError}</p> : null}
          {!historyLoading && !historyError ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {(history?.gates ?? []).map((gate) => (
                <div key={gate.code} className={`rounded-xl border p-3 ${gateTone(gate.status)}`}>
                  <p className="text-[10px] uppercase tracking-[0.12em] font-bold">{gate.code}</p>
                  <p className="text-sm font-semibold mt-1">{gate.title}</p>
                  <p className="text-xs mt-2">{gate.detail}</p>
                </div>
              ))}
            </div>
          ) : null}
          <div className="mt-4 p-3 rounded-xl bg-[#f8fafc] border border-black/10 text-sm text-slate-700">
            Cobertura por afirmaciones: <b>{history?.coverage_summary.coverage_pct ?? 0}%</b>
            {" "}({history?.coverage_summary.covered_assertions ?? 0}/{history?.coverage_summary.total_assertions ?? 0})
          </div>
        </article>

        <article className="sovereign-card">
          <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">Materialidad</p>
          <h3 className="font-headline text-2xl text-[#041627] mt-2">{formatMoney(data.materialidad_global)}</h3>
          <p className="text-sm text-slate-600 mt-2">Base tecnica para evaluacion de desviaciones.</p>
          <div className="mt-4 space-y-2 text-sm">
            <p>Riesgo global: <b>{data.riesgo_global}</b></p>
            <p>Top area: <b>{data.top_areas?.[0]?.nombre ?? "N/D"}</b></p>
          </div>
        </article>
      </section>

      <section className="grid grid-cols-1 xl:grid-cols-4 gap-4">
        <button
          type="button"
          onClick={() => void handleGeneratePdf(false)}
          disabled={generatingPdf}
          className="px-4 py-3 rounded-xl text-xs font-bold uppercase tracking-[0.12em] border border-[#041627]/20 text-[#041627] disabled:opacity-60 bg-white"
        >
          {generatingPdf ? "Procesando..." : "Generar borrador interno"}
        </button>
        <button
          type="button"
          onClick={() => void handleGeneratePdf(true)}
          disabled={generatingPdf || gateMap.get("REPORT")?.status !== "ok"}
          className="px-4 py-3 rounded-xl text-xs font-bold uppercase tracking-[0.12em] bg-[#041627] text-white disabled:opacity-60"
        >
          {generatingPdf ? "Procesando..." : "Emitir informe final"}
        </button>
        <button
          type="button"
          onClick={() => void handleDownloadLatest()}
          disabled={generatingPdf}
          className="px-4 py-3 rounded-xl text-xs font-bold uppercase tracking-[0.12em] border border-[#041627]/20 text-[#041627] disabled:opacity-60 bg-white"
        >
          Descargar ultimo PDF
        </button>
        <button
          type="button"
          onClick={() => void handleGenerateMemo()}
          disabled={memoGenerating}
          className="px-4 py-3 rounded-xl text-xs font-bold uppercase tracking-[0.12em] border border-[#041627]/20 text-[#041627] disabled:opacity-60 bg-white"
        >
          {memoGenerating ? "Generando memo..." : "Generar memo ejecutivo"}
        </button>
      </section>

      {reportMsg ? <section className="sovereign-card text-sm text-slate-700">{reportMsg}</section> : null}

      {lastMemo ? (
        <section className="sovereign-card">
          <h3 className="font-headline text-2xl text-[#041627] mb-2">Memo Ejecutivo Vigente</h3>
          <p className="text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">{lastMemo}</p>
        </section>
      ) : null}

      <section className="sovereign-card">
        <h2 className="font-headline text-3xl text-[#041627] mb-4">Historial de artefactos</h2>
        {historyLoading ? <p className="text-sm text-slate-500">Cargando historial...</p> : null}
        {!historyLoading && (history?.items?.length ?? 0) === 0 ? (
          <p className="text-sm text-slate-500">Aun no hay artefactos generados para este cliente.</p>
        ) : null}
        {!historyLoading && (history?.items?.length ?? 0) > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="border-b border-black/10 text-[10px] uppercase tracking-[0.12em] text-slate-500">
                  <th className="py-2 pr-4">Tipo</th>
                  <th className="py-2 pr-4">Nombre</th>
                  <th className="py-2 pr-4">Fecha</th>
                  <th className="py-2 pr-4">Estado</th>
                  <th className="py-2 pr-4">Hash</th>
                  <th className="py-2">Accion</th>
                </tr>
              </thead>
              <tbody>
                {(history?.items ?? []).slice().reverse().map((item, idx) => (
                  <tr key={`${item.report_name}-${idx}`} className="border-b border-black/5">
                    <td className="py-3 pr-4">{item.kind}</td>
                    <td className="py-3 pr-4">{item.report_name}</td>
                    <td className="py-3 pr-4">{formatDateLabel(item.generated_at)}</td>
                    <td className="py-3 pr-4">{item.status}</td>
                    <td className="py-3 pr-4 text-[11px] text-slate-500">{item.file_hash.slice(0, 12)}...</td>
                    <td className="py-3">
                      {item.kind === "executive_pdf" && item.path ? (
                        <button
                          type="button"
                          className="px-3 py-1 rounded-lg border border-black/10 text-xs"
                          onClick={() => void handleDownloadFromHistory(item.path, item.report_name)}
                        >
                          Descargar
                        </button>
                      ) : (
                        <span className="text-xs text-slate-400">N/A</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      <section className="sovereign-card">
        <h2 className="font-headline text-3xl text-[#041627] mb-4">Acciones</h2>
        <div className="flex flex-wrap gap-3">
          <Link href={`/papeles-trabajo/${clienteId}`} className="px-4 py-2 rounded-xl bg-[#f1f4f6] text-sm text-slate-700 border border-black/10">
            Revisar Papeles de Trabajo
          </Link>
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

