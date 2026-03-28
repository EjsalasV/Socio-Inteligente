"use client";

import { useEffect, useState } from "react";

import { getRiskEngineData } from "../api/risk";
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

      try {
        const response = await getRiskEngineData(clienteId);
        if (!active) return;
        setData(response);
      } catch (err: unknown) {
        if (!active) return;
        const rawMessage = err instanceof Error ? err.message : "No se pudo cargar la matriz de riesgo.";
        const message =
          rawMessage.toLowerCase().includes("missing jwt token")
            ? "Sesion no iniciada. Vuelve al login para continuar."
            : rawMessage;
        setError(message);
        setData(null);
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

