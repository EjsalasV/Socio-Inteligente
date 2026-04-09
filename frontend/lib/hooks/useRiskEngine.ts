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

export function useRiskEngine(clienteId: string): UseRiskResult {
  const [data, setData] = useState<RiskEngineResponse | null>(null);
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
      const response = await getRiskEngineData(clienteId);
      setData(response);
    } catch (err: unknown) {
      const rawMessage = err instanceof Error ? err.message : "No se pudo cargar la matriz de riesgo.";
      const message =
        rawMessage.toLowerCase().includes("missing jwt token")
          ? "Sesión no iniciada. Vuelve al login para continuar."
          : rawMessage;
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
      if (
        eventName.startsWith("workflow_") ||
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

