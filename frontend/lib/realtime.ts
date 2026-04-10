"use client";

import type { AuditModule } from "./hooks/useAuditContext";
import { hasSessionState } from "./auth-session";

const DEFAULT_API_BASE =
  process.env.NODE_ENV === "development"
    ? "http://localhost:8000"
    : "https://socio-inteligente-production.up.railway.app";
const PUBLIC_WS_BASE = process.env.NEXT_PUBLIC_WS_BASE ?? "";

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

function isLoopbackHost(value: string): boolean {
  const v = value.toLowerCase();
  return v.includes("localhost") || v.includes("127.0.0.1");
}

function isLocalBrowserHost(): boolean {
  if (typeof window === "undefined") return false;
  const host = String(window.location.hostname || "").toLowerCase();
  return host === "localhost" || host === "127.0.0.1";
}

function isRelativeBase(value: string): boolean {
  return value.startsWith("/");
}

function resolveWsSourceBase(): string {
  const wsConfigured = stripTrailingSlash(PUBLIC_WS_BASE.trim());
  const httpConfigured = stripTrailingSlash(
    (process.env.NEXT_PUBLIC_API_BASE?.trim() || process.env.NEXT_PUBLIC_API_URL?.trim() || ""),
  );

  // 1) Explicit WS base wins (recommended for production).
  if (wsConfigured) {
    if (isLoopbackHost(wsConfigured) && !isLocalBrowserHost()) {
      return stripTrailingSlash(DEFAULT_API_BASE);
    }
    // Do not route WS through frontend relative proxy (/api), it usually does not support websocket upgrades.
    if (isRelativeBase(wsConfigured)) {
      return stripTrailingSlash(DEFAULT_API_BASE);
    }
    return wsConfigured;
  }

  // 2) Fallback to HTTP base, but protect against bad production values.
  if (httpConfigured) {
    if (isLoopbackHost(httpConfigured) && !isLocalBrowserHost()) {
      return stripTrailingSlash(DEFAULT_API_BASE);
    }
    // If API base is relative (e.g. /api), use direct backend URL for WS.
    if (isRelativeBase(httpConfigured)) {
      return stripTrailingSlash(DEFAULT_API_BASE);
    }
    return httpConfigured;
  }

  // 3) Last resort.
  return resolveHttpBase();
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

export function buildClienteRealtimeWsUrl(clienteId: string, moduleKey: AuditModule): string {
  if (!hasSessionState() || !clienteId) return "";
  const base = toWsBase(resolveWsSourceBase());
  const params = new URLSearchParams({
    module: moduleKey,
  });
  return `${base}/ws/clientes/${encodeURIComponent(clienteId)}?${params.toString()}`;
}

export function dispatchClienteUpdatedEvent(detail: ClienteRealtimeEventDetail): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent<ClienteRealtimeEventDetail>(SOCIO_CLIENTE_UPDATED_EVENT, { detail }));
}
