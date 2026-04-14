"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import ContextualHelp from "../../../components/help/ContextualHelp";
import { exportChatCriterion, getChatHistory, postChat } from "../../../lib/api";
import { createWorkpaperTask } from "../../../lib/api/workpapers";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import { useDashboard } from "../../../lib/hooks/useDashboard";
import { useLearningRole } from "../../../lib/hooks/useLearningRole";
import { useRiskEngine } from "../../../lib/hooks/useRiskEngine";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  timestamp: string;
  citations?: Array<{
    source: string;
    excerpt: string;
    norma?: string;
    version?: string;
    vigente_desde?: string;
    ultima_actualizacion?: string;
    jurisdiccion?: string;
  }>;
  confidence?: number;
  mode_used?: string;
};

type HistoryMessage = {
  role?: "user" | "assistant" | string;
  text?: string;
  timestamp?: string;
  citations?: ChatMessage["citations"];
  confidence?: number;
};

const QUICK_PROMPTS = [
  "¿Qué norma NIIF o NIA aplica para este caso y por qué?",
  "Analiza este hallazgo y sugiere procedimientos de auditoría.",
  "Redacta un párrafo técnico para el informe final de auditoría.",
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

export default function SocioChatPage() {
  const { clienteId } = useAuditContext();
  const { role } = useLearningRole();
  const { data: dashboard, isLoading: dashboardLoading, error: dashboardError } = useDashboard(clienteId);
  const { data: riskData } = useRiskEngine(clienteId);

  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [actionMsg, setActionMsg] = useState("");

  useEffect(() => {
    let active = true;
    async function loadHistory(): Promise<void> {
      try {
        const response = await getChatHistory(clienteId);
        if (!active) return;
        const raw: HistoryMessage[] = Array.isArray(response?.data?.messages)
          ? (response.data.messages as HistoryMessage[])
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
          }));
        setMessages(mapped.slice(-120));
      } catch {
        if (!active) return;
      }
    }
    if (clienteId) void loadHistory();
    return () => {
      active = false;
    };
  }, [clienteId]);

  const openRisks = useMemo(() => riskData?.areas_criticas?.slice(0, 2) ?? [], [riskData]);
  const recentThreads = useMemo(
    () => {
      const userMsgs = messages.filter((m) => m.role === "user").slice(-6).reverse();
      return userMsgs.slice(0, 3).map((m) => ({
        title: m.text.length > 55 ? `${m.text.slice(0, 55)}...` : m.text,
        subtitle: "Consulta del usuario",
        period: m.timestamp,
      }));
    },
    [messages],
  );

  const references = useMemo(() => {
    const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");
    if (lastAssistant?.citations?.length) {
      const unique = new Map<string, string>();
      for (const c of lastAssistant.citations) {
        const source = normalizeRefPath(c.source || "");
        if (!source || unique.has(source)) continue;
        const label = c.norma ? `${c.norma} · ${prettyRefLabel(source)}` : prettyRefLabel(source);
        unique.set(source, label);
      }
      if (unique.size > 0) {
        return Array.from(unique.entries()).map(([source, label]) => ({ source, label }));
      }
    }
    return [];
  }, [messages]);

  const lastAssistantMessage = useMemo(
    () => [...messages].reverse().find((m) => m.role === "assistant") ?? null,
    [messages],
  );

  async function handleSend(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const prompt = input.trim();
    if (!prompt || sending) return;

    const userMessage: ChatMessage = {
      id: `u-${Date.now()}`,
      role: "user",
      timestamp: nowLabel(),
      text: prompt,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setSending(true);

    try {
      const response = await postChat(clienteId, { message: prompt });
      const answer = response?.data?.answer || "No hubo respuesta del asistente.";
      const assistantMessage: ChatMessage = {
        id: `a-${Date.now()}`,
        role: "assistant",
        timestamp: nowLabel(),
        text: answer,
        citations: normalizeChatCitations(response?.data?.citations),
        confidence: response?.data?.confidence ?? 0,
        mode_used: response?.data?.mode_used ?? "chat",
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "No se pudo consultar al asistente.";
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

  async function handleLinkToWorkpaper(): Promise<void> {
    if (!lastAssistantMessage) {
      setActionMsg("No hay criterio generado para vincular.");
      return;
    }
    const top = dashboard?.top_areas?.[0];
    if (!top) {
      setActionMsg("No hay área priorizada para crear tarea.");
      return;
    }
    const areaCode = String(top.codigo || "").trim();
    const areaName = String(top.nombre || "").trim();
    const prioridad = String(top.prioridad || "media").trim().toLowerCase() || "media";
    if (!areaCode || !areaName) {
      setActionMsg("No hay datos válidos del área priorizada para crear la tarea.");
      return;
    }
    const title = `Criterio Socio Chat: ${lastAssistantMessage.text.slice(0, 60)}${lastAssistantMessage.text.length > 60 ? "..." : ""}`;
    try {
      const result = await createWorkpaperTask(clienteId, {
        area_code: areaCode,
        area_name: areaName,
        title,
        nia_ref: "NIA 500",
        prioridad,
        required: true,
        evidence_note: "",
      });
      setActionMsg(result.created ? "Tarea creada en Papeles de Trabajo." : "La tarea ya existía en Papeles.");
    } catch (err) {
      setActionMsg(err instanceof Error ? err.message : "No se pudo vincular a papeles.");
    }
  }

  async function handleExportCriterion(): Promise<void> {
    if (!lastAssistantMessage) {
      setActionMsg("No hay respuesta para exportar.");
      return;
    }
    try {
      await exportChatCriterion(clienteId, {
        title: "Criterio exportado desde Socio Chat",
        content: lastAssistantMessage.text,
      });
      setActionMsg("Criterio exportado y guardado en hallazgos.");
    } catch (err) {
      setActionMsg(err instanceof Error ? err.message : "No se pudo exportar criterio.");
    }
  }

  if (dashboardLoading) return <DashboardSkeleton />;
  if (dashboardError) return <ErrorMessage message={dashboardError} />;
  if (!dashboard) return <ErrorMessage message="No hay contexto del cliente para Socio Chat." />;

  return (
    <div className="pt-4 pb-8 h-[calc(100vh-7rem)]">
      <ContextualHelp
        title="Ayuda del módulo Socio Chat"
        compact
        items={[
          {
            label: "Consulta técnica",
            description:
              "Pregunta normativa o de procedimiento y revisa fuentes antes de aplicar criterio.",
          },
          {
            label: "Exportar criterio",
            description:
              "Guarda la respuesta útil en hallazgos para mantener evidencia del razonamiento.",
          },
          {
            label: "Vincular a papel",
            description:
              "Convierte una recomendación en tarea ejecutable dentro de Papeles de Trabajo.",
          },
        ]}
      />
      {/* Panel de rol — compacto para no reducir el espacio del chat */}
      {role === "junior" && (
        <div className="bg-[#a5eff0]/10 border border-[#a5eff0]/30 rounded-xl px-5 py-4 flex flex-col md:flex-row md:items-start gap-4">
          <div className="flex items-center gap-2 shrink-0">
            <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-[#041627] text-[#a5eff0] text-[10px] font-bold">NIA</span>
            <p className="text-xs uppercase tracking-[0.14em] text-[#041627]/60 font-bold">Vista Junior — Preguntas sugeridas</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {[
              "¿Qué procedimientos debo aplicar en CxC?",
              "¿Cómo evalúo el riesgo de going concern?",
              "¿Qué es la materialidad de ejecución?",
              "¿Qué aseveraciones cubre una confirmación bancaria?",
              "¿Cuándo aplica NIA 540 en estimaciones contables?",
              "¿Cómo estructuro un hallazgo correctamente?",
            ].map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => setInput(q)}
                className="px-3 py-1.5 rounded-full bg-white border border-[#041627]/15 text-xs text-[#041627] font-medium hover:bg-[#041627] hover:text-white transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {role === "socio" && (
        <div className="bg-[#001919] border border-[#a5eff0]/20 rounded-xl px-5 py-4 flex items-center gap-4 text-white">
          <span className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#a5eff0]/20 text-[#a5eff0] text-[10px] font-bold">AI</span>
          <p className="text-xs text-slate-300 leading-relaxed">
            <span className="font-semibold text-white">Modo Socio:</span> el chat responde con criterio ejecutivo — riesgo de emisión, materialidad y enfoque estratégico.
            Pregunta por áreas críticas, hallazgos relevantes o si el encargo está listo para emitir opinión.
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-[280px_1fr_320px] gap-6 h-full">
        <aside data-tour="sociochat-conversaciones" className="sovereign-card !p-4 flex flex-col overflow-hidden">
          <div className="flex items-center justify-between px-2 mb-4">
            <h3 className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">Conversaciones</h3>
            <span className="material-symbols-outlined text-slate-400">edit_square</span>
          </div>
          <div className="space-y-2 overflow-y-auto pr-1">
            {recentThreads.map((thread, idx) => (
              <button
                type="button"
                key={`${thread.title}-${idx}`}
                className={`w-full text-left p-3 rounded-xl transition-colors ${idx === 0 ? "bg-white border border-[#041627]/10 shadow-sm" : "hover:bg-[#f1f4f6]"}`}
              >
                <p className="text-[9px] uppercase tracking-[0.15em] text-slate-400 font-bold mb-1">{thread.period}</p>
                <p className="text-sm font-semibold text-[#041627]">{thread.title}</p>
                <p className="text-[11px] text-slate-500 mt-1">{thread.subtitle}</p>
              </button>
            ))}
            {recentThreads.length === 0 ? (
              <p className="text-xs text-slate-500 px-2">No hay conversaciones recientes para este cliente.</p>
            ) : null}
          </div>
        </aside>

        <section data-tour="sociochat-chat" className="sovereign-card !p-0 overflow-hidden flex flex-col">
          <div className="px-6 py-4 bg-[#f1f4f6]/60 border-b border-black/5 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse" />
              <span className="text-xs uppercase tracking-[0.15em] text-slate-500 font-bold">Sesión activa</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => void handleLinkToWorkpaper()}
                className="text-[10px] uppercase tracking-[0.12em] px-3 py-1.5 rounded-full bg-white border border-black/10 text-slate-600"
              >
                Vincular a papel
              </button>
              <button
                type="button"
                onClick={() => void handleExportCriterion()}
                className="text-[10px] uppercase tracking-[0.12em] px-3 py-1.5 rounded-full text-white bg-[#041627]"
              >
                Exportar criterio
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-gradient-to-b from-white to-[#f8fbff]">
            {messages.length === 0 ? (
              <div className="rounded-2xl border border-[#041627]/10 bg-white p-5 text-sm text-slate-600">
                Socio AI listo. Escribe una consulta técnica (NIA/NIIF, procedimientos, hallazgos o conclusión) y te
                responderé con criterio y fuentes.
              </div>
            ) : null}
            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[82%] rounded-2xl p-4 ${msg.role === "user" ? "bg-[#eef3fa] rounded-tr-none" : "bg-white border border-[#041627]/10 rounded-tl-none shadow-sm"}`}>
                  {msg.role === "assistant" ? (
                    <p className="text-[10px] uppercase tracking-[0.16em] text-teal-700 font-bold mb-2">Criterio Socio AI</p>
                  ) : null}
                  <p className="text-sm leading-relaxed text-slate-800 whitespace-pre-wrap">{msg.text}</p>
                  {msg.role === "assistant" && (msg.mode_used || "").includes("fallback") ? (
                    <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[11px] text-amber-800">
                      Modo respaldo activo. Para respuesta generativa completa, configura la API key del LLM.
                    </div>
                  ) : null}
                  {msg.role === "assistant" && msg.citations && msg.citations.length > 0 ? (
                    <div className="mt-3 space-y-1">
                      <p className="text-[10px] uppercase tracking-[0.12em] text-slate-500 font-semibold">Fuentes</p>
                      {uniqueCitations(msg.citations).slice(0, 3).map((c) => (
                        <div key={`${msg.id}-${c.source}`} className="text-[11px] text-slate-500">
                          <p>{prettyRefLabel(c.source)}</p>
                          <p className="text-[10px] text-slate-400">
                            {c.norma ? `${c.norma}` : "Norma"} · Vigente: {c.vigente_desde || "N/D"} · Actualizado: {c.ultima_actualizacion || "N/D"}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : null}
                  {msg.role === "assistant" && typeof msg.confidence === "number" ? (
                    <p className="text-[10px] text-slate-500 mt-2">
                      Confianza: {(msg.confidence * 100).toFixed(0)}%
                      {msg.mode_used ? ` · modo: ${msg.mode_used}` : ""}
                    </p>
                  ) : null}
                  <p className="text-[10px] text-slate-400 mt-2 uppercase tracking-[0.12em]">{msg.timestamp}</p>
                </div>
              </div>
            ))}
          </div>

          <div data-tour="sociochat-input" className="p-5 bg-[#f1f4f6]/35 border-t border-black/5">
            {actionMsg ? <p className="text-xs text-slate-600 mb-3">{actionMsg}</p> : null}
            <div className="flex gap-2 mb-3 overflow-x-auto">
              {QUICK_PROMPTS.map((q) => (
                <button
                  key={q}
                  type="button"
                  onClick={() => setInput(q)}
                  className="shrink-0 px-3 py-2 rounded-xl bg-white border border-black/10 text-xs text-slate-600 hover:border-teal-500"
                >
                  {q}
                </button>
              ))}
            </div>
            <form onSubmit={handleSend} className="flex items-end gap-2 bg-white rounded-2xl p-2 border border-[#041627]/10 shadow-sm">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                className="w-full min-h-[54px] max-h-32 resize-none border-none focus:ring-0 outline-none px-2 py-2 text-sm"
                placeholder="Escribe tu consulta técnica aquí..."
              />
              <button
                type="submit"
                disabled={sending || !input.trim()}
                className="p-3 rounded-xl text-white bg-[#041627] disabled:opacity-50"
              >
                <span className="material-symbols-outlined">send</span>
              </button>
            </form>
          </div>
        </section>

        <aside className="space-y-6 overflow-y-auto pr-1">
          <article className="rounded-editorial p-6 text-white" style={{ background: "linear-gradient(135deg, #041627 0%, #1a2b3c 100%)" }}>
            <h3 className="text-xs uppercase tracking-[0.18em] text-[#89d3d4] font-bold">Contexto</h3>
            <p className="font-headline text-2xl mt-3">{dashboard.nombre_cliente}</p>
            <div className="mt-5 grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-slate-300 text-[10px] uppercase tracking-[0.14em]">Materialidad</p>
                <p className="font-headline text-xl">${(dashboard.materialidad_global / 1000000).toFixed(1)}M</p>
              </div>
              <div>
                <p className="text-slate-300 text-[10px] uppercase tracking-[0.14em]">Riesgo Global</p>
                <p className="font-headline text-xl text-[#a5eff0]">{dashboard.riesgo_global}</p>
              </div>
            </div>
          </article>

          <article data-tour="sociochat-referencias" className="sovereign-card">
            <h4 className="text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-4">Alertas de riesgo</h4>
            <div className="space-y-3">
              {openRisks.map((risk) => (
                <div key={risk.area_id} className="p-3 rounded-xl bg-[#f8fafc] border border-black/10">
                  <p className="text-sm font-semibold text-[#041627]">{risk.area_nombre}</p>
                  <p className="text-[11px] text-slate-500 mt-1">Score: {risk.score.toFixed(2)} · {risk.nivel}</p>
                </div>
              ))}
              {openRisks.length === 0 ? <p className="text-sm text-slate-500">Sin alertas abiertas.</p> : null}
            </div>
          </article>

          <article className="sovereign-card">
            <h4 className="text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-4">Referencias técnicas</h4>
            <ul className="space-y-2">
              {references.map((ref) => (
                <li key={ref.source} className="p-3 rounded-xl bg-white border border-black/10 text-xs text-slate-700">
                  <p className="font-semibold">{ref.label}</p>
                  <p className="text-[10px] text-slate-500 mt-1">{ref.source}</p>
                </li>
              ))}
              {references.length === 0 ? (
                <li className="p-3 rounded-xl bg-white border border-black/10 text-xs text-slate-500">
                  Sin referencias técnicas en la última respuesta.
                </li>
              ) : null}
            </ul>
          </article>
        </aside>
      </div>
    </div>
  );
}
