import type { ApiEnvelope, ChatRequest, ChatResponse, MetodoRequest, MetodoResponse } from "./contracts";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers,
    });
  } catch {
    throw new Error("No se pudo conectar con el backend.");
  }

  if (res.status === 401) {
    throw new TokenExpiredError("Token expired. Please login again.");
  }

  if (!res.ok) {
    let detail = "";
    try {
      const errJson = (await res.json()) as { detail?: unknown };
      if (typeof errJson?.detail === "string") {
        detail = errJson.detail;
      } else if (errJson?.detail) {
        detail = JSON.stringify(errJson.detail);
      }
    } catch {
      detail = "";
    }
    throw new Error(detail ? `API error ${res.status}: ${detail}` : `API error ${res.status}`);
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
