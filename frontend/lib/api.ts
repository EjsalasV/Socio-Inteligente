import type { ApiEnvelope, ChatRequest, ChatResponse, MetodoRequest, MetodoResponse } from "./contracts";
import { buildApiUrl, getApiBase, getBrowserOrigin } from "./api-base";
import { clearSessionState, getStoredCsrfToken } from "./auth-session";

export class TokenExpiredError extends Error {
  constructor(message: string = "JWT token expired or invalid") {
    super(message);
    this.name = "TokenExpiredError";
  }
}

type ApiErrorPayload = {
  status?: string;
  code?: string;
  message?: string;
  action_hint?: string;
  retryable?: boolean;
  details?: unknown;
  detail?: unknown;
};

function extractApiError(payload: unknown): {
  code: string;
  message: string;
  actionHint: string;
} {
  if (!payload || typeof payload !== "object") {
    return { code: "UNKNOWN_API_ERROR", message: "Error desconocido del backend.", actionHint: "" };
  }
  const obj = payload as ApiErrorPayload;
  if (typeof obj.message === "string" && obj.message.trim()) {
    return {
      code: typeof obj.code === "string" && obj.code.trim() ? obj.code.trim() : "API_ERROR",
      message: obj.message.trim(),
      actionHint: typeof obj.action_hint === "string" ? obj.action_hint.trim() : "",
    };
  }
  if (obj.detail && typeof obj.detail === "object") {
    const detailObj = obj.detail as ApiErrorPayload;
    return {
      code: typeof detailObj.code === "string" && detailObj.code.trim() ? detailObj.code.trim() : "API_ERROR",
      message:
        typeof detailObj.message === "string" && detailObj.message.trim()
          ? detailObj.message.trim()
          : "Error en solicitud al backend.",
      actionHint: typeof detailObj.action_hint === "string" ? detailObj.action_hint.trim() : "",
    };
  }
  if (typeof obj.detail === "string" && obj.detail.trim()) {
    return { code: "API_ERROR", message: obj.detail.trim(), actionHint: "" };
  }
  return { code: "API_ERROR", message: "Error en solicitud al backend.", actionHint: "" };
}

function getRequestTimeoutMs(path?: string): number {
  const raw = Number(process.env.NEXT_PUBLIC_API_TIMEOUT_MS || 20000);
  if (!Number.isFinite(raw) || raw <= 0) return 20000;
  const base = Math.min(raw, 60000);
  const heavyRaw = Number(process.env.NEXT_PUBLIC_API_HEAVY_TIMEOUT_MS || 35000);
  const heavy = Number.isFinite(heavyRaw) && heavyRaw > 0
    ? Math.max(35000, Math.min(heavyRaw, 90000))
    : 35000;
  const normalizedPath = String(path || "").toLowerCase();
  if (
    normalizedPath.startsWith("/dashboard/") ||
    normalizedPath.startsWith("/risk-engine/") ||
    normalizedPath.startsWith("/papeles-trabajo/") ||
    normalizedPath.startsWith("/workflow/")
  ) {
    return Math.max(base, heavy);
  }
  if (normalizedPath.startsWith("/chat/") || normalizedPath.startsWith("/metodologia/")) {
    return Math.max(base, 35000);
  }
  return base;
}

function isHeavyPath(path: string): boolean {
  const normalizedPath = String(path || "").toLowerCase();
  return (
    normalizedPath.startsWith("/dashboard/") ||
    normalizedPath.startsWith("/risk-engine/") ||
    normalizedPath.startsWith("/papeles-trabajo/") ||
    normalizedPath.startsWith("/workflow/") ||
    normalizedPath.startsWith("/chat/") ||
    normalizedPath.startsWith("/metodologia/")
  );
}

function getSessionAuthToken(): string {
  if (typeof window === "undefined") return "";
  const fromSession = String(window.sessionStorage?.getItem("socio_auth_token") || "").trim();
  if (fromSession) return fromSession;
  // Compat with previous storage key used by older builds.
  const fromLegacy = String(window.localStorage?.getItem("socio_token") || "").trim();
  return fromLegacy;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  const isFormData = typeof FormData !== "undefined" && init?.body instanceof FormData;
  if (!isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  // Fallback auth path for environments where secure cookies are not persisted (e.g. local http).
  // Backend accepts bearer token and/or cookie.
  if (!headers.has("Authorization")) {
    const sessionToken = getSessionAuthToken();
    if (sessionToken) {
      headers.set("Authorization", `Bearer ${sessionToken}`);
    }
  }

  const method = String(init?.method || "GET").toUpperCase();
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    const csrfToken = getStoredCsrfToken();
    if (!csrfToken) {
      throw new Error("Sesion expirada (CSRF). Vuelve a iniciar sesion.");
    }
    headers.set("X-CSRF-Token", csrfToken);
  }

  // Heavy modules may need one retry when backend warms caches on first hit.
  const attempts = isHeavyPath(path) ? 3 : 2;
  let res: Response | null = null;
  let lastError: unknown = null;

  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    const controller = new AbortController();
    const timeoutMs = getRequestTimeoutMs(path);
    const timeoutId = globalThis.setTimeout(() => controller.abort(), timeoutMs);
    try {
      res = await fetch(buildApiUrl(path), {
        ...init,
        headers,
        credentials: "include",
        signal: controller.signal,
      });
      lastError = null;
      break;
    } catch (error) {
      lastError = error;
      const isAbort = (error as { name?: string })?.name === "AbortError";
      const canRetry = attempt < attempts;
      if (isAbort && canRetry) {
        await new Promise((resolve) => setTimeout(resolve, 500));
        continue;
      }
      if (isAbort) {
        throw new Error(
          `Tiempo de espera agotado al conectar con el backend (${getApiBase()}) tras ${timeoutMs / 1000}s.`,
        );
      }
      if (canRetry) {
        await new Promise((resolve) => setTimeout(resolve, 500));
        continue;
      }
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

  let payload: unknown = null;
  try {
    payload = await res.json();
  } catch {
    payload = null;
  }

  if (res.status === 401) {
    clearSessionState();
    const parsed = extractApiError(payload);
    throw new TokenExpiredError(parsed.message || "Sesion expirada. Inicia sesion otra vez.");
  }

  if (!res.ok) {
    const parsed = extractApiError(payload);
    const suffix = parsed.actionHint ? ` | ${parsed.actionHint}` : "";
    throw new Error(`API error ${res.status} (${parsed.code}): ${parsed.message}${suffix}`);
  }

  return payload as T;
}

export async function authFetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  return apiFetch<T>(path, init);
}

export async function postChat(clienteId: string, payload: ChatRequest): Promise<ApiEnvelope<ChatResponse>> {
  return apiFetch<ApiEnvelope<ChatResponse>>(`/chat/${clienteId}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function postMetodologia(
  clienteId: string,
  payload: MetodoRequest,
): Promise<ApiEnvelope<MetodoResponse>> {
  return apiFetch<ApiEnvelope<MetodoResponse>>(`/metodologia/${clienteId}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function exportChatCriterion(
  clienteId: string,
  payload: { content: string; title?: string },
): Promise<ApiEnvelope<{ saved: boolean; title?: string }>> {
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
  return apiFetch<ApiEnvelope<{ messages: ChatHistoryItem[] }>>(`/chat/${clienteId}/history`);
}
