"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import KnowledgeAskTab from "../../../components/knowledge/KnowledgeAskTab";
import KnowledgeEntitiesTab from "../../../components/knowledge/KnowledgeEntitiesTab";
import KnowledgeGraphTab from "../../../components/knowledge/KnowledgeGraphTab";
import KnowledgeTimelineTab from "../../../components/knowledge/KnowledgeTimelineTab";
import { askKnowledge, getKnowledgeEntities, getKnowledgeGraph, getKnowledgeTimeline } from "../../../lib/api/knowledge";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import type {
  KnowledgeAskResponse,
  KnowledgeEntitiesResponse,
  KnowledgeGraphResponse,
  KnowledgeTimelineResponse,
} from "../../../types/knowledge";

type TabKey = "entities" | "graph" | "timeline" | "ask";

const DEFAULT_PAGE_SIZE = 20;

const EMPTY_ENTITIES: KnowledgeEntitiesResponse = {
  items: [],
  total: 0,
  page: 1,
  page_size: DEFAULT_PAGE_SIZE,
  total_pages: 1,
};

export default function KnowledgePage() {
  const { clienteId } = useAuditContext();
  const [activeTab, setActiveTab] = useState<TabKey>("entities");
  const [entities, setEntities] = useState<KnowledgeEntitiesResponse>(EMPTY_ENTITIES);
  const [graph, setGraph] = useState<KnowledgeGraphResponse | null>(null);
  const [timeline, setTimeline] = useState<KnowledgeTimelineResponse | null>(null);
  const [askResponse, setAskResponse] = useState<KnowledgeAskResponse | null>(null);
  const [query, setQuery] = useState<string>("");
  const [search, setSearch] = useState<string>("");
  const [page, setPage] = useState<number>(1);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [isAsking, setIsAsking] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  const loadEntities = useCallback(async () => {
    if (!clienteId) return;
    const response = await getKnowledgeEntities(clienteId, {
      page,
      page_size: DEFAULT_PAGE_SIZE,
      q: search || undefined,
    });
    setEntities(response);
  }, [clienteId, page, search]);

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

  useEffect(() => {
    let mounted = true;
    const run = async () => {
      if (!clienteId) return;
      setIsLoading(true);
      setError("");
      try {
        await loadEntities();
      } catch (err) {
        if (!mounted) return;
        setError(err instanceof Error ? err.message : "No se pudo cargar Knowledge Core.");
      } finally {
        if (mounted) setIsLoading(false);
      }
    };
    void run();
    return () => {
      mounted = false;
    };
  }, [clienteId, loadEntities]);

  useEffect(() => {
    if (!clienteId) return;
    const run = async () => {
      setIsRefreshing(true);
      setError("");
      try {
        if (activeTab === "entities") await loadEntities();
        if (activeTab === "graph" && !graph) await loadGraph();
        if (activeTab === "timeline" && !timeline) await loadTimeline();
      } catch (err) {
        setError(err instanceof Error ? err.message : "No se pudo actualizar la pestaña.");
      } finally {
        setIsRefreshing(false);
      }
    };
    void run();
  }, [activeTab, clienteId, graph, loadEntities, loadGraph, loadTimeline, timeline]);

  const handleAsk = async () => {
    if (!clienteId || !query.trim()) return;
    setIsAsking(true);
    setError("");
    try {
      const response = await askKnowledge(clienteId, { query: query.trim(), top_k: 5 });
      setAskResponse(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo ejecutar la consulta.");
    } finally {
      setIsAsking(false);
    }
  };

  const tabs = useMemo<Array<{ key: TabKey; label: string }>>(
    () => [
      { key: "entities", label: "Entidades" },
      { key: "graph", label: "Grafo" },
      { key: "timeline", label: "Timeline" },
      { key: "ask", label: "Ask" },
    ],
    [],
  );

  if (isLoading) return <DashboardSkeleton />;
  if (error && !isRefreshing) return <ErrorMessage message={error} />;

  return (
    <div className="pt-4 pb-10 space-y-6 max-w-[1600px]">
      <section className="space-y-2">
        <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">Knowledge Core</p>
        <h1 className="font-headline text-5xl text-[#041627]">Nucleo Inteligente</h1>
        <p className="text-sm text-slate-500">Vista aislada para entidades, grafo, timeline y consultas.</p>
      </section>

      <section className="sovereign-card p-4 space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          {tabs.map((tab) => {
            const active = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                type="button"
                onClick={() => setActiveTab(tab.key)}
                className={`rounded-editorial px-4 py-2 text-xs uppercase tracking-[0.1em] font-bold min-h-[44px] ${
                  active
                    ? "bg-[#041627] text-white"
                    : "border border-[#041627]/15 text-slate-700 hover:bg-[#f4f8fb]"
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {activeTab === "entities" ? (
          <div className="space-y-3">
            <div className="flex flex-col sm:flex-row gap-2">
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar por titulo o contenido..."
                className="w-full sm:max-w-md rounded-editorial border border-[#041627]/15 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#14b8a6] min-h-[44px]"
              />
              <button
                type="button"
                className="rounded-editorial px-4 py-2 text-xs uppercase tracking-[0.12em] font-bold text-white bg-[#0d9488] hover:bg-[#0b7e72] min-h-[44px]"
                onClick={() => {
                  setPage(1);
                  void loadEntities();
                }}
              >
                Buscar
              </button>
            </div>
            <KnowledgeEntitiesTab
              items={entities.items}
              total={entities.total}
              page={entities.page}
              totalPages={entities.total_pages}
              onPageChange={(nextPage) => setPage(nextPage)}
              isLoading={isRefreshing}
            />
          </div>
        ) : null}

        {activeTab === "graph" ? <KnowledgeGraphTab graph={graph} isLoading={isRefreshing} /> : null}
        {activeTab === "timeline" ? (
          <KnowledgeTimelineTab events={timeline?.items ?? []} isLoading={isRefreshing} />
        ) : null}
        {activeTab === "ask" ? (
          <KnowledgeAskTab
            query={query}
            onQueryChange={setQuery}
            onAsk={handleAsk}
            isLoading={isAsking}
            response={askResponse}
          />
        ) : null}
      </section>
    </div>
  );
}

