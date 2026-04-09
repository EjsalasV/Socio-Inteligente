"use client";

import { useCallback, useEffect, useState } from "react";

import { getDashboardData } from "../api/dashboard";
import { SOCIO_CLIENTE_UPDATED_EVENT, type ClienteRealtimeEventDetail } from "../realtime";
import type { DashboardData } from "../../types/dashboard";

type UseDashboardResult = {
  data: DashboardData | null;
  isLoading: boolean;
  error: string;
};

function parseDelayMs(): number {
  const raw = process.env.NEXT_PUBLIC_DASHBOARD_DELAY_MS;
  if (!raw) return 0;
  const parsed = Number(raw);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 0;
}

function wait(ms: number): Promise<void> {
  if (ms <= 0) return Promise.resolve();
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function useDashboard(clienteId: string): UseDashboardResult {
  const [data, setData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");

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
      await wait(parseDelayMs());
      const response = await getDashboardData(clienteId);
      setData(response);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "No se pudo cargar el dashboard.";
      setError(message);
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
      if (
        eventName.startsWith("workflow_") ||
        eventName.startsWith("workpaper_") ||
        eventName.startsWith("area_") ||
        eventName === "perfil_updated"
      ) {
        void refresh();
      }
    };
    window.addEventListener(SOCIO_CLIENTE_UPDATED_EVENT, handler as EventListener);
    return () => window.removeEventListener(SOCIO_CLIENTE_UPDATED_EVENT, handler as EventListener);
  }, [clienteId, refresh]);

  return { data, isLoading, error };
}

