"use client";

import { useEffect, useState } from "react";

import { getDashboardData } from "../api/dashboard";
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

  useEffect(() => {
    let active = true;

    async function load(): Promise<void> {
      if (!clienteId) {
        setData(null);
        setError("Cliente inválido.");
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError("");
      setData(null);

      try {
        await wait(parseDelayMs());
        const response = await getDashboardData(clienteId);
        if (!active) return;
        setData(response);
      } catch (err: unknown) {
        if (!active) return;
        const message = err instanceof Error ? err.message : "No se pudo cargar el dashboard.";
        setError(message);
      } finally {
        if (active) setIsLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [clienteId]);

  return { data, isLoading, error };
}
