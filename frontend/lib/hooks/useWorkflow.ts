"use client";

import { useEffect, useState } from "react";

import { getWorkflowState } from "../api/workflow";
import type { WorkflowState } from "../../types/workflow";

export function useWorkflow(clienteId: string): { data: WorkflowState | null; loading: boolean } {
  const [data, setData] = useState<WorkflowState | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let active = true;
    async function load(): Promise<void> {
      if (!clienteId) {
        setData(null);
        setLoading(false);
        return;
      }
      setLoading(true);
      try {
        const response = await getWorkflowState(clienteId);
        if (!active) return;
        setData(response);
      } catch {
        if (!active) return;
        setData(null);
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, [clienteId]);

  return { data, loading };
}
