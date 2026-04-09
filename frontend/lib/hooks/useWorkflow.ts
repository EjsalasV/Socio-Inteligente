"use client";

import { useCallback, useEffect, useState } from "react";

import { getWorkflowState } from "../api/workflow";
import { SOCIO_CLIENTE_UPDATED_EVENT, type ClienteRealtimeEventDetail } from "../realtime";
import type { WorkflowState } from "../../types/workflow";

export function useWorkflow(clienteId: string): { data: WorkflowState | null; loading: boolean } {
  const [data, setData] = useState<WorkflowState | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const refresh = useCallback(async () => {
    if (!clienteId) {
      setData(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const response = await getWorkflowState(clienteId);
      setData(response);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
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
      if (eventName.startsWith("workflow_") || eventName.startsWith("workpaper_")) {
        void refresh();
      }
    };
    window.addEventListener(SOCIO_CLIENTE_UPDATED_EVENT, handler as EventListener);
    return () => window.removeEventListener(SOCIO_CLIENTE_UPDATED_EVENT, handler as EventListener);
  }, [clienteId, refresh]);

  return { data, loading };
}
