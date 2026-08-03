"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";

import { hasSessionState } from "../../../lib/auth-session";
import {
  analyzeEntityProfile,
  decideEntityProfileHypothesis,
  confirmEntityProfile,
  getEntityProfileDraft,
  saveEntityProfileAnswers,
  updateEntityProfilePending,
  type EntityProfileDraft,
  type EntityProfileAnalysis,
  type EntityProfileHypothesis,
} from "../../../lib/api/entity-profile";

type Params = { clienteId?: string | string[] };

const SOURCE_STATUS: Record<string, string> = {
  available: "Disponible",
  available_with_warnings: "Disponible con advertencias",
  missing: "Pendiente",
  optional_missing: "No cargado (opcional)",
  processing_failed: "No se pudo procesar",
};

const PENDING_STATUS_LABELS = {
  pending: "Pendiente",
  requested: "Solicitado al cliente",
  received: "Recibido",
  confirmed: "Confirmado",
  not_applicable: "No aplicable",
} as const;

export default function EntityProfilePage() {
  const params = useParams<Params>();
  const router = useRouter();
  const clienteId = useMemo(
    () => (Array.isArray(params?.clienteId) ? params.clienteId[0] ?? "" : params?.clienteId ?? ""),
    [params],
  );
  const [draft, setDraft] = useState<EntityProfileDraft | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [analysis, setAnalysis] = useState<EntityProfileAnalysis | undefined>();
  const [analyzing, setAnalyzing] = useState(false);
  const [decidingId, setDecidingId] = useState("");
  const [edits, setEdits] = useState<Record<string, { title: string; reason: string }>>({});
  const [roundStatus, setRoundStatus] = useState<"idle" | "processing" | "new_round" | "complete">("idle");
  const [pendingSavingId, setPendingSavingId] = useState("");
  const [pendingEdits, setPendingEdits] = useState<Record<string, { status: keyof typeof PENDING_STATUS_LABELS; answer: string }>>({});
  const [questionIndex, setQuestionIndex] = useState(0);
  const [reviewMode, setReviewMode] = useState(false);

  useEffect(() => {
    if (!hasSessionState()) {
      router.replace("/");
      return;
    }
    if (!clienteId) return;
    let active = true;
    getEntityProfileDraft(clienteId)
      .then((value) => {
        if (!active) return;
        setDraft(value);
        setAnswers(value.answers ?? {});
        setAnalysis(value.analysis);
        setReviewMode(value.status === "confirmed" && Boolean(value.analysis));
      })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof Error ? reason.message : "No se pudo generar el perfil.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [clienteId, router]);

  useEffect(() => {
    setQuestionIndex(0);
  }, [draft?.active_round]);

  async function saveAnswers(): Promise<EntityProfileDraft | null> {
    if (!clienteId) return null;
    setSaving(true);
    setRoundStatus("processing");
    setError("");
    try {
      const [updated] = await Promise.all([
        saveEntityProfileAnswers(clienteId, answers),
        new Promise((resolve) => window.setTimeout(resolve, 550)),
      ]);
      setDraft(updated);
      setAnswers(updated.answers ?? {});
      setRoundStatus(updated.active_round > (draft?.active_round ?? 1) ? "new_round" : updated.unanswered_critical.length === 0 ? "complete" : "idle");
      return updated;
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudieron guardar las respuestas.");
      setRoundStatus("idle");
      return null;
    } finally {
      setSaving(false);
    }
  }

  async function savePendingItem(questionId: string): Promise<void> {
    const item = draft?.pending_items.find((candidate) => candidate.question_id === questionId);
    if (!item) return;
    const edit = pendingEdits[questionId] ?? { status: item.status, answer: item.answer };
    setPendingSavingId(questionId);
    setError("");
    try {
      const updated = await updateEntityProfilePending(clienteId, questionId, edit);
      setDraft(updated);
      setAnswers(updated.answers ?? {});
      setPendingEdits((current) => {
        const next = { ...current };
        delete next[questionId];
        return next;
      });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudo actualizar el pendiente.");
    } finally {
      setPendingSavingId("");
    }
  }

  async function confirmAndContinue(): Promise<void> {
    const updated = await saveAnswers();
    if (!updated || updated.unanswered_critical.length > 0) return;
    setSaving(true);
    try {
      const confirmed = await confirmEntityProfile(clienteId);
      setDraft(confirmed);
      router.push(`/socio-chat/${clienteId}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudo confirmar el perfil.");
    } finally {
      setSaving(false);
    }
  }

  async function runAnalysis(force = false): Promise<void> {
    if (!clienteId) return;
    setAnalyzing(true);
    setError("");
    try {
      const result = await analyzeEntityProfile(clienteId, force);
      setAnalysis(result);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudo analizar el contexto.");
    } finally {
      setAnalyzing(false);
    }
  }

  async function evaluateRound(): Promise<void> {
    const startingRound = draft?.active_round ?? 1;
    const updated = await saveAnswers();
    if (!updated) return;
    if (updated.active_round > startingRound || updated.unanswered_critical.length > 0) return;
    setRoundStatus("processing");
    setAnalyzing(true);
    try {
      const result = await analyzeEntityProfile(clienteId, Boolean(analysis));
      setAnalysis(result);
      setRoundStatus("complete");
      setReviewMode(true);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudo preparar el resultado del perfil.");
      setRoundStatus("complete");
    } finally {
      setAnalyzing(false);
    }
  }

  function Evidence({ item }: { item: EntityProfileHypothesis }) {
    const refs = item.evidence_refs ?? [];
    const confidence = Math.round(Math.max(0, Math.min(1, item.confidence ?? 0)) * 100);
    return (
      <div className="mt-3 flex flex-wrap gap-2 text-[11px]">
        <span className="rounded-full bg-slate-100 px-2.5 py-1 text-slate-600">Confianza IA: {confidence}%</span>
        {refs.length ? refs.map((ref) => <span key={ref} className="rounded-full bg-[#e3f4f4] px-2.5 py-1 text-[#155e63]">Evidencia: {ref}</span>) : <span className="rounded-full bg-amber-50 px-2.5 py-1 text-amber-800">Sin respaldo documental</span>}
      </div>
    );
  }

  async function decide(item: EntityProfileHypothesis, status: "pending" | "accepted" | "rejected" | "antecedent" | "current_hypothesis" | "discarded" | "pending_validation"): Promise<void> {
    if (!item.id) return;
    setDecidingId(item.id);
    setError("");
    const edit = edits[item.id];
    try {
      const updated = await decideEntityProfileHypothesis(clienteId, {
        hypothesis_id: item.id,
        status,
        edited_title: edit?.title ?? item.decision?.edited_title ?? "",
        edited_reason: edit?.reason ?? item.decision?.edited_reason ?? "",
      });
      setAnalysis(updated);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "No se pudo guardar la decisión.");
    } finally {
      setDecidingId("");
    }
  }

  function ReviewControls({ item }: { item: EntityProfileHypothesis }) {
    if (!item.id) return null;
    const status = item.decision?.status ?? "pending";
    const edit = edits[item.id] ?? {
      title: item.decision?.edited_title ?? "",
      reason: item.decision?.edited_reason ?? "",
    };
    return (
      <div className="mt-4 border-t border-black/10 pt-3">
        <div className="grid gap-2">
          <input value={edit.title} onChange={(event) => setEdits((current) => ({ ...current, [item.id!]: { ...edit, title: event.target.value } }))} className="rounded-lg border border-black/10 px-3 py-2 text-xs" placeholder="Título ajustado por el auditor (opcional)" />
          <textarea value={edit.reason} onChange={(event) => setEdits((current) => ({ ...current, [item.id!]: { ...edit, reason: event.target.value } }))} className="rounded-lg border border-black/10 px-3 py-2 text-xs" rows={2} placeholder="Criterio o justificación del auditor (opcional)" />
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <button type="button" disabled={decidingId === item.id} onClick={() => void decide(item, "antecedent")} className={`rounded-lg px-3 py-2 text-xs font-semibold ${status === "antecedent" ? "bg-blue-700 text-white" : "bg-blue-50 text-blue-800"}`}>Conservar antecedente</button>
          <button type="button" disabled={decidingId === item.id} onClick={() => void decide(item, "current_hypothesis")} className={`rounded-lg px-3 py-2 text-xs font-semibold ${status === "current_hypothesis" || status === "accepted" ? "bg-emerald-700 text-white" : "bg-emerald-50 text-emerald-800"}`}>Hipótesis actual</button>
          <button type="button" disabled={decidingId === item.id} onClick={() => void decide(item, "discarded")} className={`rounded-lg px-3 py-2 text-xs font-semibold ${status === "discarded" || status === "rejected" ? "bg-red-700 text-white" : "bg-red-50 text-red-800"}`}>Descartar</button>
          <button type="button" disabled={decidingId === item.id} onClick={() => void decide(item, "pending_validation")} className={`rounded-lg px-3 py-2 text-xs ${status === "pending_validation" || status === "pending" ? "bg-slate-700 text-white" : "bg-slate-100 text-slate-600"}`}>Pendiente</button>
          <span className="ml-auto text-[11px] text-slate-500">Decisión profesional del auditor</span>
        </div>
      </div>
    );
  }

  if (loading) {
    return <main className="min-h-screen bg-[#f4f7f8] p-8 text-slate-600">Analizando las fuentes y preparando el perfil…</main>;
  }
  if (!draft) {
    return <main className="min-h-screen bg-[#f4f7f8] p-8 text-red-700">{error || "Perfil no disponible."}</main>;
  }

  const activeRound = draft.active_round ?? 1;
  const currentQuestions = draft.questions.filter((question) => (question.round ?? 1) === activeRound);
  const previousQuestions = draft.questions.filter((question) => (question.round ?? 1) < activeRound);
  const pending = currentQuestions.filter((question) => !String(answers[question.id] ?? "").trim()).length;

  const activeQuestion = currentQuestions[Math.min(questionIndex, Math.max(0, currentQuestions.length - 1))];
  const answeredInRound = currentQuestions.filter((question) => String(answers[question.id] ?? "").trim()).length;
  const entityName = String(draft.facts.find((fact) => fact.key === "legal_name")?.value ?? draft.facts.find((fact) => fact.label.toLowerCase().includes("nombre"))?.value ?? "Cliente");
  const period = String(draft.facts.find((fact) => fact.key === "period")?.value ?? draft.facts.find((fact) => fact.label.toLowerCase().includes("periodo"))?.value ?? "Actual");
  const framework = String(draft.facts.find((fact) => fact.key === "accounting_framework")?.value ?? draft.facts.find((fact) => fact.label.toLowerCase().includes("marco"))?.value ?? "Por confirmar");

  return (
    <main className="mentor-paper min-h-screen text-[#10283a]">
      <div className="h-[100px] bg-[#081d2d]" aria-hidden="true" />
      <div className="mentor-file-tabs" aria-hidden="true"><span className="mentor-file-tab mentor-file-tab-active">Conocimiento del cliente</span><span className="mentor-file-tab">Fuentes confirmadas</span></div>
      <header className="border-b border-[#b9aa91]/45 px-8 py-7 xl:px-14">
        <div className="mx-auto flex max-w-[1120px] items-center justify-between gap-8">
          <dl className="grid flex-1 grid-cols-2 gap-7 lg:grid-cols-3"><div><dt className="mentor-kicker">Cliente</dt><dd className="mentor-meta-value truncate">{entityName}</dd></div><div><dt className="mentor-kicker">Año</dt><dd className="mentor-meta-value">{period}</dd></div><div><dt className="mentor-kicker">Marco</dt><dd className="mentor-meta-value">{framework}</dd></div></dl>
          <button type="button" onClick={() => router.push(`/onboarding/${clienteId}`)} className="flex items-center gap-2 text-xs text-[#55716e] hover:text-[#17384a]"><span className="material-symbols-outlined text-[18px]">arrow_back</span>Volver a fuentes</button>
        </div>
      </header>
      <div className="mx-auto max-w-[1120px] px-6 pb-16 pt-12 md:px-10">
        <section className={reviewMode ? "hidden" : "text-center"}>
          <p className="mentor-kicker text-[#987c55]">Cuestionario adaptativo · Ronda {activeRound}</p>
          <h1 className="mx-auto mt-4 max-w-3xl font-headline text-5xl leading-[1.02] tracking-[-0.025em] md:text-6xl">Conozcamos esta entidad,<br />una respuesta a la vez.</h1>
          <p className="mx-auto mt-5 max-w-2xl text-sm leading-6 text-[#69767b]">SocioAI adapta la siguiente pregunta a lo que respondes y a las fuentes disponibles. Tú confirmas siempre el resultado.</p>
          {analysis ? <button type="button" onClick={() => { setReviewMode(true); window.scrollTo({ top: 0, behavior: "smooth" }); }} className="mt-5 inline-flex items-center gap-2 rounded-full border border-[#65aaa6]/45 bg-[#eef8f5] px-5 py-2.5 text-xs font-semibold text-[#2c6e6b]"><span className="material-symbols-outlined text-[17px]">fact_check</span>Revisar resultado actual</button> : null}
        </section>

        {error ? <div className="mt-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div> : null}

        <section className={reviewMode ? "hidden" : "mt-10 grid gap-4 md:grid-cols-2"}>
          <details className="rounded-2xl border border-[#c9bca6]/70 bg-[#fffdf8]/70 p-5">
            <summary className="cursor-pointer font-headline text-xl">Hechos declarados <span className="ml-2 font-body text-xs text-[#7a8388]">{draft.facts.length} registrados</span></summary>
            <div className="mt-4 divide-y divide-black/10">
              {draft.facts.map((fact) => (
                <div key={fact.key} className="flex items-start justify-between gap-5 py-3">
                  <div><p className="text-sm font-semibold">{fact.label}</p><p className="text-xs text-slate-500">Fuente: {fact.source}</p></div>
                  <p className="text-right text-sm">{String(fact.value)}</p>
                </div>
              ))}
            </div>
          </details>

          <details className="rounded-2xl border border-[#c9bca6]/70 bg-[#fffdf8]/70 p-5">
            <summary className="cursor-pointer font-headline text-xl">Fuentes utilizadas <span className="ml-2 font-body text-xs text-[#7a8388]">{draft.sources.filter((source) => source.available).length} disponibles</span></summary>
            <div className="mt-4 space-y-3">
              {draft.sources.map((source, index) => (
                <div key={`${source.type}-${index}`} className="rounded-xl border border-black/10 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div><p className="text-sm font-semibold">{source.label}</p><p className="text-xs text-slate-500">{source.name ?? source.authority}{source.period ? ` · ${source.period}` : ""}</p></div>
                    <span className={`rounded-full px-2.5 py-1 text-[11px] ${source.available ? "bg-[#dff3ef] text-[#075b4c]" : "bg-slate-100 text-slate-500"}`}>
                      {SOURCE_STATUS[source.status] ?? source.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </details>
        </section>

        <section className={reviewMode ? "hidden" : "relative mx-auto mt-7 max-w-[860px] overflow-hidden rounded-[24px] border border-[#baa98e] bg-[#fffdf8]/90 shadow-[0_22px_60px_rgba(50,45,34,0.09)]"}>
          <div className="flex items-center justify-between border-b border-[#d6cab8] px-6 py-4">
            <div className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#12374a] text-[#79d7d1]"><span className="material-symbols-outlined text-[19px]">forum</span></span><div><p className="mentor-kicker">Entrevista guiada</p><p className="mt-1 text-xs text-[#7a8388]">{answeredInRound} de {currentQuestions.length} respondidas</p></div></div>
            <div className="flex gap-1.5" aria-label={`Progreso de la ronda ${activeRound}`}>{currentQuestions.map((question, index) => <span key={question.id} className={`h-1.5 rounded-full transition-all ${index === questionIndex ? "w-8 bg-[#2f8582]" : String(answers[question.id] ?? "").trim() ? "w-4 bg-[#73c9c4]" : "w-4 bg-[#d7ccbb]"}`} />)}</div>
          </div>
          <div className="min-h-[390px] p-6 md:p-10">
            {roundStatus === "processing" ? <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex min-h-[310px] flex-col items-center justify-center text-center" role="status"><div className="relative flex h-24 w-24 items-center justify-center"><span className="absolute inset-0 animate-ping rounded-full border border-[#5eb9b4]/35"/><span className="absolute inset-3 animate-pulse rounded-full border border-[#5eb9b4]/55"/><span className="material-symbols-outlined animate-spin text-4xl text-[#2f8582]">progress_activity</span></div><h2 className="mt-6 font-headline text-3xl">Configurando el conocimiento del cliente…</h2><p className="mt-3 max-w-md text-sm leading-6 text-[#6c787c]">Contrasto tus respuestas con las fuentes disponibles para decidir si hace falta una aclaración concreta.</p></motion.div> : activeQuestion ? <AnimatePresence mode="wait"><motion.div key={`${activeRound}-${activeQuestion.id}`} initial={{ opacity: 0, x: 28 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -28 }} transition={{ duration: .24 }}>
              <div className="flex items-start gap-4"><span className="font-headline text-4xl text-[#b39464]">{String(questionIndex + 1).padStart(2, "0")}</span><div><p className="mentor-kicker">Pregunta {questionIndex + 1} de {currentQuestions.length}{activeQuestion.critical ? " · necesaria" : ""}</p><h2 className="mt-3 font-headline text-3xl leading-tight md:text-4xl">{activeQuestion.text}</h2></div></div>
              <label className="mt-7 block"><span className="sr-only">Respuesta del auditor</span><textarea autoFocus value={answers[activeQuestion.id] ?? ""} onChange={(event) => setAnswers((current) => ({ ...current, [activeQuestion.id]: event.target.value }))} rows={5} className="w-full resize-none rounded-2xl border border-[#c9bca6] bg-white/70 px-5 py-4 text-sm leading-6 outline-none transition focus:border-[#2f8582] focus:ring-4 focus:ring-[#2f8582]/10" placeholder="Escribe tu respuesta con el contexto que conozcas…" /></label>
              <details className="mt-4 text-xs text-[#69767b]"><summary className="cursor-pointer font-semibold text-[#44726f]">¿Por qué me pregunta esto?</summary><p className="mt-2 border-l-2 border-[#79c7c2] pl-3 leading-5">{activeQuestion.reason}</p></details>
              <div className="mt-7 flex items-center justify-between"><button type="button" disabled={questionIndex === 0} onClick={() => setQuestionIndex((index) => Math.max(0, index - 1))} className="flex min-h-[44px] items-center gap-2 rounded-xl px-4 text-sm text-[#667579] disabled:opacity-30"><span className="material-symbols-outlined text-[18px]">arrow_back</span>Anterior</button>{questionIndex < currentQuestions.length - 1 ? <button type="button" disabled={!String(answers[activeQuestion.id] ?? "").trim()} onClick={() => setQuestionIndex((index) => Math.min(currentQuestions.length - 1, index + 1))} className="flex min-h-[46px] items-center gap-2 rounded-xl bg-[#12374a] px-6 text-sm font-semibold text-white disabled:opacity-35">Continuar<span className="material-symbols-outlined text-[18px]">arrow_forward</span></button> : <button type="button" disabled={saving || analyzing || pending > 0} onClick={() => void evaluateRound()} className="flex min-h-[46px] items-center gap-2 rounded-xl bg-[#2f8582] px-6 text-sm font-semibold text-white disabled:opacity-35">Evaluar esta ronda<span className="material-symbols-outlined text-[18px]">auto_awesome</span></button>}</div>
            </motion.div></AnimatePresence> : <p className="py-20 text-center text-sm text-[#69767b]">No hay preguntas pendientes en esta ronda.</p>}
          </div>
          {previousQuestions.length ? <details className="mt-5 rounded-xl border border-black/10 bg-slate-50 p-4"><summary className="cursor-pointer text-sm font-semibold text-slate-600">Ver {previousQuestions.length} respuestas de rondas anteriores</summary><div className="mt-4 space-y-3">{previousQuestions.map((question) => <div key={question.id} className="rounded-lg bg-white p-4 text-sm"><p className="font-semibold">{question.text}</p><p className="mt-1 text-slate-600">{answers[question.id]}</p></div>)}</div></details> : null}
          {roundStatus === "new_round" ? <div className="mt-5 rounded-xl border border-sky-200 bg-sky-50 p-4 text-sm text-sky-900" role="status"><strong>Necesito una aclaración adicional.</strong> La nueva ronda aparece porque todavía falta confirmar información concreta.</div> : null}
          {roundStatus === "complete" ? <div className="mt-5 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900" role="status"><strong>SocioAI no necesita más preguntas por ahora.</strong> El perfil queda {draft.pending_confirmations.length ? `provisional con ${draft.pending_confirmations.length} pendientes por confirmar` : "listo para confirmar"}.</div> : null}
        </section>

        {reviewMode && analysis ? <section className="mx-auto max-w-[980px]">
          <div className="text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full border border-[#62b9b4]/35 bg-[#e8f5f2] text-[#236f6c]"><span className="material-symbols-outlined text-3xl">verified</span></div>
            <p className="mentor-kicker mt-5 text-[#987c55]">Resultado del conocimiento del cliente</p>
            <h1 className="mx-auto mt-4 max-w-3xl font-headline text-5xl leading-[1.02] tracking-[-0.025em] md:text-6xl">Ya tengo una primera<br />comprensión de la entidad.</h1>
            <p className="mx-auto mt-5 max-w-2xl text-sm leading-6 text-[#69767b]">Revisa este perfil antes de permitir que SocioAI lo utilice en el Mentor. Los antecedentes e hipótesis permanecen separados de los hechos confirmados.</p>
          </div>

          <div className="mt-9 grid grid-cols-2 gap-3 md:grid-cols-4">
            <div className="rounded-xl border border-[#c9bca6] bg-white/60 p-4"><p className="mentor-kicker">Rondas</p><p className="mt-2 font-headline text-2xl">{activeRound}</p></div>
            <div className="rounded-xl border border-[#c9bca6] bg-white/60 p-4"><p className="mentor-kicker">Respuestas</p><p className="mt-2 font-headline text-2xl">{Object.values(answers).filter((value) => String(value).trim()).length}</p></div>
            <div className="rounded-xl border border-[#c9bca6] bg-white/60 p-4"><p className="mentor-kicker">Fuentes</p><p className="mt-2 font-headline text-2xl">{analysis.sources.length}</p></div>
            <div className="rounded-xl border border-[#c9bca6] bg-white/60 p-4"><p className="mentor-kicker">Pendientes</p><p className="mt-2 font-headline text-2xl">{draft.pending_confirmations.length}</p></div>
          </div>

          <article className="mt-6 rounded-[22px] border border-[#baa98e] bg-[#fffdf8]/90 p-6 shadow-[0_16px_40px_rgba(50,45,34,0.07)] md:p-8">
            <div className="flex items-start gap-4"><span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[#12374a] text-[#79d7d1]"><span className="material-symbols-outlined">domain</span></span><div><p className="mentor-kicker">Resumen propuesto</p><h2 className="mt-2 font-headline text-3xl">Lo que SocioAI entendió</h2></div></div>
            <dl className="mt-6 grid gap-5 md:grid-cols-3"><div><dt className="mentor-kicker">Actividad</dt><dd className="mt-2 text-sm leading-6">{analysis.entity_summary?.activity || "No determinada"}</dd></div><div><dt className="mentor-kicker">Modelo de ingresos</dt><dd className="mt-2 text-sm leading-6">{analysis.entity_summary?.revenue_model || "No determinado"}</dd></div><div><dt className="mentor-kicker">Entorno regulatorio</dt><dd className="mt-2 text-sm leading-6">{analysis.entity_summary?.regulatory_context || "No determinado"}</dd></div></dl>
            <button type="button" onClick={() => { setReviewMode(false); window.scrollTo({ top: 0, behavior: "smooth" }); }} className="mt-6 flex items-center gap-2 text-xs font-semibold text-[#2f7775]"><span className="material-symbols-outlined text-[17px]">edit</span>Modificar respuestas que originaron este resumen</button>
          </article>

          <div className="mt-6 grid gap-5 md:grid-cols-2">
            <article className="rounded-[20px] border border-[#c9bca6] bg-white/65 p-6"><div className="flex items-center justify-between"><div><p className="mentor-kicker">Antecedentes</p><h2 className="mt-2 font-headline text-2xl">Período anterior</h2></div><span className="rounded-full bg-[#e8eef4] px-3 py-1 text-xs">{analysis.prior_findings.length}</span></div><div className="mt-5 space-y-3">{analysis.prior_findings.length ? analysis.prior_findings.map((item, index) => <details key={`${item.title}-${index}`} className="rounded-xl border border-[#d7ccbb] bg-[#fffdf8] p-4"><summary className="cursor-pointer text-sm font-semibold">{item.title}</summary><p className="mt-2 text-xs leading-5 text-[#69767b]">{item.why_it_matters || item.follow_up_question}</p><ReviewControls item={item}/></details>) : <p className="text-sm text-[#69767b]">No se identificaron antecedentes.</p>}</div></article>
            <article className="rounded-[20px] border border-[#c9bca6] bg-white/65 p-6"><div className="flex items-center justify-between"><div><p className="mentor-kicker">Cambios</p><h2 className="mt-2 font-headline text-2xl">Período actual</h2></div><span className="rounded-full bg-[#e9f5f2] px-3 py-1 text-xs">{analysis.changes.length}</span></div><div className="mt-5 space-y-3">{analysis.changes.length ? analysis.changes.map((item, index) => <details key={`${item.title}-${index}`} className="rounded-xl border border-[#d7ccbb] bg-[#fffdf8] p-4"><summary className="cursor-pointer text-sm font-semibold">{item.title}</summary><p className="mt-2 text-xs leading-5 text-[#69767b]">{item.why_it_matters || item.why_relevant}</p><ReviewControls item={item}/></details>) : <p className="text-sm text-[#69767b]">No se identificaron cambios relevantes.</p>}</div></article>
            <article className="rounded-[20px] border border-[#c9bca6] bg-white/65 p-6"><div className="flex items-center justify-between"><div><p className="mentor-kicker">Hipótesis</p><h2 className="mt-2 font-headline text-2xl">Riesgos por validar</h2></div><span className="rounded-full bg-amber-50 px-3 py-1 text-xs">{analysis.risk_hypotheses.length}</span></div><div className="mt-5 space-y-3">{analysis.risk_hypotheses.map((item, index) => <details key={`${item.title}-${index}`} className="rounded-xl border border-[#d7ccbb] bg-[#fffdf8] p-4"><summary className="cursor-pointer text-sm font-semibold">{item.title}</summary><p className="mt-2 text-xs leading-5 text-[#69767b]">{item.why_it_matters}</p><ReviewControls item={item}/></details>)}</div></article>
            <article className="rounded-[20px] border border-[#c9bca6] bg-white/65 p-6"><div className="flex items-center justify-between"><div><p className="mentor-kicker">Estimaciones</p><h2 className="mt-2 font-headline text-2xl">Por comprender</h2></div><span className="rounded-full bg-[#f0e9dd] px-3 py-1 text-xs">{analysis.estimate_hypotheses.length}</span></div><div className="mt-5 space-y-3">{analysis.estimate_hypotheses.map((item, index) => <details key={`${item.title}-${index}`} className="rounded-xl border border-[#d7ccbb] bg-[#fffdf8] p-4"><summary className="cursor-pointer text-sm font-semibold">{item.title}</summary><p className="mt-2 text-xs leading-5 text-[#69767b]">{item.why_relevant}</p><ReviewControls item={item}/></details>)}</div></article>
          </div>

          {analysis.missing_information?.length ? <article className="mt-6 rounded-[20px] border border-amber-200 bg-amber-50/70 p-6"><p className="mentor-kicker text-amber-800">Información pendiente</p><ul className="mt-4 grid gap-2 text-sm text-amber-950 md:grid-cols-2">{analysis.missing_information.map((item) => <li key={item} className="flex gap-2"><span className="material-symbols-outlined text-[17px]">schedule</span>{item}</li>)}</ul></article> : null}

          <div className="sticky bottom-5 mt-7 flex flex-col gap-4 rounded-[20px] border border-[#83c7c2] bg-[#eef9f6]/95 p-5 shadow-[0_18px_45px_rgba(23,61,63,.14)] backdrop-blur md:flex-row md:items-center md:justify-between"><p className="max-w-2xl text-sm leading-6 text-[#315b59]">Al confirmar, SocioAI usará los hechos y decisiones visibles como contexto. Las hipótesis continuarán identificadas como asuntos por validar.</p><div className="flex gap-3"><button type="button" onClick={() => { setReviewMode(false); window.scrollTo({ top: 0, behavior: "smooth" }); }} className="rounded-xl border border-[#9cbdb9] bg-white px-5 py-3 text-sm font-semibold">Modificar respuestas</button><button type="button" disabled={saving} onClick={() => void confirmAndContinue()} className="rounded-xl bg-[#12374a] px-5 py-3 text-sm font-semibold text-white disabled:opacity-50">{saving ? "Confirmando…" : "Confirmar perfil y entrar al Mentor"}</button></div></div>
        </section> : null}

        {draft.pending_items.length ? (
          <section className={reviewMode ? "hidden" : "sovereign-card mt-6"} data-testid="pending-confirmations">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.14em] text-amber-700">Seguimiento durante el encargo</p>
                <h2 className="mt-1 font-headline text-3xl">Pendientes por confirmar</h2>
                <p className="mt-2 max-w-3xl text-sm text-slate-600">Completa la información cuando esté disponible. SocioAI conserva el origen y el efecto del pendiente sin convertirlo en un hecho.</p>
              </div>
              <span className="rounded-full bg-amber-100 px-3 py-1.5 text-xs font-semibold text-amber-900">{draft.pending_confirmations.length} abiertos</span>
            </div>
            <div className="mt-6 space-y-4">
              {draft.pending_items.map((item) => {
                const edit = pendingEdits[item.question_id] ?? { status: item.status, answer: item.answer };
                const closed = item.status === "confirmed" || item.status === "not_applicable";
                return (
                  <article key={item.question_id} className={`rounded-xl border p-5 ${closed ? "border-emerald-200 bg-emerald-50/40" : "border-amber-200 bg-amber-50/40"}`}>
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="max-w-3xl"><p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">{item.area}</p><h3 className="mt-1 text-sm font-semibold">{item.question}</h3><p className="mt-2 text-xs leading-5 text-slate-600"><strong>Efecto:</strong> {item.impact}</p></div>
                      <select aria-label={`Estado de ${item.question}`} value={edit.status} onChange={(event) => setPendingEdits((current) => ({ ...current, [item.question_id]: { ...edit, status: event.target.value as keyof typeof PENDING_STATUS_LABELS } }))} className="rounded-lg border border-black/15 bg-white px-3 py-2 text-xs">
                        {Object.entries(PENDING_STATUS_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                      </select>
                    </div>
                    <textarea aria-label={`Respuesta para ${item.question}`} value={edit.answer} onChange={(event) => setPendingEdits((current) => ({ ...current, [item.question_id]: { ...edit, answer: event.target.value } }))} rows={3} className="mt-4 w-full rounded-xl border border-black/15 bg-white px-4 py-3 text-sm outline-none focus:border-[#177e82]" placeholder="Actualiza la respuesta cuando recibas información…" />
                    <div className="mt-3 flex items-center justify-between gap-3"><p className="text-[11px] text-slate-500">Estado actual: {PENDING_STATUS_LABELS[item.status]}</p><button type="button" disabled={pendingSavingId === item.question_id} onClick={() => void savePendingItem(item.question_id)} className="rounded-lg bg-[#177e82] px-4 py-2 text-xs font-semibold text-white disabled:opacity-50">{pendingSavingId === item.question_id ? "Guardando…" : "Guardar pendiente"}</button></div>
                  </article>
                );
              })}
            </div>
          </section>
        ) : null}

        <section className={reviewMode ? "hidden" : "sovereign-card mt-6"}>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="max-w-3xl">
              <p className="text-xs uppercase tracking-[0.14em] text-slate-500">Lectura asistida por IA</p>
              <h2 className="mt-1 font-headline text-3xl">Hipótesis para orientar tu comprensión</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">La IA analiza únicamente las fuentes cargadas y tus respuestas. Nada de esta sección se convierte automáticamente en riesgo de auditoría.</p>
            </div>
            <button type="button" disabled={analyzing} onClick={() => void runAnalysis(Boolean(analysis))} className="rounded-xl bg-[#177e82] px-5 py-3 text-sm font-semibold text-white disabled:opacity-50">
              {analyzing ? "Analizando fuentes…" : analysis ? "Regenerar análisis" : "Analizar fuentes con IA"}
            </button>
          </div>

          {!analysis ? (
            <div className="mt-6 rounded-xl border border-dashed border-black/15 bg-slate-50 p-6 text-sm text-slate-600">El análisis no se ejecuta automáticamente para cuidar privacidad y tokens. Tú decides cuándo iniciarlo.</div>
          ) : (
            <div className="mt-6 space-y-6">
              {analysis.entity_summary ? (
                <div className="rounded-xl border border-[#89d3d4]/50 bg-[#f2fbfb] p-5">
                  <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#177e82]">Resumen propuesto</p>
                  <p className="mt-2 text-sm"><strong>Actividad:</strong> {analysis.entity_summary.activity || "No determinada"}</p>
                  <p className="mt-1 text-sm"><strong>Ingresos:</strong> {analysis.entity_summary.revenue_model || "No determinado"}</p>
                  <p className="mt-1 text-sm"><strong>Entorno regulatorio:</strong> {analysis.entity_summary.regulatory_context || "No determinado"}</p>
                </div>
              ) : null}

              {analysis.changes.length ? (
                <div>
                  <h3 className="font-headline text-2xl">Cambios o continuidades por confirmar</h3>
                  <div className="mt-3 grid gap-3 md:grid-cols-2">
                    {analysis.changes.map((item, index) => (
                      <article key={`${item.title}-${index}`} className="rounded-xl border border-black/10 p-4">
                        <p className="text-sm font-semibold">{item.title}</p>
                        <p className="mt-1 text-xs leading-5 text-slate-600">{item.why_it_matters ?? item.why_relevant}</p>
                        <Evidence item={item} />
                        <ReviewControls item={item} />
                      </article>
                    ))}
                  </div>
                </div>
              ) : null}

              {analysis.prior_findings?.length ? <div><h3 className="font-headline text-2xl">Hallazgos anteriores por seguir</h3><p className="mt-1 text-xs text-slate-500">Son antecedentes, no riesgos vigentes, hasta obtener evidencia del periodo actual.</p><div className="mt-3 grid gap-3 md:grid-cols-2">{analysis.prior_findings.map((item, index) => <article key={`${item.title}-${index}`} className="rounded-xl border border-blue-200 bg-blue-50/40 p-4"><p className="text-sm font-semibold">{item.title}</p>{item.follow_up_question ? <p className="mt-2 text-xs text-slate-700"><strong>Pregunta de seguimiento:</strong> {item.follow_up_question}</p> : null}<Evidence item={item} /><ReviewControls item={item} /></article>)}</div></div> : null}

              <div className="grid gap-5 lg:grid-cols-2">
                <div>
                  <h3 className="font-headline text-2xl">Riesgos por validar</h3>
                  <div className="mt-3 space-y-3">
                    {analysis.risk_hypotheses.length ? analysis.risk_hypotheses.map((item, index) => (
                      <article key={`${item.title}-${index}`} className="rounded-xl border border-black/10 p-4">
                        <div className="flex gap-3"><span className="material-symbols-outlined text-amber-600">hypothesis</span><div><p className="text-sm font-semibold">{item.title}</p><p className="mt-1 text-xs leading-5 text-slate-600">{item.why_it_matters}</p></div></div>
                        <Evidence item={item} />
                        <ReviewControls item={item} />
                      </article>
                    )) : <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">No se propusieron riesgos con la información disponible.</p>}
                  </div>
                </div>
                <div>
                  <h3 className="font-headline text-2xl">Estimaciones por comprender</h3>
                  <div className="mt-3 space-y-3">
                    {analysis.estimate_hypotheses.length ? analysis.estimate_hypotheses.map((item, index) => (
                      <article key={`${item.title}-${index}`} className="rounded-xl border border-black/10 p-4">
                        <p className="text-sm font-semibold">{item.title}</p><p className="mt-1 text-xs leading-5 text-slate-600">{item.why_relevant}</p>
                        <Evidence item={item} />
                        <ReviewControls item={item} />
                      </article>
                    )) : <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">No se identificaron estimaciones; confirma si realmente no existen.</p>}
                  </div>
                </div>
              </div>

              {analysis.missing_information?.length ? <div className="rounded-xl bg-amber-50 p-5"><p className="text-sm font-semibold text-amber-900">Información que todavía falta</p><ul className="mt-2 space-y-1 text-sm text-amber-900">{analysis.missing_information.map((item) => <li key={item}>• {item}</li>)}</ul></div> : null}
              {analysis.sources.length ? <div className="rounded-xl bg-slate-50 p-5"><p className="text-sm font-semibold">Mapa de evidencia</p><div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-600">{analysis.sources.map((source) => <span key={source.source_id} className="rounded-lg border border-black/10 bg-white px-3 py-2"><strong>{source.source_id}</strong>: {source.name}{source.period ? ` · ${source.period}` : ""}</span>)}</div></div> : null}
              <div className="flex flex-wrap items-center justify-between gap-2 border-t border-black/10 pt-4 text-xs text-slate-500"><p>{analysis.disclaimer}</p><p>{analysis.model?.model ? `Modelo: ${analysis.model.model}` : ""}{analysis.model?.input_tokens ? ` · ${analysis.model.input_tokens} tokens de entrada` : ""}</p></div>
            </div>
          )}
        </section>

        {draft.limitations.length ? (
          <section className={reviewMode ? "hidden" : "mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-6"}>
            <h2 className="font-semibold text-amber-900">Limitaciones visibles</h2>
            <ul className="mt-3 space-y-2 text-sm text-amber-900">{draft.limitations.map((item) => <li key={item}>• {item}</li>)}</ul>
          </section>
        ) : null}

        <div className={reviewMode ? "hidden" : "mt-6 flex flex-col items-stretch justify-between gap-4 rounded-2xl border border-[#89d3d4]/50 bg-[#edfafa] p-5 md:flex-row md:items-center"}>
          <p className="max-w-3xl text-sm text-[#164e52]">{draft.transparency_note}</p>
          <div className="flex shrink-0 gap-3">
            <button type="button" disabled={saving || pending > 0} onClick={() => void saveAnswers()} className="rounded-xl border border-black/15 bg-white px-5 py-3 text-sm font-semibold disabled:opacity-50">{saving ? "Revisando respuestas…" : "Enviar respuestas"}</button>
            <button type="button" disabled={saving || pending > 0} onClick={() => void confirmAndContinue()} className="rounded-xl bg-[#002f30] px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40">
              {saving ? "Guardando…" : "Confirmar y entrar al Mentor"}
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
