"use client";

import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";

import { useAuditContext } from "../../lib/hooks/useAuditContext";
import {
  buildClienteRealtimeWsUrl,
  dispatchClienteUpdatedEvent,
  type ClienteRealtimeEventDetail,
  type PresenceParticipant,
} from "../../lib/realtime";

type ClienteRealtimeContextValue = {
  connected: boolean;
  reconnecting: boolean;
  onlineCount: number;
  participants: PresenceParticipant[];
  lastEvent: ClienteRealtimeEventDetail | null;
};

const DEFAULT_VALUE: ClienteRealtimeContextValue = {
  connected: false,
  reconnecting: false,
  onlineCount: 0,
  participants: [],
  lastEvent: null,
};

const ClienteRealtimeContext = createContext<ClienteRealtimeContextValue>(DEFAULT_VALUE);

function safeJsonParse(value: string): Record<string, unknown> {
  if (!value) return {};
  try {
    const parsed = JSON.parse(value);
    return parsed && typeof parsed === "object" ? (parsed as Record<string, unknown>) : {};
  } catch {
    return {};
  }
}

export default function ClienteRealtimeProvider({ children }: { children: React.ReactNode }) {
  const { clienteId, moduleKey } = useAuditContext();
  const [connected, setConnected] = useState<boolean>(false);
  const [reconnecting, setReconnecting] = useState<boolean>(false);
  const [onlineCount, setOnlineCount] = useState<number>(0);
  const [participants, setParticipants] = useState<PresenceParticipant[]>([]);
  const [lastEvent, setLastEvent] = useState<ClienteRealtimeEventDetail | null>(null);
  const reconnectAttemptRef = useRef<number>(0);
  const reconnectTimerRef = useRef<number | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const shouldReconnectRef = useRef<boolean>(true);

  useEffect(() => {
    if (!clienteId) {
      setConnected(false);
      setReconnecting(false);
      setOnlineCount(0);
      setParticipants([]);
      setLastEvent(null);
      shouldReconnectRef.current = false;
      return;
    }

    const wsUrl = buildClienteRealtimeWsUrl(clienteId, moduleKey);
    if (!wsUrl) {
      setConnected(false);
      setReconnecting(false);
      shouldReconnectRef.current = false;
      return;
    }

    let disposed = false;
    shouldReconnectRef.current = true;

    const clearReconnectTimer = () => {
      if (reconnectTimerRef.current !== null) {
        window.clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
    };

    const scheduleReconnect = () => {
      if (disposed || !shouldReconnectRef.current) return;
      clearReconnectTimer();
      const attempt = reconnectAttemptRef.current + 1;
      reconnectAttemptRef.current = attempt;
      const delayMs = Math.min(15000, 500 * Math.pow(2, Math.min(attempt, 5)));
      setReconnecting(true);
      reconnectTimerRef.current = window.setTimeout(() => {
        connect();
      }, delayMs);
    };

    const connect = () => {
      if (disposed) return;
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          if (disposed) return;
          reconnectAttemptRef.current = 0;
          setConnected(true);
          setReconnecting(false);
          ws.send(JSON.stringify({ type: "set_module", module: moduleKey }));
        };

        ws.onmessage = (event: MessageEvent<string>) => {
          if (disposed) return;
          const message = safeJsonParse(event.data);
          const type = String(message.type || "");

          if (type === "presence_snapshot") {
            const rawParticipants = Array.isArray(message.participants) ? message.participants : [];
            const nextParticipants = rawParticipants
              .filter((row): row is Record<string, unknown> => Boolean(row && typeof row === "object"))
              .map((row) => ({
                user_id: String(row.user_id || ""),
                sub: String(row.sub || ""),
                display_name: String(row.display_name || row.sub || "Usuario"),
                role: String(row.role || "auditor"),
                module: String(row.module || "general"),
                connected_at: String(row.connected_at || ""),
                last_seen_at: String(row.last_seen_at || ""),
              }));
            setParticipants(nextParticipants);
            const nextCount = Number(message.online_count);
            setOnlineCount(Number.isFinite(nextCount) ? nextCount : nextParticipants.length);
            return;
          }

          if (type === "cliente_event") {
            const detail: ClienteRealtimeEventDetail = {
              clienteId: String(message.cliente_id || clienteId),
              eventName: String(message.event_name || "updated"),
              actor: String(message.actor || ""),
              payload:
                message.payload && typeof message.payload === "object"
                  ? (message.payload as Record<string, unknown>)
                  : {},
              sentAt: String(message.sent_at || ""),
            };
            setLastEvent(detail);
            dispatchClienteUpdatedEvent(detail);
            return;
          }

          if (type === "ping") {
            ws.send(JSON.stringify({ type: "pong" }));
          }
        };

        ws.onerror = () => {
          if (disposed) return;
          setConnected(false);
        };

        ws.onclose = (event) => {
          if (disposed) return;
          setConnected(false);
          const closeCode = Number(event.code || 0);
          if (closeCode === 4401 || closeCode === 4403 || closeCode === 1008) {
            shouldReconnectRef.current = false;
            setReconnecting(false);
            return;
          }
          scheduleReconnect();
        };
      } catch {
        setConnected(false);
        scheduleReconnect();
      }
    };

    connect();

    return () => {
      disposed = true;
      shouldReconnectRef.current = false;
      clearReconnectTimer();
      const ws = wsRef.current;
      wsRef.current = null;
      if (ws) {
        try {
          ws.close();
        } catch {
          // noop
        }
      }
    };
  }, [clienteId, moduleKey]);

  const value = useMemo<ClienteRealtimeContextValue>(
    () => ({
      connected,
      reconnecting,
      onlineCount,
      participants,
      lastEvent,
    }),
    [connected, reconnecting, onlineCount, participants, lastEvent],
  );

  return <ClienteRealtimeContext.Provider value={value}>{children}</ClienteRealtimeContext.Provider>;
}

export function useClienteRealtime(): ClienteRealtimeContextValue {
  return useContext(ClienteRealtimeContext);
}
