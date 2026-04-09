import type { ApiEnvelope, ChatRequest, ChatResponse, MetodoRequest, MetodoResponse } from "./contracts";
import { buildApiUrl, getApiBase, getBrowserOrigin } from "./api-base";

export class TokenExpiredError extends Error {
  constructor(message: string = "JWT token expired or invalid") {
    super(message);
    this.name = "TokenExpiredError";
  }
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("socio_token");
}

function getRequestTimeoutMs(): number {
  const raw = Number(process.env.NEXT_PUBLIC_API_TIMEOUT_MS || 45000);
  if (!Number.isFinite(raw) || raw <= 0) return 45000;
  return Math.min(raw, 120000);
}

function isIdempotentMethod(method?: string): boolean {
  const normalized = String(method || "GET").trim().toUpperCase();
  return normalized === "GET" || normalized === "HEAD";
}

function requireToken(): string {
  const token = getToken();
  if (!token) {
    throw new Error("Missing JWT token in session");
  }
  return token;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const headers = new Headers(init?.headers);
  const isFormData = typeof FormData !== "undefined" && init?.body instanceof FormData;
  if (!isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const method = String(init?.method || "GET").toUpperCase();
  const attempts = isIdempotentMethod(method) ? 2 : 1;
  let res: Response | null = null;
  let lastError: unknown = null;

  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    const controller = new AbortController();
    const timeoutMs = getRequestTimeoutMs() * attempt;
    const timeoutId = globalThis.setTimeout(() => controller.abort(), timeoutMs);
    try {
      res = await fetch(buildApiUrl(path), {
        ...init,
        headers,
        signal: controller.signal,
      });
      lastError = null;
      break;
    } catch (error) {
      lastError = error;
      const isAbort = (error as { name?: string })?.name === "AbortError";
      const canRetry = attempt < attempts;
      if (isAbort && canRetry) continue;
      if (isAbort) {
        throw new Error(
          `Tiempo de espera agotado al conectar con el backend (${getApiBase()}) tras ${timeoutMs / 1000}s.`,
        );
      }
      if (canRetry) continue;
      throw new Error(
        `No se pudo conectar con el backend (${getApiBase()}). Origin actual: ${getBrowserOrigin()}.`,
      );
    } finally {
      globalThis.clearTimeout(timeoutId);
    }
  }

  if (!res) {
    if ((lastError as { name?: string })?.name === "AbortError") {
      throw new Error(`Tiempo de espera agotado al conectar con el backend (${getApiBase()}).`);
    }
    throw new Error(`No se pudo conectar con el backend (${getApiBase()}).`);
  }

  if (res.status === 401) {
    throw new TokenExpiredError("Token expired. Please login again.");
  }

  if (!res.ok) {
    let detail = "";
    let actionHint = "";
    try {
      const errJson = (await res.json()) as { detail?: unknown };
      if (typeof errJson?.detail === "string") {
        detail = errJson.detail;
      } else if (errJson?.detail && typeof errJson.detail === "object") {
        const d = errJson.detail as { message?: unknown; action_hint?: unknown; code?: unknown };
        if (typeof d.message === "string" && d.message.trim()) {
          detail = d.message.trim();
        } else {
          detail = JSON.stringify(errJson.detail);
        }
        if (typeof d.action_hint === "string" && d.action_hint.trim()) {
          actionHint = d.action_hint.trim();
        }
      } else if (errJson?.detail) {
        detail = JSON.stringify(errJson.detail);
      }
    } catch {
      detail = "";
    }
    const suffix = actionHint ? ` | ${actionHint}` : "";
    throw new Error(detail ? `API error ${res.status}: ${detail}${suffix}` : `API error ${res.status}`);
  }

  return (await res.json()) as T;
}

export async function authFetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  requireToken();
  return apiFetch<T>(path, init);
}

export async function postChat(clienteId: string, payload: ChatRequest): Promise<ApiEnvelope<ChatResponse>> {
  requireToken();
  return apiFetch<ApiEnvelope<ChatResponse>>(`/chat/${clienteId}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function postMetodologia(
  clienteId: string,
  payload: MetodoRequest,
): Promise<ApiEnvelope<MetodoResponse>> {
  requireToken();
  return apiFetch<ApiEnvelope<MetodoResponse>>(`/metodologia/${clienteId}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function exportChatCriterion(
  clienteId: string,
  payload: { content: string; title?: string },
): Promise<ApiEnvelope<{ saved: boolean; title?: string }>> {
  requireToken();
  return apiFetch<ApiEnvelope<{ saved: boolean; title?: string }>>(`/chat/${clienteId}/export`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export type ChatHistoryItem = {
  role: "user" | "assistant";
  text: string;
  timestamp: string;
  citations?: Array<Record<string, unknown>>;
  confidence?: number;
};

export async function getChatHistory(
  clienteId: string,
): Promise<ApiEnvelope<{ messages: ChatHistoryItem[] }>> {
  requireToken();
  return apiFetch<ApiEnvelope<{ messages: ChatHistoryItem[] }>>(`/chat/${clienteId}/history`);
}
