"use client";

import { useCallback, useEffect } from "react";

import { useAppState } from "../../components/providers/AppStateProvider";
import type { WorkpaperPlanData } from "../../types/workpapers";
import { getWorkpaperPlan, patchWorkpaperTask } from "../api/workpapers";
import { SOCIO_CLIENTE_UPDATED_EVENT, type ClienteRealtimeEventDetail } from "../realtime";

type UseWorkpapersResult = {
  data: WorkpaperPlanData | null;
  isLoading: boolean;
  isLoadingMore: boolean;
  hasMore: boolean;
  error: string;
  savingTaskId: string | null;
  refresh: () => Promise<void>;
  loadMore: () => Promise<void>;
  updateTask: (taskId: string, done: boolean, evidenceNote: string) => Promise<void>;
};

const inFlightByKey = new Map<string, Promise<void>>();

function parseWorkpapersPageSize(): number {
  const raw = process.env.NEXT_PUBLIC_WORKPAPERS_PAGE_SIZE;
  if (!raw) return 60;
  const parsed = Number(raw);
  if (!Number.isFinite(parsed)) return 60;
  return Math.max(20, Math.min(200, Math.round(parsed)));
}

export function useWorkpapers(clienteId: string): UseWorkpapersResult {
  const { getWorkpapersEntry, setWorkpapersEntry } = useAppState();
  const entry = getWorkpapersEntry(clienteId);

  const refresh = useCallback(
    async (pageSizeOverride?: number) => {
      if (!clienteId) return;

      const pageSize = pageSizeOverride ?? entry.requestedPageSize ?? parseWorkpapersPageSize();
      const requestKey = `${clienteId}:${pageSize}`;
      const existing = inFlightByKey.get(requestKey);
      if (existing) {
        await existing;
        return;
      }

      const request = (async () => {
        setWorkpapersEntry(clienteId, { isLoading: true, error: "" });
        try {
          const response = await getWorkpaperPlan(clienteId, { page: 1, pageSize });
          setWorkpapersEntry(clienteId, {
            data: response,
            requestedPageSize: pageSize,
            error: "",
            isLoading: false,
            updatedAt: Date.now(),
          });
        } catch (err: unknown) {
          const message = err instanceof Error ? err.message : "No se pudo cargar papeles de trabajo.";
          setWorkpapersEntry(clienteId, {
            data: null,
            error: message,
            isLoading: false,
          });
        } finally {
          inFlightByKey.delete(requestKey);
        }
      })();

      inFlightByKey.set(requestKey, request);
      await request;
    },
    [clienteId, entry.requestedPageSize, setWorkpapersEntry],
  );

  useEffect(() => {
    if (!clienteId) return;
    const basePageSize = parseWorkpapersPageSize();
    setWorkpapersEntry(clienteId, { requestedPageSize: basePageSize });
    void refresh(basePageSize);
  }, [clienteId, refresh, setWorkpapersEntry]);

  useEffect(() => {
    if (!clienteId) return;
    const handler = (event: Event) => {
      const custom = event as CustomEvent<ClienteRealtimeEventDetail>;
      if (custom.detail?.clienteId !== clienteId) return;
      const eventName = String(custom.detail?.eventName || "");
      if (eventName.startsWith("workpaper_") || eventName.startsWith("workflow_")) {
        void refresh();
      }
    };
    window.addEventListener(SOCIO_CLIENTE_UPDATED_EVENT, handler as EventListener);
    return () => window.removeEventListener(SOCIO_CLIENTE_UPDATED_EVENT, handler as EventListener);
  }, [clienteId, refresh]);

  const loadMore = useCallback(async () => {
    if (!clienteId) return;
    if (!entry.data?.tasks_has_more) return;
    if (entry.isLoadingMore) return;
    setWorkpapersEntry(clienteId, { isLoadingMore: true });
    try {
      const nextPageSize = (entry.requestedPageSize || parseWorkpapersPageSize()) + parseWorkpapersPageSize();
      await refresh(nextPageSize);
    } finally {
      setWorkpapersEntry(clienteId, { isLoadingMore: false });
    }
  }, [clienteId, entry.data?.tasks_has_more, entry.isLoadingMore, entry.requestedPageSize, refresh, setWorkpapersEntry]);

  const updateTask = useCallback(
    async (taskId: string, done: boolean, evidenceNote: string) => {
      if (!clienteId) return;
      setWorkpapersEntry(clienteId, { savingTaskId: taskId });
      try {
        await patchWorkpaperTask(clienteId, taskId, { done, evidence_note: evidenceNote });
        const latestEntry = getWorkpapersEntry(clienteId);
        setWorkpapersEntry(clienteId, {
          data: latestEntry.data
            ? {
                ...latestEntry.data,
                tasks: latestEntry.data.tasks.map((task) =>
                  task.id === taskId ? { ...task, done, evidence_note: evidenceNote } : task,
                ),
              }
            : null,
        });
        await refresh();
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "No se pudo actualizar el papel de trabajo.";
        setWorkpapersEntry(clienteId, { error: message });
      } finally {
        setWorkpapersEntry(clienteId, { savingTaskId: null });
      }
    },
    [clienteId, getWorkpapersEntry, refresh, setWorkpapersEntry],
  );

  return {
    data: entry.data,
    isLoading: entry.isLoading,
    isLoadingMore: entry.isLoadingMore,
    hasMore: Boolean(entry.data?.tasks_has_more),
    error: entry.error,
    savingTaskId: entry.savingTaskId,
    refresh: () => refresh(),
    loadMore,
    updateTask,
  };
}
