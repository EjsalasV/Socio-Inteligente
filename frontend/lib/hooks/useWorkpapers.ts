"use client";

import { useCallback, useEffect, useState } from "react";

import { getWorkpaperPlan, patchWorkpaperTask } from "../api/workpapers";
import { SOCIO_CLIENTE_UPDATED_EVENT, type ClienteRealtimeEventDetail } from "../realtime";
import type { WorkpaperPlanData } from "../../types/workpapers";

type UseWorkpapersResult = {
  data: WorkpaperPlanData | null;
  isLoading: boolean;
  error: string;
  savingTaskId: string | null;
  refresh: () => Promise<void>;
  updateTask: (taskId: string, done: boolean, evidenceNote: string) => Promise<void>;
};

export function useWorkpapers(clienteId: string): UseWorkpapersResult {
  const [data, setData] = useState<WorkpaperPlanData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");
  const [savingTaskId, setSavingTaskId] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!clienteId) {
      setData(null);
      setError("Cliente inválido.");
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError("");
    try {
      const response = await getWorkpaperPlan(clienteId);
      setData(response);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "No se pudo cargar papeles de trabajo.";
      setError(message);
      setData(null);
    } finally {
      setIsLoading(false);
    }
  }, [clienteId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

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

  const updateTask = useCallback(
    async (taskId: string, done: boolean, evidenceNote: string) => {
      setSavingTaskId(taskId);
      try {
        await patchWorkpaperTask(clienteId, taskId, { done, evidence_note: evidenceNote });
        setData((prev) => {
          if (!prev) return prev;
          const tasks = prev.tasks.map((task) =>
            task.id === taskId ? { ...task, done, evidence_note: evidenceNote } : task,
          );
          const required = tasks.filter((task) => task.required);
          const requiredDone = required.filter((task) => task.done);
          const completion_pct = required.length > 0 ? (requiredDone.length / required.length) * 100 : 0;
          return { ...prev, tasks, completion_pct };
        });
        await refresh();
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "No se pudo actualizar el papel de trabajo.";
        setError(message);
      } finally {
        setSavingTaskId(null);
      }
    },
    [clienteId, refresh],
  );

  return { data, isLoading, error, savingTaskId, refresh, updateTask };
}
