import { authFetchJson } from "../api";
import { buildApiUrl } from "../api-base";
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

export interface ReportHistoryItem {
  kind: string;
  report_name: string;
  generated_at: string;
  path: string;
  file_hash: string;
  size_bytes: number;
  status: string;
  origin: string;
}

export interface ReportHistoryPayload {
  cliente_id: string;
  gates: Array<{ code: string; title: string; status: "ok" | "blocked"; detail: string }>;
  gate_status: Record<string, "ok" | "blocked" | string>;
  coverage_summary: {
    total_assertions: number;
    covered_assertions: number;
    coverage_pct: number;
    missing_by_area: Record<string, string[]>;
  };
  items: ReportHistoryItem[];
}

export interface ReportStatusPayload {
  cliente_id: string;
  gates: Array<{ code: string; title: string; status: "ok" | "blocked"; detail: string }>;
  missing_sections: string[];
  can_emit_draft: boolean;
  can_emit_final: boolean;
  coverage_summary: {
    total_assertions: number;
    covered_assertions: number;
    coverage_pct: number;
    missing_by_area: Record<string, string[]>;
  };
}

export async function generateExecutivePdf(clienteId: string, mode: "draft" | "final" = "draft"): Promise<ExecutivePdfMeta> {
  const response = await authFetchJson<ApiEnvelope<unknown>>(`/reportes/${clienteId}/executive-pdf?mode=${mode}`);
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

  const response = await fetch(buildApiUrl(`/reportes/${clienteId}/executive-pdf`), {
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

  const fileResponse = await fetch(buildApiUrl(`/reportes/${clienteId}/executive-pdf/file?path=${encodeURIComponent(path)}`), {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!fileResponse.ok) {
    throw new Error(`No se pudo descargar el archivo (${fileResponse.status}).`);
  }
  return { blob: await fileResponse.blob(), filename };
}

export async function downloadExecutivePdfByPath(
  clienteId: string,
  path: string,
  filename: string,
): Promise<{ blob: Blob; filename: string }> {
  const token = typeof window !== "undefined" ? localStorage.getItem("socio_token") : null;
  if (!token) {
    throw new Error("Missing JWT token in session");
  }
  const fileResponse = await fetch(buildApiUrl(`/reportes/${clienteId}/executive-pdf/file?path=${encodeURIComponent(path)}`), {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!fileResponse.ok) {
    throw new Error(`No se pudo descargar el archivo (${fileResponse.status}).`);
  }
  return { blob: await fileResponse.blob(), filename };
}

export async function getReportHistory(clienteId: string): Promise<ReportHistoryPayload> {
  const response = await authFetchJson<ApiEnvelope<unknown>>(`/reportes/${clienteId}/historial`);
  const raw = typeof response?.data === "object" && response.data !== null ? (response.data as Record<string, unknown>) : {};
  const itemsRaw = Array.isArray(raw.items) ? raw.items : [];
  const gatesRaw = Array.isArray(raw.gates) ? raw.gates : [];
  const coverageRaw = typeof raw.coverage_summary === "object" && raw.coverage_summary !== null
    ? (raw.coverage_summary as Record<string, unknown>)
    : {};

  return {
    cliente_id: typeof raw.cliente_id === "string" ? raw.cliente_id : clienteId,
    gate_status: typeof raw.gate_status === "object" && raw.gate_status !== null
      ? (raw.gate_status as Record<string, "ok" | "blocked" | string>)
      : {},
    gates: gatesRaw.map((g) => {
      const row = typeof g === "object" && g !== null ? (g as Record<string, unknown>) : {};
      return {
        code: typeof row.code === "string" ? row.code : "",
        title: typeof row.title === "string" ? row.title : "",
        status: (typeof row.status === "string" ? row.status : "blocked") as "ok" | "blocked",
        detail: typeof row.detail === "string" ? row.detail : "",
      };
    }),
    coverage_summary: {
      total_assertions: typeof coverageRaw.total_assertions === "number" ? coverageRaw.total_assertions : 0,
      covered_assertions: typeof coverageRaw.covered_assertions === "number" ? coverageRaw.covered_assertions : 0,
      coverage_pct: typeof coverageRaw.coverage_pct === "number" ? coverageRaw.coverage_pct : 0,
      missing_by_area: typeof coverageRaw.missing_by_area === "object" && coverageRaw.missing_by_area !== null
        ? (coverageRaw.missing_by_area as Record<string, string[]>)
        : {},
    },
    items: itemsRaw.map((item) => {
      const row = typeof item === "object" && item !== null ? (item as Record<string, unknown>) : {};
      return {
        kind: typeof row.kind === "string" ? row.kind : "",
        report_name: typeof row.report_name === "string" ? row.report_name : "",
        generated_at: typeof row.generated_at === "string" ? row.generated_at : "",
        path: typeof row.path === "string" ? row.path : "",
        file_hash: typeof row.file_hash === "string" ? row.file_hash : "",
        size_bytes: typeof row.size_bytes === "number" ? row.size_bytes : 0,
        status: typeof row.status === "string" ? row.status : "unknown",
        origin: typeof row.origin === "string" ? row.origin : "unknown",
      };
    }),
  };
}

export async function getReportStatus(clienteId: string): Promise<ReportStatusPayload> {
  const response = await authFetchJson<ApiEnvelope<unknown>>(`/reportes/${clienteId}/status`);
  const raw = typeof response?.data === "object" && response.data !== null ? (response.data as Record<string, unknown>) : {};
  const gatesRaw = Array.isArray(raw.gates) ? raw.gates : [];
  const coverageRaw = typeof raw.coverage_summary === "object" && raw.coverage_summary !== null
    ? (raw.coverage_summary as Record<string, unknown>)
    : {};
  const missing = Array.isArray(raw.missing_sections) ? raw.missing_sections.map((x) => String(x)) : [];
  return {
    cliente_id: typeof raw.cliente_id === "string" ? raw.cliente_id : clienteId,
    missing_sections: missing,
    can_emit_draft: Boolean(raw.can_emit_draft),
    can_emit_final: Boolean(raw.can_emit_final),
    gates: gatesRaw.map((g) => {
      const row = typeof g === "object" && g !== null ? (g as Record<string, unknown>) : {};
      return {
        code: typeof row.code === "string" ? row.code : "",
        title: typeof row.title === "string" ? row.title : "",
        status: (typeof row.status === "string" ? row.status : "blocked") as "ok" | "blocked",
        detail: typeof row.detail === "string" ? row.detail : "",
      };
    }),
    coverage_summary: {
      total_assertions: typeof coverageRaw.total_assertions === "number" ? coverageRaw.total_assertions : 0,
      covered_assertions: typeof coverageRaw.covered_assertions === "number" ? coverageRaw.covered_assertions : 0,
      coverage_pct: typeof coverageRaw.coverage_pct === "number" ? coverageRaw.coverage_pct : 0,
      missing_by_area: typeof coverageRaw.missing_by_area === "object" && coverageRaw.missing_by_area !== null
        ? (coverageRaw.missing_by_area as Record<string, string[]>)
        : {},
    },
  };
}
