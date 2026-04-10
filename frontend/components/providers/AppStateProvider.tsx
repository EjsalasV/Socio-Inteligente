"use client";

import { createContext, useCallback, useContext, useMemo, useState } from "react";

import type { DashboardData } from "../../types/dashboard";
import type { WorkpaperPlanData } from "../../types/workpapers";

type DashboardEntry = {
  data: DashboardData | null;
  isLoading: boolean;
  error: string;
  updatedAt: number | null;
};

type WorkpapersEntry = {
  data: WorkpaperPlanData | null;
  isLoading: boolean;
  isLoadingMore: boolean;
  savingTaskId: string | null;
  error: string;
  requestedPageSize: number;
  updatedAt: number | null;
};

type AppStateContextValue = {
  getDashboardEntry: (clienteId: string) => DashboardEntry;
  setDashboardEntry: (clienteId: string, patch: Partial<DashboardEntry>) => void;
  getWorkpapersEntry: (clienteId: string) => WorkpapersEntry;
  setWorkpapersEntry: (clienteId: string, patch: Partial<WorkpapersEntry>) => void;
  resetClientState: (clienteId: string) => void;
};

const defaultDashboardEntry = (): DashboardEntry => ({
  data: null,
  isLoading: false,
  error: "",
  updatedAt: null,
});

const defaultWorkpapersEntry = (): WorkpapersEntry => ({
  data: null,
  isLoading: false,
  isLoadingMore: false,
  savingTaskId: null,
  error: "",
  requestedPageSize: 60,
  updatedAt: null,
});

const AppStateContext = createContext<AppStateContextValue | null>(null);

export default function AppStateProvider({ children }: { children: React.ReactNode }) {
  const [dashboardByCliente, setDashboardByCliente] = useState<Record<string, DashboardEntry>>({});
  const [workpapersByCliente, setWorkpapersByCliente] = useState<Record<string, WorkpapersEntry>>({});

  const getDashboardEntry = useCallback(
    (clienteId: string): DashboardEntry => dashboardByCliente[clienteId] ?? defaultDashboardEntry(),
    [dashboardByCliente],
  );

  const setDashboardEntry = useCallback((clienteId: string, patch: Partial<DashboardEntry>) => {
    if (!clienteId) return;
    setDashboardByCliente((prev) => {
      const current = prev[clienteId] ?? defaultDashboardEntry();
      return {
        ...prev,
        [clienteId]: {
          ...current,
          ...patch,
        },
      };
    });
  }, []);

  const getWorkpapersEntry = useCallback(
    (clienteId: string): WorkpapersEntry => workpapersByCliente[clienteId] ?? defaultWorkpapersEntry(),
    [workpapersByCliente],
  );

  const setWorkpapersEntry = useCallback((clienteId: string, patch: Partial<WorkpapersEntry>) => {
    if (!clienteId) return;
    setWorkpapersByCliente((prev) => {
      const current = prev[clienteId] ?? defaultWorkpapersEntry();
      return {
        ...prev,
        [clienteId]: {
          ...current,
          ...patch,
        },
      };
    });
  }, []);

  const resetClientState = useCallback((clienteId: string) => {
    if (!clienteId) return;
    setDashboardByCliente((prev) => {
      if (!(clienteId in prev)) return prev;
      const next = { ...prev };
      delete next[clienteId];
      return next;
    });
    setWorkpapersByCliente((prev) => {
      if (!(clienteId in prev)) return prev;
      const next = { ...prev };
      delete next[clienteId];
      return next;
    });
  }, []);

  const value = useMemo<AppStateContextValue>(
    () => ({
      getDashboardEntry,
      setDashboardEntry,
      getWorkpapersEntry,
      setWorkpapersEntry,
      resetClientState,
    }),
    [getDashboardEntry, getWorkpapersEntry, resetClientState, setDashboardEntry, setWorkpapersEntry],
  );

  return <AppStateContext.Provider value={value}>{children}</AppStateContext.Provider>;
}

export function useAppState(): AppStateContextValue {
  const ctx = useContext(AppStateContext);
  if (!ctx) {
    return {
      getDashboardEntry: () => defaultDashboardEntry(),
      setDashboardEntry: () => undefined,
      getWorkpapersEntry: () => defaultWorkpapersEntry(),
      setWorkpapersEntry: () => undefined,
      resetClientState: () => undefined,
    };
  }
  return ctx;
}
