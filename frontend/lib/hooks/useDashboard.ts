"use client";

import { useCallback, useEffect } from "react";

import { useAppState } from "../../components/providers/AppStateProvider";
import type { DashboardData } from "../../types/dashboard";
import { getDashboardData } from "../api/dashboard";
import { SOCIO_CLIENTE_UPDATED_EVENT, type ClienteRealtimeEventDetail } from "../realtime";

type UseDashboardResult = {
  data: DashboardData | null;
  isLoading: boolean;
  error: string;
};

const inFlightByKey = new Map<string, Promise<void>>();

function parseDelayMs(): number {
  const raw = process.env.NEXT_PUBLIC_DASHBOARD_DELAY_MS;
  if (!raw) return 0;
  const parsed = Number(raw);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 0;
}

function parseAreasPageSize(): number {
  const raw = process.env.NEXT_PUBLIC_DASHBOARD_AREAS_PAGE_SIZE;
  if (!raw) return 8;
  const parsed = Number(raw);
  if (!Number.isFinite(parsed)) return 8;
  return Math.max(4, Math.min(50, Math.round(parsed)));
}

function parseDashboardCacheTtlMs(): number {
  const raw = process.env.NEXT_PUBLIC_DASHBOARD_CACHE_TTL_MS;
  if (!raw) return 120000;
  const parsed = Number(raw);
  if (!Number.isFinite(parsed) || parsed <= 0) return 120000;
  return Math.max(10000, Math.min(300000, Math.round(parsed)));
}

function wait(ms: number): Promise<void> {
  if (ms <= 0) return Promise.resolve();
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function useDashboard(clienteId: string): UseDashboardResult {
  const { getDashboardEntry, setDashboardEntry } = useAppState();
  const entry = getDashboardEntry(clienteId);

  const refresh = useCallback(async (force = false) => {
    if (!clienteId) {
      setDashboardEntry(clienteId, {
        data: null,
        error: "Cliente invalido.",
        isLoading: false,
      });
      return;
    }

    const areasPage = 1;
    const areasPageSize = parseAreasPageSize();
    const cacheTtlMs = parseDashboardCacheTtlMs();
    const current = getDashboardEntry(clienteId);
    if (
      !force &&
      current.data &&
      current.updatedAt &&
      Date.now() - current.updatedAt < cacheTtlMs
    ) {
      return;
    }
    const requestKey = `${clienteId}:${areasPage}:${areasPageSize}`;
    const existing = inFlightByKey.get(requestKey);
    if (existing) {
      await existing;
      return;
    }

    const request = (async () => {
      setDashboardEntry(clienteId, { isLoading: true, error: "" });
      try {
        await wait(parseDelayMs());
        const response = await getDashboardData(clienteId, { areasPage, areasPageSize });
        setDashboardEntry(clienteId, {
          data: response,
          error: "",
          isLoading: false,
          updatedAt: Date.now(),
        });
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "No se pudo cargar el dashboard.";
        setDashboardEntry(clienteId, {
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
  }, [clienteId, getDashboardEntry, setDashboardEntry]);

  useEffect(() => {
    void refresh(false);
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
        eventName === "perfil_updated" ||
        eventName === "tb_uploaded" ||
        eventName === "mayor_uploaded"
      ) {
        void refresh(true);
      }
    };
    window.addEventListener(SOCIO_CLIENTE_UPDATED_EVENT, handler as EventListener);
    return () => window.removeEventListener(SOCIO_CLIENTE_UPDATED_EVENT, handler as EventListener);
  }, [clienteId, refresh]);

  return {
    data: entry.data,
    isLoading: entry.isLoading,
    error: entry.error,
  };
}
