"use client";

import { useCallback, useEffect, useState } from "react";

import { getRiskEngineData } from "../api/risk";
import { SOCIO_CLIENTE_UPDATED_EVENT, type ClienteRealtimeEventDetail } from "../realtime";
import type { RiskEngineResponse } from "../../types/risk";

type UseRiskResult = {
  data: RiskEngineResponse | null;
  isLoading: boolean;
  error: string;
};

const RISK_CACHE = new Map<string, { data: RiskEngineResponse; updatedAt: number }>();

function parseRiskCacheTtlMs(): number {
  const raw = Number(process.env.NEXT_PUBLIC_RISK_CACHE_TTL_MS || 90000);
  if (!Number.isFinite(raw) || raw <= 0) return 90000;
  return Math.max(10000, Math.min(300000, Math.round(raw)));
}

export function useRiskEngine(clienteId: string): UseRiskResult {
  const [data, setData] = useState<RiskEngineResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");

  const refresh = useCallback(
    async (force = false) => {
      if (!clienteId) {
        setData(null);
        setError("Cliente invalido.");
        setIsLoading(false);
        return;
      }

      const ttl = parseRiskCacheTtlMs();
      const cached = RISK_CACHE.get(clienteId);
      if (!force && cached && Date.now() - cached.updatedAt < ttl) {
        setData(cached.data);
        setError("");
        setIsLoading(false);
        return;
      }

      if (!data) setIsLoading(true);
      setError("");

      try {
        const response = await getRiskEngineData(clienteId);
        RISK_CACHE.set(clienteId, { data: response, updatedAt: Date.now() });
        setData(response);
      } catch (err: unknown) {
        const rawMessage = err instanceof Error ? err.message : "No se pudo cargar la matriz de riesgo.";
        const message = rawMessage.toLowerCase().includes("missing jwt token")
          ? "Sesion no iniciada. Vuelve al login para continuar."
          : rawMessage;
        setError(message);
        setData(null);
      } finally {
        setIsLoading(false);
      }
    },
    [clienteId, data],
  );

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
        eventName.startsWith("area_") ||
        eventName === "perfil_updated"
      ) {
        void refresh(true);
      }
    };
    window.addEventListener(SOCIO_CLIENTE_UPDATED_EVENT, handler as EventListener);
    return () => window.removeEventListener(SOCIO_CLIENTE_UPDATED_EVENT, handler as EventListener);
  }, [clienteId, refresh]);

  return { data, isLoading, error };
}

