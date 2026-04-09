"use client";

import type { AuditModule } from "./hooks/useAuditContext";

const DEFAULT_API_BASE =
  process.env.NODE_ENV === "development"
    ? "http://localhost:8000"
    : "https://socio-inteligente-production.up.railway.app";

export const SOCIO_CLIENTE_UPDATED_EVENT = "socio-cliente-updated";

export type ClienteRealtimeEventDetail = {
  clienteId: string;
  eventName: string;
  actor: string;
  payload: Record<string, unknown>;
  sentAt: string;
};

export type PresenceParticipant = {
  user_id: string;
  sub: string;
  display_name: string;
  role: string;
  module: string;
  connected_at: string;
  last_seen_at: string;
};

function stripTrailingSlash(value: string): string {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

function resolveHttpBase(): string {
  const configured =
    process.env.NEXT_PUBLIC_API_BASE?.trim() ||
    process.env.NEXT_PUBLIC_API_URL?.trim() ||
    "";
  if (configured) return stripTrailingSlash(configured);
  return stripTrailingSlash(DEFAULT_API_BASE);
}

function toWsBase(httpBase: string): string {
  if (httpBase.startsWith("https://")) {
    return `wss://${httpBase.slice("https://".length)}`;
  }
  if (httpBase.startsWith("http://")) {
    return `ws://${httpBase.slice("http://".length)}`;
  }
  return httpBase.startsWith("ws://") || httpBase.startsWith("wss://")
    ? httpBase
    : `ws://${httpBase}`;
}

export function getSessionToken(): string {
  if (typeof window === "undefined") return "";
  return window.localStorage.getItem("socio_token") || "";
}

export function buildClienteRealtimeWsUrl(clienteId: string, moduleKey: AuditModule): string {
  const token = getSessionToken();
  if (!token || !clienteId) return "";
  const base = toWsBase(resolveHttpBase());
  const params = new URLSearchParams({
    token,
    module: moduleKey,
  });
  return `${base}/ws/clientes/${encodeURIComponent(clienteId)}?${params.toString()}`;
}

export function dispatchClienteUpdatedEvent(detail: ClienteRealtimeEventDetail): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent<ClienteRealtimeEventDetail>(SOCIO_CLIENTE_UPDATED_EVENT, { detail }));
}

