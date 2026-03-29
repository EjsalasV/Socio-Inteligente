import { authFetchJson } from "../api";
import type { ApiEnvelope } from "../contracts";

export interface ExecutivePdfMeta {
  cliente_id: string;
  report_name: string;
  generated_at: string;
  path: string;
  file_hash: string;
  size_bytes: number;
}

export interface ReportMemoMeta {
  cliente_id: string;
  memo: string;
  generated_at: string;
  source: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function generateExecutivePdf(clienteId: string): Promise<ExecutivePdfMeta> {
  const response = await authFetchJson<ApiEnvelope<unknown>>(`/reportes/${clienteId}/executive-pdf`);
  const raw = typeof response?.data === "object" && response.data !== null ? (response.data as Record<string, unknown>) : {};
  return {
    cliente_id: typeof raw.cliente_id === "string" ? raw.cliente_id : clienteId,
    report_name: typeof raw.report_name === "string" ? raw.report_name : "",
    generated_at: typeof raw.generated_at === "string" ? raw.generated_at : "",
    path: typeof raw.path === "string" ? raw.path : "",
    file_hash: typeof raw.file_hash === "string" ? raw.file_hash : "",
    size_bytes: typeof raw.size_bytes === "number" ? raw.size_bytes : 0,
  };
}

export async function generateExecutiveMemo(clienteId: string): Promise<ReportMemoMeta> {
  const response = await authFetchJson<ApiEnvelope<unknown>>(`/reportes/${clienteId}/memo`, {
    method: "POST",
  });
  const raw = typeof response?.data === "object" && response.data !== null ? (response.data as Record<string, unknown>) : {};
  return {
    cliente_id: typeof raw.cliente_id === "string" ? raw.cliente_id : clienteId,
    memo: typeof raw.memo === "string" ? raw.memo : "",
    generated_at: typeof raw.generated_at === "string" ? raw.generated_at : "",
    source: typeof raw.source === "string" ? raw.source : "unknown",
  };
}

export async function getExecutiveMemo(clienteId: string): Promise<ReportMemoMeta> {
  const response = await authFetchJson<ApiEnvelope<unknown>>(`/reportes/${clienteId}/memo`);
  const raw = typeof response?.data === "object" && response.data !== null ? (response.data as Record<string, unknown>) : {};
  return {
    cliente_id: typeof raw.cliente_id === "string" ? raw.cliente_id : clienteId,
    memo: typeof raw.memo === "string" ? raw.memo : "",
    generated_at: typeof raw.generated_at === "string" ? raw.generated_at : "",
    source: typeof raw.source === "string" ? raw.source : "unknown",
  };
}

export async function downloadExecutivePdf(clienteId: string): Promise<{ blob: Blob; filename: string }> {
  const token = typeof window !== "undefined" ? localStorage.getItem("socio_token") : null;
  if (!token) {
    throw new Error("Missing JWT token in session");
  }

  const response = await fetch(`${API_BASE}/reportes/${clienteId}/executive-pdf`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    throw new Error(`No se pudo descargar el PDF (${response.status}).`);
  }
  const json = (await response.json()) as ApiEnvelope<Record<string, unknown>>;
  const raw = typeof json?.data === "object" && json.data !== null ? json.data : {};
  const path = typeof raw.path === "string" ? raw.path : "";
  const filename = typeof raw.report_name === "string" ? raw.report_name : `${clienteId}_executive_summary.pdf`;

  const fileResponse = await fetch(`${API_BASE}/reportes/${clienteId}/executive-pdf/file?path=${encodeURIComponent(path)}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!fileResponse.ok) {
    throw new Error(`No se pudo descargar el archivo (${fileResponse.status}).`);
  }
  return { blob: await fileResponse.blob(), filename };
}
