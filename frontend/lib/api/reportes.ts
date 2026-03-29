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
