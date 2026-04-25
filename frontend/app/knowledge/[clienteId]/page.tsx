"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import { askKnowledge, getKnowledgeEntities, getKnowledgeGraph, getKnowledgeTimeline } from "../../../lib/api/knowledge";
import { getDashboardData } from "../../../lib/api/dashboard";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import type {
  KnowledgeAskResponse,
  KnowledgeEntitiesResponse,
  KnowledgeGraphResponse,
  KnowledgeTimelineResponse,
} from "../../../types/knowledge";

const DEFAULT_PAGE_SIZE = 200;

const EMPTY_ENTITIES: KnowledgeEntitiesResponse = {
  items: [],
  total: 0,
  page: 1,
  page_size: DEFAULT_PAGE_SIZE,
  total_pages: 1,
};

export default function KnowledgePage() {
  const { clienteId } = useAuditContext();
  const searchParams = useSearchParams();
  const debugMode = searchParams?.get("debug") === "1";

  const [entities, setEntities] = useState<KnowledgeEntitiesResponse>(EMPTY_ENTITIES);
  const [graph, setGraph] = useState<KnowledgeGraphResponse | null>(null);
  const [timeline, setTimeline] = useState<KnowledgeTimelineResponse | null>(null);
  const [clienteNombre, setClienteNombre] = useState<string>("");
  const [askResponse, setAskResponse] = useState<KnowledgeAskResponse | null>(null);
  const [query, setQuery] = useState<string>("");
  const [search, setSearch] = useState<string>("");
  const [expandedIds, setExpandedIds] = useState<Record<number, boolean>>({});
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [isAsking, setIsAsking] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [isDisabled, setIsDisabled] = useState<boolean>(false);

  const loadEntities = useCallback(async () => {
    if (!clienteId) return;
    const response = await getKnowledgeEntities(clienteId, {
      page_size: DEFAULT_PAGE_SIZE,
      q: search || undefined,
    });
    setEntities(response);
  }, [clienteId, search]);

  const loadGraph = useCallback(async () => {
    if (!clienteId) return;
    const response = await getKnowledgeGraph(clienteId);
    setGraph(response);
  }, [clienteId]);

  const loadTimeline = useCallback(async () => {
    if (!clienteId) return;
    const response = await getKnowledgeTimeline(clienteId);
    setTimeline(response);
  }, [clienteId]);

  const loadCliente = useCallback(async () => {
    if (!clienteId) return;
    try {
      const dashboard = await getDashboardData(clienteId);
      setClienteNombre(dashboard.nombre_cliente || clienteId);
    } catch {
      setClienteNombre(clienteId);
    }
  }, [clienteId]);

  useEffect(() => {
    let mounted = true;
    const run = async () => {
      if (!clienteId) return;
      setIsLoading(true);
      setError("");
      setIsDisabled(false);
      try {
        await Promise.all([loadEntities(), loadGraph(), loadTimeline(), loadCliente()]);
      } catch (err) {
        if (!mounted) return;
        const message = err instanceof Error ? err.message : "No se pudo cargar Memoria del Cliente.";
        if (message.includes("KNOWLEDGE_CORE_DISABLED")) {
          setIsDisabled(true);
        } else {
          setError(message);
        }
      } finally {
        if (mounted) setIsLoading(false);
      }
    };
    void run();
    return () => {
      mounted = false;
    };
  }, [clienteId, loadCliente, loadEntities, loadGraph, loadTimeline]);

  useEffect(() => {
    if (!clienteId) return;
    const run = async () => {
      setIsRefreshing(true);
      setError("");
      try {
        await Promise.all([
          loadEntities(),
          !graph ? loadGraph() : Promise.resolve(),
          !timeline ? loadTimeline() : Promise.resolve(),
        ]);
      } catch (err) {
        const message = err instanceof Error ? err.message : "No se pudo actualizar la memoria.";
        if (message.includes("KNOWLEDGE_CORE_DISABLED")) {
          setIsDisabled(true);
        } else {
          setError(message);
        }
      } finally {
        setIsRefreshing(false);
      }
    };
    void run();
  }, [clienteId, graph, loadEntities, loadGraph, loadTimeline, timeline]);

  const handleAsk = async () => {
    if (!clienteId || !query.trim()) return;
    setIsAsking(true);
    setError("");
    try {
      const response = await askKnowledge(clienteId, { query: query.trim(), top_k: 5 });
      setAskResponse(response);
    } catch (err) {
      const message = err instanceof Error ? err.message : "No se pudo ejecutar la consulta.";
      if (message.includes("KNOWLEDGE_CORE_DISABLED")) {
        setIsDisabled(true);
      } else {
        setError(message);
      }
    } finally {
      setIsAsking(false);
    }
  };

  const findings = useMemo(
    () => entities.items.filter((item) => item.entity_type === "finding"),
    [entities.items],
  );

  const nodeMap = useMemo(() => {
    const map = new Map<number, { title: string; entity_type: string }>();
    for (const node of graph?.nodes ?? []) {
      map.set(node.id, { title: node.title || `Entidad ${node.id}`, entity_type: node.entity_type });
    }
    return map;
  }, [graph?.nodes]);

  const latestUpdated = useMemo(() => {
    const candidates = entities.items.map((x) => x.updated_at).filter(Boolean);
    if (candidates.length === 0) return "";
    const sorted = [...candidates].sort((a, b) => (a > b ? -1 : 1));
    return sorted[0];
  }, [entities.items]);

  const evidenciasCount = useMemo(
    () => entities.items.filter((x) => x.entity_type === "evidence" || x.entity_type === "working_paper").length,
    [entities.items],
  );

  const humanDate = (iso: string): string => {
    if (!iso) return "-";
    const dt = new Date(iso);
    if (Number.isNaN(dt.getTime())) return "-";
    return dt.toLocaleString("es-CO");
  };

  const relationText = (relation: KnowledgeGraphResponse["edges"][number]): string => {
    const from = nodeMap.get(relation.from_entity_id);
    const to = nodeMap.get(relation.to_entity_id);
    const fromTitle = from?.title || `Entidad ${relation.from_entity_id}`;
    const toTitle = to?.title || `Entidad ${relation.to_entity_id}`;
    if (relation.relation_type === "belongs_to" && (to?.entity_type === "client" || toTitle.toLowerCase().includes("cliente"))) {
      return `El hallazgo "${fromTitle}" pertenece al cliente "${toTitle}".`;
    }
    if (relation.relation_type === "belongs_to" && to?.entity_type === "note") {
      return `El hallazgo "${fromTitle}" pertenece al periodo "${toTitle}".`;
    }
    if (relation.relation_type === "supports") {
      return `La evidencia "${fromTitle}" soporta el hallazgo "${toTitle}".`;
    }
    if (relation.relation_type === "impacts") {
      return `El hallazgo "${fromTitle}" impacta "${toTitle}".`;
    }
    return `"${fromTitle}" se relaciona con "${toTitle}" (${relation.relation_type}).`;
  };

  const eventLabel = (eventType: string): string => {
    if (eventType === "entity_created") return "Se creo";
    if (eventType === "entity_updated") return "Se actualizo";
    if (eventType === "relation_created") return "Se vinculo";
    if (eventType === "relation_updated") return "Se actualizo el vinculo";
    if (eventType === "ask_query") return "Se consulto la memoria";
    return eventType;
  };

  const translatedTitle = (title: string): string => {
    const raw = String(title || "");
    if (!raw) return "Hallazgo sin titulo";
    return raw.replace(/^Mayor:\s*/i, "Mayor · ");
  };

  if (isLoading) return <DashboardSkeleton />;
  if (isDisabled) {
    return (
      <div className="pt-4 pb-10 space-y-6 max-w-[1200px]">
        <section className="space-y-2">
          <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">Knowledge Core</p>
          <h1 className="font-headline text-5xl text-[#041627]">Nucleo Inteligente</h1>
        </section>
        <section className="sovereign-card p-6 border border-amber-300 bg-amber-50">
          <h2 className="font-headline text-2xl text-amber-900">Knowledge Core deshabilitado</h2>
          <p className="text-sm text-amber-800 mt-2">
            Este modulo esta disponible, pero el backend lo tiene apagado en este entorno.
          </p>
          <p className="text-xs text-amber-700 mt-3">
            Accion requerida en despliegue: definir <code>KNOWLEDGE_CORE_ENABLED=1</code> y reiniciar backend.
          </p>
        </section>
      </div>
    );
  }
  if (error && !isRefreshing) return <ErrorMessage message={error} />;

  return (
    <div className="pt-4 pb-10 space-y-6 max-w-[1400px]">
      <section className="space-y-2">
        <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">Memoria del Cliente</p>
        <h1 className="font-headline text-5xl text-[#041627]">Memoria del Cliente</h1>
        <p className="text-sm text-slate-500">
          {clienteNombre || clienteId} · Hallazgos {findings.length} · Evidencias/Relaciones {evidenciasCount}/{graph?.meta.total_edges ?? 0} · Ultima actualizacion{" "}
          <span className="font-semibold text-slate-700">{humanDate(latestUpdated)}</span>
        </p>
      </section>

      <section className="sovereign-card p-5 space-y-4">
        <div className="flex flex-col sm:flex-row gap-2">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar hallazgos por titulo o contenido..."
            className="w-full sm:max-w-md rounded-editorial border border-[#041627]/15 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#14b8a6] min-h-[44px]"
          />
          <button
            type="button"
            className="rounded-editorial px-4 py-2 text-xs uppercase tracking-[0.12em] font-bold text-white bg-[#0d9488] hover:bg-[#0b7e72] min-h-[44px]"
            onClick={() => void loadEntities()}
          >
            Buscar
          </button>
        </div>
        <h2 className="font-headline text-2xl text-[#041627]">Hallazgos detectados</h2>
        {findings.length === 0 ? (
          <p className="text-sm text-slate-500">Aun no hay hallazgos registrados para este cliente.</p>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {findings.map((item) => {
              const meta = item.metadata || {};
              const severity = typeof meta.severity === "string" ? meta.severity : "";
              const metrics = meta.metrics && typeof meta.metrics === "object" ? (meta.metrics as Record<string, unknown>) : {};
              return (
                <article key={item.id} className="rounded-editorial border border-[#041627]/10 p-4 bg-white space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="text-base font-semibold text-[#041627]">{translatedTitle(item.title)}</h3>
                    {severity ? (
                      <span className="text-[10px] uppercase tracking-[0.1em] rounded px-2 py-1 bg-amber-100 text-amber-900">
                        {severity}
                      </span>
                    ) : null}
                  </div>
                  <p className="text-xs text-slate-500">Modulo origen: {item.source_module}</p>
                  <p className="text-xs text-slate-600">
                    Metricas: {Object.keys(metrics).length > 0 ? Object.entries(metrics).map(([k, v]) => `${k}: ${String(v)}`).join(" · ") : "Sin metricas"}
                  </p>
                  <p className="text-xs text-slate-500">Actualizado: {humanDate(item.updated_at)}</p>
                  <button
                    type="button"
                    className="rounded-editorial px-3 py-2 text-xs font-semibold border border-[#041627]/20 min-h-[44px]"
                    onClick={() => setExpandedIds((prev) => ({ ...prev, [item.id]: !prev[item.id] }))}
                  >
                    {expandedIds[item.id] ? "Ocultar detalle" : "Ver detalle"}
                  </button>
                  {expandedIds[item.id] ? (
                    <div className="text-sm text-slate-700 rounded bg-[#f7fafc] border border-[#041627]/10 p-3">{item.content || "Sin detalle."}</div>
                  ) : null}
                </article>
              );
            })}
          </div>
        )}
      </section>

      <section className="sovereign-card p-5 space-y-4">
        <h2 className="font-headline text-2xl text-[#041627]">Relaciones importantes</h2>
        {graph?.edges?.length ? (
          <ul className="space-y-2">
            {graph.edges.slice(0, 12).map((edge) => (
              <li key={edge.id} className="rounded-editorial border border-[#041627]/10 p-3 text-sm text-slate-700">
                {relationText(edge)}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-500">Sin relaciones registradas.</p>
        )}
      </section>

      <section className="sovereign-card p-5 space-y-4">
        <h2 className="font-headline text-2xl text-[#041627]">Actividad reciente</h2>
        {timeline?.items?.length ? (
          <ul className="space-y-2">
            {timeline.items.slice(0, 20).map((event) => (
              <li key={event.id} className="rounded-editorial border border-[#041627]/10 p-3">
                <p className="text-sm font-semibold text-[#041627]">{eventLabel(event.event_type)}</p>
                <p className="text-xs text-slate-500">{humanDate(event.created_at)}</p>
                {debugMode ? <p className="text-[11px] text-slate-500 mt-1">source_id: {event.source_id || "-"}</p> : null}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-500">Sin actividad reciente.</p>
        )}
      </section>

      <section className="sovereign-card p-5 space-y-4">
        <h2 className="font-headline text-2xl text-[#041627]">Pregunta sobre este cliente</h2>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ejemplo: que hallazgos criticos existen en efectivo y bancos?"
          className="w-full min-h-[120px] rounded-editorial border border-[#041627]/15 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#14b8a6]"
        />
        <button
          type="button"
          onClick={handleAsk}
          disabled={isAsking || !query.trim()}
          className="rounded-editorial px-4 py-2 text-xs uppercase tracking-[0.12em] font-bold text-white bg-[#0d9488] hover:bg-[#0b7e72] min-h-[44px] disabled:opacity-50"
        >
          {isAsking ? "Consultando..." : "Preguntar a la memoria"}
        </button>
        {askResponse ? (
          <div className="space-y-3">
            <div className="rounded-editorial border border-[#041627]/10 p-3 bg-[#f8fbfd]">
              <p className="text-sm font-semibold text-[#041627]">Respuesta</p>
              <p className="text-sm text-slate-700 mt-1">{askResponse.answer}</p>
            </div>
            <div className="rounded-editorial border border-[#041627]/10 p-3">
              <p className="text-sm font-semibold text-[#041627]">Fuentes</p>
              <ul className="mt-2 space-y-2">
                {askResponse.sources.map((source, idx) => (
                  <li key={`${source.entity_id}-${idx}`} className="text-xs text-slate-700">
                    <span className="font-semibold">{source.title || source.entity_type || "Fuente"}</span> · modulo {source.source_module} · score {source.score.toFixed(2)}
                    <p className="text-slate-500 mt-1">{source.excerpt}</p>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ) : null}
      </section>

      {isRefreshing ? <p className="text-xs text-slate-500">Actualizando memoria...</p> : null}
    </div>
  );
}
