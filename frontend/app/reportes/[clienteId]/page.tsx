"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import ContextualHelp from "../../../components/help/ContextualHelp";
import {
  downloadExecutivePdfByPath,
  getDocumentAllowedActions,
  getDocumentEvidenceGate,
  getDocumentQualityCheck,
  getDocumentSectionEvidence,
  getDocumentSections,
  getDocumentVersions,
  issueDocumentFinal,
  linkDocumentSectionEvidence,
  generateExecutiveMemo,
  generateExecutivePdf,
  getExecutiveMemo,
  getReportHistory,
  getReportStatus,
  transitionDocumentState,
  type DocumentAllowedActions,
  type DocumentEvidenceGate,
  type DocumentQualityCheck,
  type DocumentSectionEvidencePayload,
  type DocumentSectionsPayload,
  type DocumentVersion,
  type ReportHistoryPayload,
  type ReportStatusPayload,
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

const DOCUMENT_TYPES = ["carta_control_interno", "niif_pymes_borrador"] as const;
type DocumentType = (typeof DOCUMENT_TYPES)[number];

function nextStateLabel(state: string): string {
  if (state === "reviewed") return "Marcar reviewed";
  if (state === "approved") return "Aprobar";
  if (state === "issued") return "Emitir";
  return state;
}

function summarizeBlockingReason(reason: string): string {
  if (reason === "missing_required_support") return "Falta evidencia requerida";
  return reason || "Bloqueo de evidencia";
}

function evidenceCtaLabel(reason: string): string {
  if (reason === "missing_required_support") return "Completar evidencia";
  return "Ver detalle";
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
  const [statusPayload, setStatusPayload] = useState<ReportStatusPayload | null>(null);
  const [lastMemo, setLastMemo] = useState<string>("");
  const [docVersions, setDocVersions] = useState<Record<string, { current: DocumentVersion | null; versions: DocumentVersion[] }>>({});
  const [docActions, setDocActions] = useState<Record<string, DocumentAllowedActions | null>>({});
  const [docQuality, setDocQuality] = useState<Record<string, DocumentQualityCheck | null>>({});
  const [docEvidenceGate, setDocEvidenceGate] = useState<Record<string, DocumentEvidenceGate | null>>({});
  const [docSections, setDocSections] = useState<Record<string, DocumentSectionsPayload | null>>({});
  const [selectedSection, setSelectedSection] = useState<Record<string, DocumentSectionEvidencePayload | null>>({});
  const [focusedSectionId, setFocusedSectionId] = useState<Record<string, string | null>>({});
  const [docBusy, setDocBusy] = useState<Record<string, boolean>>({});

  async function refreshHistory(): Promise<void> {
    setHistoryLoading(true);
    setHistoryError("");
    try {
      const [hist, memo] = await Promise.all([getReportHistory(clienteId), getExecutiveMemo(clienteId)]);
      const status = await getReportStatus(clienteId);
      const versionPromises = DOCUMENT_TYPES.map((documentType) => getDocumentVersions(clienteId, documentType));
      const actionsPromises = DOCUMENT_TYPES.map((documentType) => getDocumentAllowedActions(clienteId, documentType));
      const qualityPromises = DOCUMENT_TYPES.map((documentType) =>
        getDocumentQualityCheck(clienteId, documentType).catch(() => null),
      );
      const evidenceGatePromises = DOCUMENT_TYPES.map((documentType) =>
        getDocumentEvidenceGate(clienteId, documentType).catch(() => null),
      );
      const sectionsPromises = DOCUMENT_TYPES.map((documentType) =>
        getDocumentSections(clienteId, documentType).catch(() => null),
      );
      const [versionResults, actionResults, qualityResults, evidenceGateResults, sectionsResults] = await Promise.all([
        Promise.all(versionPromises),
        Promise.all(actionsPromises),
        Promise.all(qualityPromises),
        Promise.all(evidenceGatePromises),
        Promise.all(sectionsPromises),
      ]);
      const nextVersions: Record<string, { current: DocumentVersion | null; versions: DocumentVersion[] }> = {};
      const nextActions: Record<string, DocumentAllowedActions | null> = {};
      const nextQuality: Record<string, DocumentQualityCheck | null> = {};
      const nextEvidenceGate: Record<string, DocumentEvidenceGate | null> = {};
      const nextSections: Record<string, DocumentSectionsPayload | null> = {};
      DOCUMENT_TYPES.forEach((documentType, idx) => {
        nextVersions[documentType] = versionResults[idx];
        nextActions[documentType] = actionResults[idx];
        nextQuality[documentType] = qualityResults[idx];
        nextEvidenceGate[documentType] = evidenceGateResults[idx];
        nextSections[documentType] = sectionsResults[idx];
      });
      setHistory(hist);
      setStatusPayload(status);
      setLastMemo(memo.memo || "");
      setDocVersions(nextVersions);
      setDocActions(nextActions);
      setDocQuality(nextQuality);
      setDocEvidenceGate(nextEvidenceGate);
      setDocSections(nextSections);
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

  const latestPdf = useMemo(() => {
    const items = (history?.items ?? []).filter((item) => item.kind === "executive_pdf" && item.path);
    if (items.length === 0) return null;
    return items.slice().sort((a, b) => new Date(b.generated_at).getTime() - new Date(a.generated_at).getTime())[0];
  }, [history]);
  const tbStage = (data?.tb_stage || "sin_saldos").toLowerCase();
  const tbStageLabel =
    tbStage === "final"
      ? "Corte Final"
      : tbStage === "preliminar"
        ? "Corte Preliminar"
        : tbStage === "inicial"
          ? "Corte Inicial"
          : "Sin saldos";

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
      const meta = await generateExecutivePdf(clienteId, finalMode ? "final" : "draft");
      setReportMsg(
        finalMode
          ? `Informe final generado: ${meta.report_name} (${(meta.size_bytes / 1024).toFixed(1)} KB)`
          : `Borrador interno generado: ${meta.report_name} (${(meta.size_bytes / 1024).toFixed(1)} KB)`,
      );
      await refreshHistory();
    } catch (err) {
      const base = err instanceof Error ? err.message : "No se pudo generar el PDF.";
      if (finalMode && gateMap.get("REPORT")?.status !== "ok") {
        setReportMsg(`${base} Revisa gates y cobertura en esta misma vista antes de emitir final.`);
        return;
      }
      setReportMsg(base);
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
      if (!latestPdf) {
        throw new Error("No existe PDF generado todavia. Primero genera borrador interno.");
      }
      const { blob, filename } = await downloadExecutivePdfByPath(clienteId, latestPdf.path, latestPdf.report_name);
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

  async function handleTransition(documentType: DocumentType, targetState: "reviewed" | "approved"): Promise<void> {
    setDocBusy((prev) => ({ ...prev, [documentType]: true }));
    setReportMsg("");
    try {
      await transitionDocumentState(clienteId, documentType, {
        target_state: targetState,
        reason: `Cambio via UI: ${targetState}`,
      });
      setReportMsg(`Estado actualizado en ${documentType}: ${targetState}`);
      await refreshHistory();
    } catch (err) {
      setReportMsg(err instanceof Error ? err.message : "No se pudo cambiar el estado documental.");
    } finally {
      setDocBusy((prev) => ({ ...prev, [documentType]: false }));
    }
  }

  async function handleIssue(documentType: DocumentType): Promise<void> {
    setDocBusy((prev) => ({ ...prev, [documentType]: true }));
    setReportMsg("");
    try {
      const issued = await issueDocumentFinal(clienteId, documentType, { reason: "Emision final desde UI" });
      setReportMsg(`Documento emitido. PDF final: ${issued.data.pdf_artifact_path}`);
      await refreshHistory();
    } catch (err) {
      setReportMsg(err instanceof Error ? err.message : "No se pudo emitir el documento.");
    } finally {
      setDocBusy((prev) => ({ ...prev, [documentType]: false }));
    }
  }

  async function handleDownloadArtifact(documentType: string, artifactPath: string, filename: string): Promise<void> {
    await handleDownloadFromHistory(artifactPath, filename || `${documentType}.docx`);
  }

  async function handleOpenSection(documentType: DocumentType, sectionId: string): Promise<void> {
    setDocBusy((prev) => ({ ...prev, [documentType]: true }));
    try {
      const detail = await getDocumentSectionEvidence(clienteId, documentType, sectionId);
      setSelectedSection((prev) => ({ ...prev, [documentType]: detail }));
      setFocusedSectionId((prev) => ({ ...prev, [documentType]: sectionId }));
      if (typeof window !== "undefined") {
        window.setTimeout(() => {
          const target = document.getElementById(`section-detail-${documentType}`);
          target?.scrollIntoView({ behavior: "smooth", block: "center" });
        }, 80);
      }
    } catch (err) {
      setReportMsg(err instanceof Error ? err.message : "No se pudo cargar la sección.");
    } finally {
      setDocBusy((prev) => ({ ...prev, [documentType]: false }));
    }
  }

  async function handleQuickLinkEvidence(documentType: DocumentType, sectionId: string): Promise<void> {
    const sourceType = window.prompt("source_type (trial_balance/workpaper/hallazgo/management_response/adjustment/supporting_document/cedula):");
    if (!sourceType) return;
    const sourceId = window.prompt("source_id:");
    if (!sourceId) return;
    const label = window.prompt("label:");
    if (!label) return;
    const reference = window.prompt("reference (opcional):") ?? "";
    setDocBusy((prev) => ({ ...prev, [documentType]: true }));
    try {
      await linkDocumentSectionEvidence(clienteId, documentType, sectionId, {
        source_type: sourceType,
        source_id: sourceId,
        label,
        reference,
      });
      setReportMsg(`Evidencia vinculada en ${documentType} / ${sectionId}`);
      await refreshHistory();
      await handleOpenSection(documentType, sectionId);
    } catch (err) {
      setReportMsg(err instanceof Error ? err.message : "No se pudo vincular evidencia.");
    } finally {
      setDocBusy((prev) => ({ ...prev, [documentType]: false }));
    }
  }

  return (
    <div className="pt-4 pb-10 space-y-8 max-w-[1500px]">
      <section className="rounded-editorial p-7 shadow-editorial text-white border border-[#041627]/20 bg-gradient-to-br from-[#041627] to-[#1a2b3c]">
        <p className="text-xs uppercase tracking-[0.2em] text-[#a5eff0] font-body">Centro Operativo de Reportes</p>
        <h1 data-tour="reportes-title" className="font-headline text-5xl text-white mt-2">Emision y Trazabilidad</h1>
        <p className="font-body text-slate-200 mt-3 leading-relaxed text-base">
          Cliente: <span className="font-semibold text-white">{data.nombre_cliente}</span> ·
          Periodo: <span className="font-semibold text-white"> {data.periodo || "Actual"}</span>
          {" "}· TB: <span className="font-semibold text-white">{tbStageLabel}</span>
        </p>
      </section>

      <ContextualHelp
        title="Ayuda del modulo Reportes"
        items={[
          {
            label: "Gates de emision",
            description:
              "Verifica PLAN, EXEC y REPORT antes de emitir informe final.",
          },
          {
            label: "Acciones principales",
            description:
              "Genera borrador interno primero; emite final solo cuando los bloqueos esten resueltos.",
          },
          {
            label: "Gobierno documental",
            description:
              "Controla versiones, cambios y artefactos para trazabilidad de calidad.",
          },
        ]}
      />

      <section data-tour="reportes-gates" className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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
          {(statusPayload?.missing_sections?.length ?? 0) > 0 ? (
            <div className="mt-3 p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800">
              Faltantes para emision final:
              <ul className="mt-2 list-disc list-inside">
                {statusPayload?.missing_sections?.slice(0, 5).map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {gateMap.get("REPORT")?.status !== "ok" ? (
            <div className="mt-3 p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-800">
              Emision final bloqueada: completa tareas requeridas en Papeles de Trabajo y registra conclusion tecnica en hallazgos.
            </div>
          ) : null}
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

      <section data-tour="reportes-actions" className="grid grid-cols-1 xl:grid-cols-4 gap-4">
        <button
          type="button"
          onClick={() => void handleGeneratePdf(false)}
          disabled={generatingPdf || (statusPayload ? !statusPayload.can_emit_draft : false)}
          className="px-4 py-3 rounded-xl text-xs font-bold uppercase tracking-[0.12em] border border-[#041627]/20 text-[#041627] disabled:opacity-60 bg-white"
        >
          {generatingPdf ? "Procesando..." : "Generar borrador interno"}
        </button>
        <button
          type="button"
          onClick={() => void handleGeneratePdf(true)}
          disabled={generatingPdf || (statusPayload ? !statusPayload.can_emit_final : gateMap.get("REPORT")?.status !== "ok")}
          className="px-4 py-3 rounded-xl text-xs font-bold uppercase tracking-[0.12em] bg-[#041627] text-white disabled:opacity-60"
        >
          {generatingPdf ? "Procesando..." : "Emitir informe final"}
        </button>
        <button
          type="button"
          onClick={() => void handleDownloadLatest()}
          disabled={generatingPdf || !latestPdf}
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

      <section data-tour="reportes-history" className="sovereign-card">
        <h2 className="font-headline text-3xl text-[#041627] mb-4">Gobierno Documental</h2>
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {DOCUMENT_TYPES.map((documentType) => {
            const pack = docVersions[documentType];
            const current = pack?.current ?? null;
            const actions = docActions[documentType];
            const quality = docQuality[documentType];
            const evidenceGate = docEvidenceGate[documentType];
            const allowedNext = actions?.allowed_next_states ?? [];
            const diff = current?.diff_from_previous;
            const artifacts = current?.artifacts ?? [];
            const sectionMap = new Map((docSections[documentType]?.sections ?? []).map((s) => [s.section_id, s]));
            const activeSectionId = focusedSectionId[documentType];
            return (
              <article key={documentType} className="rounded-xl border border-black/10 p-4 bg-white">
                <p className="text-[10px] uppercase tracking-[0.12em] text-slate-500">{documentType}</p>
                <h3 className="font-semibold text-[#041627] mt-2">
                  Versión actual: {current?.document_version ?? "N/D"} · Estado: {current?.state ?? "sin_version"}
                </h3>
                <p className="text-xs text-slate-600 mt-1">
                  {current?.summary ?? "Sin resumen de regeneración."}
                </p>

                <div className="mt-3 text-xs text-slate-700 space-y-1">
                  <p>Rol actual: <b>{actions?.role ?? "N/D"}</b></p>
                  <p>Acciones permitidas: {(actions?.permissions ?? []).join(", ") || "Ninguna"}</p>
                </div>

                <div className="mt-3 space-y-1 text-xs">
                  <p className="font-semibold text-[#041627]">Diff vs versión anterior</p>
                  <p>Secciones cambiadas: {diff?.changed_sections?.length ?? 0}</p>
                  <p>Input cambiado: {diff?.input_changed ? "Sí" : "No"}</p>
                  <p>Plantilla cambiada: {diff?.template_changed ? "Sí" : "No"}</p>
                  <p>Prompt/modelo cambiado: {diff?.prompt_changed ? "Sí" : "No"}</p>
                </div>

                <div className="mt-3 space-y-1 text-xs">
                  <p className="font-semibold text-[#041627]">Checklist previo a aprobación</p>
                  <p>
                    Score: <b>{quality?.quality_check?.score ?? 0}</b> ·
                    Semáforo: <b>{quality?.quality_check?.semaphore ?? "red"}</b>
                  </p>
                  {(quality?.quality_check?.checks ?? []).map((check) => (
                    <p key={check.code} className={check.status === "ok" ? "text-emerald-700" : "text-rose-700"}>
                      {check.code}: {check.detail}
                    </p>
                  ))}
                  <p className={quality?.quality_check?.can_approve ? "text-emerald-700" : "text-rose-700"}>
                    can_approve: {quality?.quality_check?.can_approve ? "true" : "false"}
                  </p>
                </div>

                <div className="mt-3 space-y-1 text-xs">
                  <p className="font-semibold text-[#041627]">Evidence Gate</p>
                  <p>
                    Cobertura: <b>{evidenceGate?.coverage_percent ?? 0}%</b> · Mínimo: <b>{evidenceGate?.minimum_required ?? 0}%</b>
                  </p>
                  <p className={evidenceGate?.can_approve ? "text-emerald-700" : "text-rose-700"}>
                    can_approve: {evidenceGate?.can_approve ? "true" : "false"}
                  </p>
                  <p className={evidenceGate?.can_issue ? "text-emerald-700" : "text-rose-700"}>
                    can_issue: {evidenceGate?.can_issue ? "true" : "false"}
                  </p>
                  {(evidenceGate?.approve_blocking_reasons ?? []).map((reason, idx) => (
                    <p key={`${documentType}-approve-reason-${idx}`} className="text-rose-700">
                      No se puede aprobar: {reason}
                    </p>
                  ))}
                  {(evidenceGate?.issue_blocking_reasons ?? []).map((reason, idx) => (
                    <p key={`${documentType}-issue-reason-${idx}`} className="text-rose-700">
                      No se puede emitir: {reason}
                    </p>
                  ))}
                  {(evidenceGate?.blocking_sections ?? []).length ? (
                    <div className="space-y-2">
                      {(evidenceGate?.blocking_sections ?? []).map((blocked) => {
                        const section = sectionMap.get(blocked.section_id);
                        const ratio = `${section?.linked_support_count ?? 0}/${section?.required_support_count ?? 1}`;
                        return (
                          <div key={`${documentType}-blocked-${blocked.section_id}`} className="rounded-lg border border-rose-200 bg-rose-50 p-2">
                            <p className="text-rose-800 font-semibold">
                              {blocked.section_title || blocked.section_id}
                            </p>
                            <p className="text-rose-700">
                              {summarizeBlockingReason(blocked.reason)} · Cobertura {ratio}
                            </p>
                            <button
                              type="button"
                              className="mt-1 px-2 py-1 rounded-lg border border-rose-300 bg-white text-rose-800"
                              onClick={() => void handleOpenSection(documentType, blocked.section_id)}
                            >
                              {evidenceCtaLabel(blocked.reason)}
                            </button>
                          </div>
                        );
                      })}
                    </div>
                  ) : null}
                </div>

                <div className="mt-3 flex flex-wrap gap-2">
                  {allowedNext.map((nextState) => (
                    nextState === "issued" ? (
                      <button
                        key={`${documentType}-${nextState}`}
                        type="button"
                        disabled={Boolean(docBusy[documentType])}
                        onClick={() => void handleIssue(documentType)}
                        className="px-3 py-1 rounded-lg border border-black/10 text-xs bg-[#041627] text-white disabled:opacity-60"
                      >
                        Emitir y generar PDF final
                      </button>
                    ) : (
                    <button
                      key={`${documentType}-${nextState}`}
                      type="button"
                      disabled={Boolean(docBusy[documentType])}
                      onClick={() => void handleTransition(documentType, nextState as "reviewed" | "approved")}
                      className="px-3 py-1 rounded-lg border border-black/10 text-xs bg-[#f8fafc] disabled:opacity-60"
                    >
                      {nextStateLabel(nextState)}
                    </button>
                    )
                  ))}
                </div>

                <div className="mt-3 text-xs">
                  <p className="font-semibold text-[#041627]">Cobertura de evidencia por sección</p>
                  <p>
                    Soportadas: <b>{docSections[documentType]?.coverage.supported_sections ?? 0}</b> /
                    {" "}<b>{docSections[documentType]?.coverage.total_sections ?? 0}</b> ·
                    Faltantes críticas: <b>{docSections[documentType]?.coverage.missing_required ?? 0}</b> ·
                    Cobertura: <b>{docSections[documentType]?.coverage.coverage_percent ?? 0}%</b>
                  </p>
                  <div className="mt-2 space-y-1 max-h-40 overflow-auto">
                    {(docSections[documentType]?.sections ?? []).slice(0, 10).map((section) => (
                      <div
                        key={`${documentType}-${section.section_id}`}
                        className={`flex items-center justify-between gap-2 rounded px-1 ${
                          activeSectionId === section.section_id ? "bg-amber-50 border border-amber-200" : ""
                        }`}
                      >
                        <button
                          type="button"
                          className="text-left underline text-slate-700"
                          onClick={() => void handleOpenSection(documentType, section.section_id)}
                        >
                          {section.section_title}
                        </button>
                        <span
                          className={
                            section.status === "supported"
                              ? "text-emerald-700"
                              : section.status === "missing_required_support"
                                ? "text-rose-700"
                                : "text-amber-700"
                          }
                        >
                          {section.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {selectedSection[documentType] ? (
                  <div id={`section-detail-${documentType}`} className="mt-3 text-xs rounded-lg border border-black/10 p-3 bg-[#f8fafc]">
                    <p className="font-semibold text-[#041627]">Detalle sección seleccionada</p>
                    <p className="mt-1">
                      <b>{selectedSection[documentType]?.section.section_title}</b>
                    </p>
                    <p className="mt-1 text-slate-700">
                      {summarizeBlockingReason(selectedSection[documentType]?.section.blocking_reason ?? "")}
                      {" "}· Cobertura {selectedSection[documentType]?.section.linked_support_count ?? 0}/
                      {selectedSection[documentType]?.section.required_support_count ?? 1}
                    </p>
                    <p className="mt-1 text-slate-700">
                      Section content:
                    </p>
                    <pre className="whitespace-pre-wrap text-[11px] bg-white border border-black/10 rounded p-2 max-h-40 overflow-auto">
                      {JSON.stringify(selectedSection[documentType]?.section_content, null, 2)}
                    </pre>
                    <p className="mt-2 font-semibold text-[#041627]">Evidencias vinculadas</p>
                    {(selectedSection[documentType]?.section.sources ?? []).length === 0 ? (
                      <p className="text-slate-500">Sin evidencias vinculadas.</p>
                    ) : (
                      <ul className="list-disc list-inside text-slate-700">
                        {(selectedSection[documentType]?.section.sources ?? []).map((src, idx) => (
                          <li key={`${documentType}-src-${idx}`}>
                            {src.source_type} · {src.source_id} · {src.label}
                          </li>
                        ))}
                      </ul>
                    )}
                    <button
                      type="button"
                      className="mt-2 px-3 py-1 rounded-lg border border-black/10"
                      onClick={() =>
                        void handleQuickLinkEvidence(documentType, selectedSection[documentType]?.section.section_id ?? "")
                      }
                    >
                      {evidenceCtaLabel(selectedSection[documentType]?.section.blocking_reason ?? "")}
                    </button>
                  </div>
                ) : null}

                <div className="mt-3 text-xs">
                  <p className="font-semibold text-[#041627]">Artefactos descargables</p>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {artifacts.map((artifact, idx) => (
                      <button
                        key={`${artifact.artifact_type}-${idx}`}
                        type="button"
                        className="px-3 py-1 rounded-lg border border-black/10"
                        onClick={() =>
                          void handleDownloadArtifact(
                            documentType,
                            artifact.artifact_path,
                            `${documentType}_v${current?.document_version ?? "x"}.${artifact.artifact_type === "docx" ? "docx" : "md"}`,
                          )
                        }
                      >
                        {artifact.artifact_type.toUpperCase()}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="mt-3 text-xs">
                  <p className="font-semibold text-[#041627]">Historial de transiciones</p>
                  {(current?.state_history ?? []).length === 0 ? (
                    <p className="text-slate-500">Sin transiciones registradas.</p>
                  ) : (
                    <ul className="mt-1 list-disc list-inside text-slate-700">
                      {(current?.state_history ?? []).slice(-5).map((h, idx) => (
                        <li key={`${documentType}-tr-${idx}`}>
                          {h.from_state} → {h.to_state} · {h.changed_role} · {formatDateLabel(h.changed_at ?? "")}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      </section>

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

