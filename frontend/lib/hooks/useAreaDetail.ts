"use client";

import { useEffect, useState } from "react";

import { getAreaDetail } from "../api/areas";
import type { AreaDetailData } from "../../types/area";

type UseAreaDetailResult = {
  data: AreaDetailData | null;
  isLoading: boolean;
  error: string;
};

export function useAreaDetail(clienteId: string, areaLs: string): UseAreaDetailResult {
  const [data, setData] = useState<AreaDetailData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    let active = true;

    async function load(): Promise<void> {
      if (!clienteId || !areaLs) {
        setData(null);
        setError("Área inválida.");
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError("");
      try {
        const response = await getAreaDetail(clienteId, areaLs);
        if (!active) return;
        setData(response);
      } catch (err: unknown) {
        if (!active) return;
        const message = err instanceof Error ? err.message : "No se pudo cargar el detalle del área.";
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
  }, [clienteId, areaLs]);

  return { data, isLoading, error };
}
