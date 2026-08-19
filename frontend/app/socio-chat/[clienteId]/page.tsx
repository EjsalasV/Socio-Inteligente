"use client";

import { ChangeEvent, FormEvent, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import { createChatConversation, deleteChatConversation, getChatConversations, getChatHistory, postChat, postChatFeedback, postPilotSurvey, renameChatConversation, type ChatConversation } from "../../../lib/api";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import { useDashboard } from "../../../lib/hooks/useDashboard";
import { useLearningRole } from "../../../lib/hooks/useLearningRole";
import { useRiskEngine } from "../../../lib/hooks/useRiskEngine";
import { ReactMarkdown } from "../../../components/ReactMarkdown";
import { logoutSession } from "../../../lib/auth-session";
import { useWorkflow } from "../../../lib/hooks/useWorkflow";
import { summarizeUiError } from "../../../lib/ui-errors";
import { uploadClienteDocumento } from "../../../lib/api/clientes";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  timestamp: string;
  citations?: Array<{
    source: string;
    excerpt: string;
    norma?: string;
    title?: string;
    version?: string;
    vigente_desde?: string;
    ultima_actualizacion?: string;
    jurisdiccion?: string;
  }>;
  confidence?: number;
  mode_used?: string;
  web_search_used?: boolean;
  expert_criteria_used?: boolean;
  quality_control?: {
    publication?: "published" | "withheld" | string;
    normative?: string;
    grounding?: string;
    quality_repair_used?: boolean;
    normative_redaction_used?: boolean;
    grounding_redaction_used?: boolean;
    trace_id?: string;
    trace_status?: string;
  };
};

type HistoryMessage = {
  role?: "user" | "assistant" | string;
  text?: string;
  timestamp?: string;
  citations?: ChatMessage["citations"];
  confidence?: number;
  mode_used?: string;
  quality_control?: ChatMessage["quality_control"];
};

const QUICK_PROMPTS = [
  "Ayúdame a comprender qué merece atención en este cliente.",
  "Enséñame cómo analizar una estimación contable sin saltar a conclusiones.",
  "Desafía mi criterio sobre el riesgo que estoy evaluando.",
];

function normalizeRefPath(path: string): string {
  if (!path) return "Fuente técnica";
  return path.replace(/\\/g, "/");
}

function prettyRefLabel(path: string): string {
  const p = normalizeRefPath(path);
  const parts = p.split("/").filter(Boolean);
  const file = parts[parts.length - 1] || p;
  const base = file.replace(/\.md$/i, "").replace(/_/g, " ");
  return base.replace(/\b\w/g, (x) => x.toUpperCase());
}

function uniqueCitations(
  citations: NonNullable<ChatMessage["citations"]>,
): NonNullable<ChatMessage["citations"]> {
  const seen = new Set<string>();
  const out: NonNullable<ChatMessage["citations"]> = [];
  for (const c of citations) {
    const key = `${normalizeRefPath(c.source || "")}|${c.norma || ""}`;
    if (!key || seen.has(key)) continue;
    seen.add(key);
    out.push(c);
  }
  return out;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function normalizeChatCitations(input: unknown): NonNullable<ChatMessage["citations"]> {
  if (!Array.isArray(input)) return [];
  type Citation = NonNullable<ChatMessage["citations"]>[number];
  const mapped: Array<Citation | null> = input.map((item: unknown) => {
      if (!isRecord(item)) return null;
      const source = typeof item.source === "string" ? item.source : "";
      const excerpt = typeof item.excerpt === "string" ? item.excerpt : "";
      return {
        source,
        excerpt,
        norma: typeof item.norma === "string" ? item.norma : undefined,
        version: typeof item.version === "string" ? item.version : undefined,
        vigente_desde: typeof item.vigente_desde === "string" ? item.vigente_desde : undefined,
        ultima_actualizacion:
          typeof item.ultima_actualizacion === "string" ? item.ultima_actualizacion : undefined,
        jurisdiccion: typeof item.jurisdiccion === "string" ? item.jurisdiccion : undefined,
      };
    });
  return mapped.filter((item: Citation | null): item is Citation => item !== null);
}

function nowLabel(): string {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

type ChatNotice = {
  tone: "info" | "error";
  title: string;
  detail: string;
};

export default function SocioChatPage() {
  const router = useRouter();
  const { clienteId } = useAuditContext();
  const { role } = useLearningRole();
  const { data: dashboard, isLoading: dashboardLoading, error: dashboardError } = useDashboard(clienteId);
  const { data: riskData } = useRiskEngine(clienteId);
  const { data: workflow } = useWorkflow(clienteId);

  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState("");
  const [mentorMode, setMentorMode] = useState<"teach" | "help" | "challenge">("help");
  const [profileOpen, setProfileOpen] = useState(false);
  const [showThread, setShowThread] = useState(false);
  const [loadingConversations, setLoadingConversations] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [chatNotice, setChatNotice] = useState<ChatNotice | null>(null);
  const [showConversationActionsAlways, setShowConversationActionsAlways] = useState(false);
  const [uploadingSource, setUploadingSource] = useState(false);
  const [attachedSourceName, setAttachedSourceName] = useState("");
  const sourceInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let active = true;
    async function loadConversations(): Promise<void> {
      setLoadingConversations(true);
      setChatNotice({
        tone: "info",
        title: "Cargando conversaciones",
        detail: "Estoy recuperando el historial reciente del Mentor.",
      });
      try {
        const response = await getChatConversations(clienteId);
        if (!active) return;
        let rows = response?.data?.conversations ?? [];
        if (rows.length === 0) {
          const created = await createChatConversation(clienteId);
          rows = created.data?.conversation ? [created.data.conversation] : [];
        }
        setConversations(rows);
        setActiveConversationId(rows[0]?.id ?? "");
        if (active) setChatNotice(null);
      } catch (reason) {
        if (active) {
          setConversations([]);
          setActiveConversationId("");
          setChatNotice({
            tone: "error",
            title: "No se pudo cargar el Mentor",
            detail: summarizeUiError(
              reason,
              "No se pudo recuperar el historial de conversaciones.",
              "las conversaciones del Mentor",
            ).detail,
          });
        }
      } finally {
        if (active) setLoadingConversations(false);
      }
    }
    if (clienteId) void loadConversations();
    return () => { active = false; };
  }, [clienteId]);

  useEffect(() => {
    let active = true;
    async function loadHistory(): Promise<void> {
      if (!activeConversationId) {
        setMessages([]);
        setLoadingHistory(false);
        return;
      }
      setLoadingHistory(true);
      setChatNotice({
        tone: "info",
        title: "Cargando historial",
        detail: "Estoy abriendo la conversación seleccionada.",
      });
      try {
        const response = await getChatHistory(clienteId, activeConversationId);
        if (!active) return;
        const raw: HistoryMessage[] = Array.isArray(response?.data?.messages)
          ? (response.data.messages as unknown as HistoryMessage[])
          : [];
        const mapped: ChatMessage[] = raw
          .filter(
            (m: HistoryMessage): m is HistoryMessage & { role: "user" | "assistant"; text: string } =>
              Boolean(m) && (m.role === "user" || m.role === "assistant") && typeof m.text === "string",
          )
          .map((m, idx) => ({
            id: `h-${idx}-${m.timestamp || ""}`,
            role: m.role,
            text: m.text,
            timestamp: m.timestamp ? new Date(m.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : nowLabel(),
            citations: Array.isArray(m.citations) ? (m.citations as ChatMessage["citations"]) : [],
            confidence: typeof m.confidence === "number" ? m.confidence : 0,
            mode_used: m.mode_used,
            quality_control: m.quality_control,
          }));
        setMessages(mapped.slice(-120));
        if (active) setChatNotice(null);
      } catch (reason) {
        if (!active) return;
        setMessages([]);
        setChatNotice({
          tone: "error",
          title: "No se pudo cargar el historial",
          detail: summarizeUiError(
            reason,
            "No se pudo recuperar el historial de la conversación.",
            "el historial de la conversación",
          ).detail,
        });
      } finally {
        if (active) setLoadingHistory(false);
      }
    }
    void loadHistory();
    return () => { active = false; };
  }, [clienteId, activeConversationId]);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(hover: none), (pointer: coarse)");
    const update = () => setShowConversationActionsAlways(mediaQuery.matches);

    update();

    if (typeof mediaQuery.addEventListener === "function") {
      mediaQuery.addEventListener("change", update);
      return () => mediaQuery.removeEventListener("change", update);
    }

    mediaQuery.addListener(update);
    return () => mediaQuery.removeListener(update);
  }, []);

  const openRisks = useMemo(() => riskData?.areas_criticas?.slice(0, 2) ?? [], [riskData]);
  const conversationActionClass = showConversationActionsAlways
    ? "opacity-100 transition"
    : "opacity-0 transition group-hover:opacity-100 group-focus-within:opacity-100 focus-visible:opacity-100";
  async function handleSend(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const modeInstruction = mentorMode === "teach" ? "Enséñame: " : mentorMode === "challenge" ? "Desafía mi criterio: " : "Ayúdame: ";
    const prompt = `${modeInstruction}${input.trim()}`;
    if (!prompt || sending) return;

    const userMessage: ChatMessage = {
      id: `u-${Date.now()}`,
      role: "user",
      timestamp: nowLabel(),
      text: prompt,
    };

    setMessages((prev) => [...prev, userMessage]);
    setShowThread(true);
    setInput("");
    setSending(true);

    try {
      const response = await postChat(clienteId, { message: prompt, conversation_id: activeConversationId });
      const answer = response?.data?.answer || "No hubo respuesta del asistente.";
      const assistantMessage: ChatMessage = {
        id: `a-${Date.now()}`,
        role: "assistant",
        timestamp: nowLabel(),
        text: answer,
        citations: normalizeChatCitations(response?.data?.citations),
        confidence: response?.data?.confidence ?? 0,
        mode_used: response?.data?.mode_used ?? "chat",
        web_search_used: response?.data?.web_search_used === true,
        expert_criteria_used: response?.data?.expert_criteria_used === true,
        quality_control: response?.data?.quality_control as ChatMessage["quality_control"],
      };
      setMessages((prev) => [...prev, assistantMessage]);
      const refreshed = await getChatConversations(clienteId);
      setConversations(refreshed.data?.conversations ?? []);
      setChatNotice(null);
    } catch (err) {
      const summary = summarizeUiError(err, "No se pudo consultar al asistente.", "el mensaje");
      const message = summary.detail;
      setChatNotice({
        tone: "error",
        title: summary.title,
        detail: message,
      });
      const assistantMessage: ChatMessage = {
        id: `a-${Date.now()}`,
        role: "assistant",
        timestamp: nowLabel(),
        text: `Error: ${message}`,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } finally {
      setSending(false);
    }
  }

  async function handleResponseFeedback(message: ChatMessage, outcome: "helpful" | "incorrect"): Promise<void> {
    const traceId = message.quality_control?.trace_id;
    if (!traceId) return;
    let comment = "";
    if (outcome === "incorrect") {
      const entered = window.prompt(
        "Describe brevemente el problema sin incluir nombres, saldos, RUC ni datos identificables del cliente.",
        "",
      );
      if (entered === null) return;
      comment = entered.trim().slice(0, 500);
    }
    try {
      await postChatFeedback(clienteId, {
        trace_id: traceId,
        outcome,
        issue_type: outcome === "incorrect" ? "other" : "",
        comment,
      });
      setChatNotice({
        tone: "info",
        title: outcome === "helpful" ? "Respuesta marcada como útil" : "Problema registrado",
        detail: "El feedback quedó vinculado a la traza de calidad, no al entrenamiento del modelo.",
      });
    } catch (reason) {
      const summary = summarizeUiError(reason, "No se pudo registrar el feedback.", "la evaluación de la respuesta");
      setChatNotice({ tone: "error", title: summary.title, detail: summary.detail });
    }
  }

  async function handleSessionEvaluation(): Promise<void> {
    const timeRaw = window.prompt("¿Cuántos minutos aproximados te ahorró esta sesión?", "0");
    if (timeRaw === null) return;
    const beforeRaw = window.prompt("Comprensión antes de usar SocioAI (1 a 5)", "3");
    if (beforeRaw === null) return;
    const afterRaw = window.prompt("Comprensión después de usar SocioAI (1 a 5)", "4");
    if (afterRaw === null) return;
    const timeSaved = Math.max(0, Math.min(480, Number.parseInt(timeRaw, 10) || 0));
    const before = Math.max(1, Math.min(5, Number.parseInt(beforeRaw, 10) || 3));
    const after = Math.max(1, Math.min(5, Number.parseInt(afterRaw, 10) || 3));
    try {
      await postPilotSurvey(clienteId, {
        conversation_id: activeConversationId,
        time_saved_minutes: timeSaved,
        understanding_before: before,
        understanding_after: after,
        would_reuse: window.confirm("¿Volverías a usar SocioAI en otro encargo?"),
        willing_to_pay: window.confirm("Si mantiene esta utilidad, ¿considerarías pagar por SocioAI?"),
      });
      setChatNotice({ tone: "info", title: "Evaluación Alpha registrada", detail: "Gracias. Estas métricas no entrenan al modelo ni incorporan datos del cliente." });
    } catch (reason) {
      const summary = summarizeUiError(reason, "No se pudo registrar la evaluación.", "la evaluación Alpha");
      setChatNotice({ tone: "error", title: summary.title, detail: summary.detail });
    }
  }

  async function handleNewConversation(): Promise<void> {
    try {
      setChatNotice({
        tone: "info",
        title: "Creando conversación",
        detail: "Estoy preparando un nuevo hilo para este cliente.",
      });
      const response = await createChatConversation(clienteId);
      const row = response.data?.conversation;
      if (!row) return;
      setConversations((prev) => [row, ...prev]);
      setActiveConversationId(row.id);
      setMessages([]);
      setShowThread(false);
      setChatNotice(null);
    } catch (reason) {
      const summary = summarizeUiError(reason, "No se pudo crear una nueva conversación.", "una conversación nueva");
      setChatNotice({ tone: "error", title: summary.title, detail: summary.detail });
    }
  }

  async function handleRenameConversation(row: ChatConversation): Promise<void> {
    const title = window.prompt("Nombre de la conversación", row.title)?.trim();
    if (!title) return;
    try {
      const response = await renameChatConversation(clienteId, row.id, title);
      const updated = response.data?.conversation;
      if (updated) setConversations((prev) => prev.map((item) => item.id === row.id ? updated : item));
      setChatNotice(null);
    } catch (reason) {
      const summary = summarizeUiError(reason, "No se pudo renombrar la conversación.", "la conversación");
      setChatNotice({ tone: "error", title: summary.title, detail: summary.detail });
    }
  }

  async function handleDeleteConversation(row: ChatConversation): Promise<void> {
    if (!window.confirm(`¿Eliminar la conversación “${row.title}”? Esta acción no se puede deshacer.`)) return;
    try {
      await deleteChatConversation(clienteId, row.id);
      const remaining = conversations.filter((item) => item.id !== row.id);
      setConversations(remaining);
      if (activeConversationId === row.id) {
        setActiveConversationId(remaining[0]?.id ?? "");
        setMessages([]);
      }
      setChatNotice(null);
    } catch (reason) {
      const summary = summarizeUiError(reason, "No se pudo eliminar la conversación.", "la conversación");
      setChatNotice({ tone: "error", title: summary.title, detail: summary.detail });
    }
  }

  async function handleSourceSelected(event: ChangeEvent<HTMLInputElement>): Promise<void> {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file || uploadingSource) return;

    setUploadingSource(true);
    setChatNotice({
      tone: "info",
      title: "Procesando fuente",
      detail: `SocioAI está incorporando ${file.name} al contexto del cliente.`,
    });
    try {
      const document = await uploadClienteDocumento(clienteId, file, "other");
      setAttachedSourceName(document.name);
      const indexed = document.ingestion?.indexed === true;
      setChatNotice({
        tone: indexed ? "info" : "error",
        title: indexed ? "Fuente disponible para el Mentor" : "Fuente guardada con advertencias",
        detail: indexed
          ? `${document.name} quedó indexado y podrá respaldar las próximas respuestas.`
          : `${document.name} se conservó, pero no pudo indexarse completamente. Revísalo en Fuentes del cliente.`,
      });
    } catch (reason) {
      const summary = summarizeUiError(reason, "No se pudo adjuntar la fuente.", "el archivo seleccionado");
      setChatNotice({ tone: "error", title: summary.title, detail: summary.detail });
    } finally {
      setUploadingSource(false);
    }
  }

  if (dashboardLoading) return <DashboardSkeleton />;
  if (dashboardError) return <ErrorMessage message={dashboardError} />;
  if (!dashboard) return <ErrorMessage message="No hay contexto del cliente para Socio Chat." />;

  const phaseLabel = workflow?.current_phase === "informe" ? "Informe" : workflow?.current_phase === "ejecucion" ? "Visita final" : "Planificación";
  const recentConversation = conversations[0];
  const suggestedRisk = openRisks[0];
  const suggestedAreaHref = suggestedRisk?.area_id
    ? `/areas/${encodeURIComponent(clienteId)}/${encodeURIComponent(suggestedRisk.area_id)}`
    : `/entity-profile/${encodeURIComponent(clienteId)}`;

  return (
    <main className="mentor-paper min-h-screen text-[#10283a]">
      <div className="h-[100px] bg-[#081d2d]" aria-hidden="true" />
      <div className="mentor-file-tabs" aria-hidden="true">
        <span className="mentor-file-tab mentor-file-tab-active">Expediente vivo</span>
        <span className="mentor-file-tab">Fuentes confirmadas</span>
      </div>

      <header className="relative z-20 flex min-h-[105px] items-center justify-between border-b border-[#b9aa91]/45 px-8 xl:px-14">
        <dl className="grid grid-cols-2 gap-x-10 gap-y-3 lg:grid-cols-4 xl:gap-x-16">
          <div><dt className="mentor-kicker">Cliente</dt><dd className="mentor-meta-value max-w-[230px] truncate">{dashboard.nombre_cliente}</dd></div>
          <div><dt className="mentor-kicker">Año</dt><dd className="mentor-meta-value">{dashboard.periodo || "Actual"}</dd></div>
          <div><dt className="mentor-kicker">Fase</dt><dd className="mentor-meta-value">{phaseLabel}</dd></div>
          <div><dt className="mentor-kicker">Marco</dt><dd className="mentor-meta-value">NIIF para PYMES</dd></div>
        </dl>
        <div className="absolute -top-[70px] right-8 ml-5 xl:right-14">
          <button type="button" onClick={() => setProfileOpen((value) => !value)} className="flex h-11 w-11 items-center justify-center rounded-full border border-[#173b46]/20 bg-[#2f7775] font-headline text-sm text-white shadow-sm" aria-label="Abrir menú de usuario" aria-expanded={profileOpen}>BF</button>
          {profileOpen ? <div className="absolute right-0 top-14 w-56 rounded-xl border border-[#cfc2ac] bg-[#fffdf8] p-2 text-sm shadow-xl">
            <p className="px-3 py-2 font-semibold">Perfil del auditor</p>
            <Link href="/admin" className="block rounded-lg px-3 py-2 hover:bg-[#f1eadf]">Administración</Link>
            <button type="button" onClick={() => void logoutSession().finally(() => router.push("/"))} className="block w-full rounded-lg px-3 py-2 text-left hover:bg-[#f1eadf]">Cerrar sesión</button>
          </div> : null}
        </div>
      </header>

      <section className="relative mx-auto flex min-h-[calc(100vh-205px)] max-w-[1120px] flex-col px-8 pb-10 pt-16">
        <div className="mentor-watermark" aria-hidden="true"><span className="material-symbols-outlined">verified_user</span></div>
        <div className="relative z-10 max-w-[900px]">
          <h1 className="mx-auto max-w-[820px] text-center font-headline text-[54px] leading-[0.98] tracking-[-0.035em] text-[#0b2538] md:text-[68px]">¿En qué estás<br />trabajando hoy?</h1>
          <p className="mentor-kicker mt-7 text-center text-[#6f624e]">Elige cómo quieres que te acompañe</p>
        </div>

        <div className="relative z-10 mx-auto mt-5 w-full max-w-[800px]">
          <div className="grid w-full grid-cols-3 overflow-hidden rounded-[10px] border border-[#17384a]" role="group" aria-label="Modo de mentoría">
            {([[
              "teach", "school", "Enséñame", "Explícame una norma o enfoque."
            ], ["help", "explore", "Ayúdame", "Guíame en una tarea o decisión."], ["challenge", "flag", "Desafíame", "Pon a prueba mi criterio."]] as const).map(([value, icon, label]) => <button key={value} type="button" onClick={() => setMentorMode(value)} aria-pressed={mentorMode === value} className={`group relative min-h-[62px] border-x border-[#17384a]/25 px-4 text-center transition first:border-l-0 last:border-r-0 ${mentorMode === value ? "bg-[#0e3044] text-white shadow-[0_10px_24px_rgba(9,34,50,0.16)]" : "text-[#183242] hover:bg-white/40"}`}>
              <span className="flex items-center justify-center gap-3 font-headline text-[21px]"><span className={`material-symbols-outlined text-[22px] ${mentorMode === value ? "text-[#78d4cf]" : "text-[#2f8582]"}`}>{icon}</span>{label}</span>
            </button>)}
          </div>
          <div className="mt-4 flex items-center gap-2 text-xs text-[#55716e]"><span className="material-symbols-outlined text-[17px]">lock</span>Usaré solo las fuentes confirmadas de este cliente.</div>

          {chatNotice ? (
            <div
              className={`mt-6 rounded-[16px] border px-4 py-3 text-sm shadow-sm ${chatNotice.tone === "error" ? "border-red-200 bg-red-50 text-red-900" : "border-[#b9d8d4] bg-[#edf8f6] text-[#245f5d]"}`}
              role={chatNotice.tone === "error" ? "alert" : "status"}
              aria-live={chatNotice.tone === "error" ? "assertive" : "polite"}
            >
              <p className="font-semibold">{chatNotice.title}</p>
              <p className="mt-1 leading-relaxed">{chatNotice.detail}</p>
            </div>
          ) : null}

          {loadingHistory ? (
            <div className="mt-6 rounded-[18px] border border-[#c9bca6]/80 bg-[#fffdf8]/85 p-4 text-sm text-[#6f624e]" role="status" aria-live="polite">
              Cargando historial de la conversación…
            </div>
          ) : null}

          {showThread && messages.length > 0 ? <section data-tour="sociochat-chat" aria-live="polite" aria-relevant="additions text" className="mt-6 max-h-[330px] overflow-y-auto rounded-[18px] border border-[#c9bca6]/80 bg-[#fffdf8]/85 p-5 shadow-[0_12px_30px_rgba(37,45,43,0.07)]">
            <div className="space-y-5">
            {messages.length === 0 ? (
              <div className="rounded-2xl border border-[#041627]/10 bg-white p-5 text-sm text-slate-600">
                <p className="font-headline text-2xl text-[#041627]">Empecemos por tu tarea, no por el módulo.</p>
                <p className="mt-2">Cuéntame qué cuenta, procedimiento, riesgo o decisión estás analizando. Mientras más contexto compartas, mejor podré guiarte.</p>
                <div className="mt-4 flex flex-wrap gap-2">{QUICK_PROMPTS.map((prompt) => <button key={prompt} type="button" onClick={() => setInput(prompt)} className="rounded-full border border-[#177e82]/25 bg-[#edfafa] px-3 py-2 text-xs text-[#155e63] hover:bg-[#d9f3f3]">{prompt}</button>)}</div>
              </div>
            ) : null}
            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[82%] rounded-2xl p-4 ${msg.role === "user" ? "bg-[#eef3fa] rounded-tr-none" : msg.text.startsWith("Error:") ? "rounded-tl-none border border-red-200 bg-red-50 text-red-900 shadow-sm" : "bg-white border border-[#041627]/10 rounded-tl-none shadow-sm"}`}>
                  {msg.role === "assistant" ? (
                    <p className="text-[10px] uppercase tracking-[0.16em] text-teal-700 font-bold mb-2">Criterio Socio AI</p>
                  ) : null}
                  <div className="text-sm leading-relaxed text-slate-800"><ReactMarkdown compact>{msg.text}</ReactMarkdown></div>
                  {msg.role === "assistant" && (msg.mode_used || "").includes("fallback") ? (
                    <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[11px] text-amber-800">
                      Modo respaldo activo. Para respuesta generativa completa, configura la API key del LLM.
                    </div>
                  ) : null}
                  {msg.role === "assistant" && msg.quality_control ? (() => {
                    const withheld = msg.quality_control?.publication === "withheld";
                    const adjusted = Boolean(
                      msg.quality_control?.quality_repair_used
                      || msg.quality_control?.normative_redaction_used
                      || msg.quality_control?.grounding_redaction_used,
                    );
                    const traceFailed = msg.quality_control?.trace_status === "failed";
                    const label = traceFailed
                      ? "Trazabilidad no registrada"
                      : withheld
                        ? "Respuesta retenida por control"
                        : adjusted
                          ? "Verificada con ajustes"
                          : "Control de calidad registrado";
                    const tone = traceFailed
                      ? "border-red-200 bg-red-50 text-red-800"
                      : withheld
                        ? "border-amber-200 bg-amber-50 text-amber-800"
                        : "border-teal-200 bg-teal-50 text-teal-800";
                    return (
                      <div
                        className={`mt-3 inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-bold ${tone}`}
                        title={msg.quality_control.trace_id ? `Traza ${msg.quality_control.trace_id}` : undefined}
                      >
                        <span className="material-symbols-outlined text-[13px]">verified_user</span>
                        {label}
                      </div>
                    );
                  })() : null}
                  {msg.role === "assistant" && msg.quality_control?.trace_id ? (
                    <div className="mt-2 flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() => void handleResponseFeedback(msg, "helpful")}
                        className="rounded-full border border-teal-200 bg-white px-2.5 py-1 text-[10px] font-semibold text-teal-800 hover:bg-teal-50"
                      >
                        Útil
                      </button>
                      <button
                        type="button"
                        onClick={() => void handleResponseFeedback(msg, "incorrect")}
                        className="rounded-full border border-rose-200 bg-white px-2.5 py-1 text-[10px] font-semibold text-rose-700 hover:bg-rose-50"
                      >
                        Reportar respuesta incorrecta
                      </button>
                    </div>
                  ) : null}
                  {msg.role === "assistant" && msg.citations && msg.citations.length > 0 ? (() => {
                    const niaCitations = uniqueCitations(msg.citations).filter(c => c.norma !== "Web");
                    const webCitations = uniqueCitations(msg.citations).filter(c => c.norma === "Web");
                    return (
                      <div className="mt-3 space-y-2">
                        {niaCitations.length > 0 && (
                          <div className="space-y-1">
                            <p className="text-[10px] uppercase tracking-[0.12em] text-slate-500 font-semibold">Fuentes normativas</p>
                            {niaCitations.slice(0, 3).map((c) => (
                              <div key={`${msg.id}-${c.source}`} className="text-[11px] text-slate-500">
                                <p>{prettyRefLabel(c.source)}</p>
                                <p className="text-[10px] text-slate-400">
                                  {c.norma ?? "Norma"} · Vigente: {c.vigente_desde || "N/D"} · Actualizado: {c.ultima_actualizacion || "N/D"}
                                </p>
                              </div>
                            ))}
                          </div>
                        )}
                        {webCitations.length > 0 && (
                          <div className="rounded-lg bg-blue-50 border border-blue-200 px-3 py-2 space-y-1">
                            <div className="flex items-center gap-1.5 mb-1">
                              <span className="material-symbols-outlined text-blue-600 text-sm">language</span>
                              <p className="text-[10px] uppercase tracking-[0.12em] text-blue-700 font-bold">Fuentes web</p>
                            </div>
                            {webCitations.slice(0, 3).map((c) => (
                              <div key={`${msg.id}-${c.source}`} className="text-[11px]">
                                <a
                                  href={c.source}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-blue-700 underline underline-offset-2 font-medium hover:text-blue-900"
                                >
                                  {c.title || prettyRefLabel(c.source)}
                                </a>
                                {c.excerpt && (
                                  <p className="text-[10px] text-blue-600/70 mt-0.5 line-clamp-2">{c.excerpt}</p>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })() : null}
                  {msg.role === "assistant" && typeof msg.confidence === "number" ? (
                    <div className="flex items-center gap-2 mt-2 flex-wrap">
                      <p className="text-[10px] text-slate-500">
                        Confianza: {(msg.confidence * 100).toFixed(0)}%
                        {msg.mode_used ? ` · modo: ${msg.mode_used}` : ""}
                      </p>
                      {msg.web_search_used && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 text-[10px] font-bold">
                          <span className="material-symbols-outlined text-[11px]">language</span>
                          Búsqueda web activa
                        </span>
                      )}
                      {msg.expert_criteria_used && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#a5eff0]/25 text-[#002f30] text-[10px] font-bold border border-[#89d3d4]/60">
                          <span className="material-symbols-outlined text-[11px]">history_edu</span>
                          Criterio Experto
                        </span>
                      )}
                    </div>
                  ) : null}
                  <p className="text-[10px] text-slate-400 mt-2 uppercase tracking-[0.12em]">{msg.timestamp}</p>
                </div>
              </div>
            ))}
            </div>
          </section> : null}

          <div data-tour="sociochat-input" className="mt-6">
            <form onSubmit={handleSend} className="mentor-composer flex items-end gap-3 rounded-[16px] border border-[#bcae96] bg-[#fffefa]/90 p-3 shadow-[0_16px_36px_rgba(45,44,36,0.08)]">
              <input
                ref={sourceInputRef}
                type="file"
                accept=".pdf,.docx,.xlsx,.txt,.md,.csv"
                className="sr-only"
                onChange={(event) => void handleSourceSelected(event)}
                aria-label="Seleccionar fuente para el Mentor"
              />
              <button
                type="button"
                disabled={uploadingSource}
                onClick={() => sourceInputRef.current?.click()}
                className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-[#55716e] hover:bg-[#eee7da] disabled:opacity-40"
                aria-label={uploadingSource ? "Procesando fuente" : "Adjuntar fuente"}
                title="Adjuntar PDF, DOCX, XLSX, TXT, MD o CSV como fuente de contexto"
              >
                <span className="material-symbols-outlined">{uploadingSource ? "progress_activity" : "attach_file"}</span>
              </button>
              <textarea
                aria-label="Mensaje para Socio AI"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                className="w-full min-h-[88px] max-h-40 resize-none border-none bg-transparent px-2 py-3 text-sm outline-none focus:ring-0"
                placeholder="Cuéntame tu situación, pregunta o el criterio que quieres aplicar…"
              />
              <button
                type="submit"
                disabled={sending || !input.trim()}
                className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-[#2f8582] text-white shadow-sm transition hover:bg-[#246f6d] disabled:opacity-40"
              >
                <span className="material-symbols-outlined">send</span>
              </button>
            </form>
            {attachedSourceName ? (
              <p className="mt-2 flex items-center gap-1.5 text-xs text-[#2b7774]" role="status">
                <span className="material-symbols-outlined text-[15px]">description</span>
                Fuente incorporada: {attachedSourceName}
              </p>
            ) : null}
            {sending ? (
              <p className="mt-3 text-xs uppercase tracking-[0.12em] text-[#6f624e]" role="status" aria-live="polite">
                Enviando mensaje al Mentor…
              </p>
            ) : null}
            {messages.some((message) => message.role === "assistant") ? (
              <button type="button" onClick={() => void handleSessionEvaluation()} className="mt-3 text-xs font-semibold text-[#2b7774] underline underline-offset-4">
                Cerrar y evaluar esta sesión Alpha
              </button>
            ) : null}
          </div>

          <div className="mt-10 grid gap-8 border-t border-[#c9bca6]/70 pt-6 md:grid-cols-2">
            <article>
              <div className="flex items-center justify-between"><h2 className="mentor-kicker">Conversación reciente</h2><button type="button" onClick={() => void handleNewConversation()} className="text-xs text-[#2b7774] hover:underline">Nueva conversación</button></div>
              {loadingConversations ? <p className="mt-4 text-sm text-[#7a8388]" role="status" aria-live="polite">Cargando conversaciones guardadas…</p> : null}
              {recentConversation ? <div className="group mt-4 flex items-start gap-3"><span className="material-symbols-outlined mt-0.5 text-[20px] text-[#9a7b52]">chat_bubble</span><button type="button" onClick={() => { setActiveConversationId(recentConversation.id); setShowThread(true); }} className="min-w-0 flex-1 text-left"><p className="truncate font-headline text-lg">{recentConversation.title}</p><p className="mt-1 text-xs text-[#7a8388]">Actualizada {new Date(recentConversation.updated_at).toLocaleDateString()}</p></button><button type="button" onClick={() => void handleRenameConversation(recentConversation)} className={conversationActionClass} aria-label="Renombrar conversación"><span className="material-symbols-outlined text-[18px]">edit</span></button><button type="button" onClick={() => void handleDeleteConversation(recentConversation)} className={conversationActionClass} aria-label="Eliminar conversación"><span className="material-symbols-outlined text-[18px]">delete</span></button></div> : <p className="mt-4 text-sm text-[#7a8388]">Aún no hay conversaciones.</p>}
            </article>
            <article>
              <h2 className="mentor-kicker">Área sugerida</h2>
              <Link href={suggestedAreaHref} className="mt-4 flex w-full items-start gap-3 text-left"><span className="material-symbols-outlined mt-0.5 text-[20px] text-[#2f8582]">track_changes</span><span><span className="block font-headline text-lg">{suggestedRisk?.area_nombre || "Comprensión del cliente"}</span><span className="mt-1 block text-xs text-[#7a8388]">{suggestedRisk ? `Prioridad ${suggestedRisk.nivel.toLowerCase()} · abrir área para revisarla.` : "Abre el perfil y empieza por una cuenta, procedimiento o decisión concreta."}</span></span></Link>
            </article>
          </div>
          {role === "junior" || role === "socio" ? <p className="mt-6 text-[11px] text-[#7d8587]">Vista adaptada al nivel {role === "junior" ? "Junior" : "Socio"}; el nivel cambia la forma de acompañarte, no tus permisos ni el criterio requerido.</p> : null}
        </div>
      </section>
    </main>
  );
}
