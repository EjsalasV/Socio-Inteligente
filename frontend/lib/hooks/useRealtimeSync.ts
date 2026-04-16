'use client';

import { useEffect, useState, useRef, useCallback } from 'react';

export interface RealtimeParticipant {
  user_id: string;
  sub: string;
  display_name: string;
  role: string;
  module: string;
  connected_at: string;
  last_seen_at: string;
}

export interface RealtimeSyncOptions {
  clienteId: string;
  token?: string;
  module?: string;
  onHallazgoUpdated?: (data: any) => void;
  onAlertCreated?: (data: any) => void;
  onGateStatusChanged?: (data: any) => void;
  onPresenceUpdate?: (participants: RealtimeParticipant[]) => void;
  onError?: (error: string) => void;
  autoReconnect?: boolean;
  reconnectDelay?: number;
}

export function useRealtimeSync({
  clienteId,
  token,
  module = 'general',
  onHallazgoUpdated,
  onAlertCreated,
  onGateStatusChanged,
  onPresenceUpdate,
  onError,
  autoReconnect = true,
  reconnectDelay = 3000,
}: RealtimeSyncOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [participants, setParticipants] = useState<RealtimeParticipant[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const protocol = typeof window !== 'undefined' && window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const baseUrl = typeof window !== 'undefined' ? `${protocol}//${window.location.host}` : '';

      const authToken = token || (typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null);
      const params = new URLSearchParams();
      if (authToken) {
        params.append('token', authToken);
      }
      params.append('module', module);

      const wsUrl = `${baseUrl}/ws/clientes/${clienteId}?${params.toString()}`;

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        if (reconnectTimerRef.current) {
          clearTimeout(reconnectTimerRef.current);
          reconnectTimerRef.current = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          if (message.type === 'presence_snapshot') {
            const newParticipants = message.participants || [];
            setParticipants(newParticipants);
            onPresenceUpdate?.(newParticipants);
          }

          if (message.type === 'cliente_event') {
            const eventName = message.event_name || '';
            const payload = message.payload || {};

            if (eventName === 'hallazgo_updated' || eventName === 'hallazgo_generated') {
              onHallazgoUpdated?.(payload);
            } else if (eventName === 'alert_created') {
              onAlertCreated?.(payload);
            } else if (eventName === 'gate_status_changed') {
              onGateStatusChanged?.(payload);
            }
          }
        } catch (err) {
          console.error('WebSocket error parsing:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        onError?.('Error en conexion WebSocket');
      };

      ws.onclose = () => {
        setIsConnected(false);

        if (autoReconnect) {
          reconnectTimerRef.current = setTimeout(() => {
            connect();
          }, reconnectDelay);
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('WebSocket creation failed:', err);
      onError?.('No se pudo conectar');
    }
  }, [clienteId, token, module, autoReconnect, reconnectDelay, onError, onPresenceUpdate, onHallazgoUpdated, onAlertCreated, onGateStatusChanged]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    setIsConnected(false);
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    participants,
    disconnect,
  };
}
