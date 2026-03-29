"use client";

import { FormEvent, useMemo, useState } from "react";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import { exportChatCriterion, postChat } from "../../../lib/api";
import { createWorkpaperTask } from "../../../lib/api/workpapers";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import { useDashboard } from "../../../lib/hooks/useDashboard";
import { useRiskEngine } from "../../../lib/hooks/useRiskEngine";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  timestamp: string;
  citations?: Array<{ source: string; excerpt: string }>;
  confidence?: number;
};

const QUICK_PROMPTS = [
  "Pregunta sobre normativa NIIF...",
  "Analiza este hallazgo...",
  "Redacta un parrafo para informe...",
];

function nowLabel(): string {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function SocioChatPage() {
  const { clienteId } = useAuditContext();
  const { data: dashboard, isLoading: dashboardLoading, error: dashboardError } = useDashboard(clienteId);
  const { data: riskData } = useRiskEngine(clienteId);

  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [actionMsg, setActionMsg] = useState("");

  const openRisks = useMemo(() => riskData?.areas_criticas?.slice(0, 2) ?? [], [riskData]);
  const recentThreads = useMemo(
    () => {
      const periodLabel = dashboard?.periodo ? `Periodo ${dashboard.periodo}` : "Periodo actual";
      return (dashboard?.top_areas ?? [])
        .filter((item) => item.con_saldo)
        .slice(0, 3)
        .map((item) => ({
          title: `Analisis de area ${item.codigo}`,
          subtitle: item.nombre,
          period: periodLabel,
        }));
    },
    [dashboard],
  );

  const references = useMemo(() => {
    const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");
    if (lastAssistant?.citations?.length) {
      return lastAssistant.citations.map((c) => c.source);
    }
    return ["NIA 315 - Valoracion de riesgos.", "NIA 330 - Respuestas del auditor."];
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
        citations: response?.data?.citations ?? [],
        confidence: response?.data?.confidence ?? 0,
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
      setActionMsg("No hay area priorizada para crear tarea.");
      return;
    }
    const title = `Criterio Socio Chat: ${lastAssistantMessage.text.slice(0, 60)}${lastAssistantMessage.text.length > 60 ? "..." : ""}`;
    try {
      const result = await createWorkpaperTask(clienteId, {
        area_code: top.codigo,
        area_name: top.nombre,
        title,
        nia_ref: "NIA 500",
        prioridad: top.prioridad,
        required: true,
        evidence_note: "",
      });
      setActionMsg(result.created ? "Tarea creada en Papeles de Trabajo." : "La tarea ya existia en Papeles.");
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
      <div className="grid grid-cols-1 xl:grid-cols-[280px_1fr_320px] gap-6 h-full">
        <aside className="sovereign-card !p-4 flex flex-col overflow-hidden">
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

        <section className="sovereign-card !p-0 overflow-hidden flex flex-col">
          <div className="px-6 py-4 bg-[#f1f4f6]/60 border-b border-black/5 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse" />
              <span className="text-xs uppercase tracking-[0.15em] text-slate-500 font-bold">Sesion activa</span>
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
            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[82%] rounded-2xl p-4 ${msg.role === "user" ? "bg-[#eef3fa] rounded-tr-none" : "bg-white border border-[#041627]/10 rounded-tl-none shadow-sm"}`}>
                  {msg.role === "assistant" ? (
                    <p className="text-[10px] uppercase tracking-[0.16em] text-teal-700 font-bold mb-2">Criterio Socio AI</p>
                  ) : null}
                  <p className="text-sm leading-relaxed text-slate-800 whitespace-pre-wrap">{msg.text}</p>
                  {msg.role === "assistant" && msg.citations && msg.citations.length > 0 ? (
                    <div className="mt-3 space-y-1">
                      <p className="text-[10px] uppercase tracking-[0.12em] text-slate-500 font-semibold">Fuentes</p>
                      {msg.citations.slice(0, 2).map((c) => (
                        <p key={`${msg.id}-${c.source}`} className="text-[11px] text-slate-500">
                          {c.source}
                        </p>
                      ))}
                    </div>
                  ) : null}
                  {msg.role === "assistant" && typeof msg.confidence === "number" ? (
                    <p className="text-[10px] text-slate-500 mt-2">Confianza: {(msg.confidence * 100).toFixed(0)}%</p>
                  ) : null}
                  <p className="text-[10px] text-slate-400 mt-2 uppercase tracking-[0.12em]">{msg.timestamp}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="p-5 bg-[#f1f4f6]/35 border-t border-black/5">
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
                placeholder="Escribe tu consulta tecnica aqui..."
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

          <article className="sovereign-card">
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
            <h4 className="text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-4">Referencias tecnicas</h4>
            <ul className="space-y-2">
              {references.map((ref) => (
                <li key={ref} className="p-3 rounded-xl bg-white border border-black/10 text-xs text-slate-700">
                  {ref}
                </li>
              ))}
            </ul>
          </article>
        </aside>
      </div>
    </div>
  );
}
