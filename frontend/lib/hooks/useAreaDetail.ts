"use client";

import { useCallback, useEffect, useState } from "react";

import { getAreaDetail } from "../api/areas";
import { SOCIO_CLIENTE_UPDATED_EVENT, type ClienteRealtimeEventDetail } from "../realtime";
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

  const refresh = useCallback(async () => {
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
      setData(response);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "No se pudo cargar el detalle del área.";
      setError(message);
      setData(null);
    } finally {
      setIsLoading(false);
    }
  }, [clienteId, areaLs]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (!clienteId || !areaLs) return;
    const handler = (event: Event) => {
      const custom = event as CustomEvent<ClienteRealtimeEventDetail>;
      if (custom.detail?.clienteId !== clienteId) return;
      const eventName = String(custom.detail?.eventName || "");
      if (!eventName.startsWith("area_")) return;
      const eventArea = String(custom.detail?.payload?.area_code || "");
      if (eventArea && eventArea !== areaLs) return;
      void refresh();
    };
    window.addEventListener(SOCIO_CLIENTE_UPDATED_EVENT, handler as EventListener);
    return () => window.removeEventListener(SOCIO_CLIENTE_UPDATED_EVENT, handler as EventListener);
  }, [areaLs, clienteId, refresh]);

  return { data, isLoading, error };
}

