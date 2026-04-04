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
  document_version?: number;
  supersedes_version?: number | null;
  is_current?: boolean;
  state?: string;
  diff_from_previous?: {
    has_previous?: boolean;
    changed_sections?: string[];
    prompt_changed?: boolean;
    template_changed?: boolean;
    input_changed?: boolean;
  };
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

export interface DocumentArtifact {
  artifact_type: "markdown" | "docx" | string;
  artifact_path: string;
  artifact_hash: string;
  template_version: string;
  size_bytes: number;
}

export interface DocumentVersion {
  document_type: string;
  document_version: number;
  supersedes_version: number | null;
  is_current: boolean;
  state: "draft" | "reviewed" | "approved" | "issued" | string;
  created_at: string;
  updated_at: string;
  summary?: string;
  diff_from_previous?: {
    has_previous?: boolean;
    changed_sections?: string[];
    prompt_changed?: boolean;
    template_changed?: boolean;
    input_changed?: boolean;
  };
  artifacts: DocumentArtifact[];
  generation_metadata?: {
    source?: string;
    template_mode?: "custom" | "default" | "fallback" | string;
    template_version?: string;
    prompt_id?: string;
    prompt_version?: string;
  };
  state_history?: Array<{
    changed_by?: string;
    changed_role?: string;
    changed_at?: string;
    from_state?: string;
    to_state?: string;
    reason?: string;
  }>;
}

export interface DocumentAllowedActions {
  cliente_id: string;
  document_type: string;
  role: string;
  current_state: string;
  permissions: string[];
  allowed_next_states: string[];
}

export interface DocumentQualityCheck {
  cliente_id: string;
  document_type: string;
  document_version: number;
  state: string;
  quality_check: {
    can_approve: boolean;
    score: number;
    semaphore: "red" | "yellow" | "green" | string;
    checks: Array<{
      code: string;
      label: string;
      status: "ok" | "blocked" | string;
      detail: string;
    }>;
  };
}

export interface DocumentSectionSource {
  source_type: string;
  source_id: string;
  reference: string;
  label: string;
  linked_by?: string;
  linked_at?: string;
  mode?: string;
}

export interface DocumentSection {
  section_id: string;
  section_title: string;
  is_required: boolean;
  status: string;
  sources: DocumentSectionSource[];
  is_critical?: boolean;
  required_support_count?: number;
  linked_support_count?: number;
  coverage_percent?: number;
  blocking_reason?: string;
}

export interface DocumentSectionsPayload {
  cliente_id: string;
  document_type: string;
  document_version: number;
  sections: DocumentSection[];
  coverage: {
    total_sections: number;
    supported_sections: number;
    missing_required: number;
    coverage_percent?: number;
  };
}

export interface DocumentEvidenceGate {
  cliente_id: string;
  document_type: string;
  document_version: number;
  state: string;
  coverage_percent: number;
  minimum_required: number;
  can_approve: boolean;
  can_issue: boolean;
  enforce_on_approved: boolean;
  enforce_on_issued: boolean;
  approve_blocking_reasons: string[];
  issue_blocking_reasons: string[];
  blocking_sections: Array<{
    section_id: string;
    section_title?: string;
    reason: string;
  }>;
}

export interface DocumentSectionEvidencePayload {
  cliente_id: string;
  document_type: string;
  document_version: number;
  section: DocumentSection;
  section_content: unknown;
  artifacts: DocumentArtifact[];
  state_history: Array<Record<string, unknown>>;
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
        document_version: typeof row.document_version === "number" ? row.document_version : undefined,
        supersedes_version: typeof row.supersedes_version === "number" ? row.supersedes_version : null,
        is_current: typeof row.is_current === "boolean" ? row.is_current : undefined,
        state: typeof row.state === "string" ? row.state : undefined,
        diff_from_previous:
          typeof row.diff_from_previous === "object" && row.diff_from_previous !== null
            ? (row.diff_from_previous as ReportHistoryItem["diff_from_previous"])
            : undefined,
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

export async function getDocumentVersions(
  clienteId: string,
  documentType: string,
): Promise<{ current: DocumentVersion | null; versions: DocumentVersion[] }> {
  const response = await authFetchJson<ApiEnvelope<unknown>>(
    `/reportes/${clienteId}/documentos/${encodeURIComponent(documentType)}/versiones`,
  );
  const raw = typeof response?.data === "object" && response.data !== null ? (response.data as Record<string, unknown>) : {};
  const versionsRaw = Array.isArray(raw.versions) ? raw.versions : [];
  const versions = versionsRaw.map((item) => (item as DocumentVersion));
  const currentRaw = (raw.current ?? null) as DocumentVersion | null;
  return { versions, current: currentRaw };
}

export async function getDocumentAllowedActions(
  clienteId: string,
  documentType: string,
): Promise<DocumentAllowedActions> {
  const response = await authFetchJson<ApiEnvelope<unknown>>(
    `/reportes/${clienteId}/documentos/${encodeURIComponent(documentType)}/acciones`,
  );
  const raw = typeof response?.data === "object" && response.data !== null ? (response.data as Record<string, unknown>) : {};
  return {
    cliente_id: String(raw.cliente_id ?? clienteId),
    document_type: String(raw.document_type ?? documentType),
    role: String(raw.role ?? "staff"),
    current_state: String(raw.current_state ?? "draft"),
    permissions: Array.isArray(raw.permissions) ? raw.permissions.map((x) => String(x)) : [],
    allowed_next_states: Array.isArray(raw.allowed_next_states) ? raw.allowed_next_states.map((x) => String(x)) : [],
  };
}

export async function getDocumentQualityCheck(
  clienteId: string,
  documentType: string,
): Promise<DocumentQualityCheck> {
  const response = await authFetchJson<ApiEnvelope<unknown>>(
    `/reportes/${clienteId}/documentos/${encodeURIComponent(documentType)}/quality-check`,
  );
  return response.data as DocumentQualityCheck;
}

export async function getDocumentEvidenceGate(
  clienteId: string,
  documentType: string,
): Promise<DocumentEvidenceGate> {
  const response = await authFetchJson<ApiEnvelope<unknown>>(
    `/reportes/${clienteId}/documentos/${encodeURIComponent(documentType)}/evidence-gate`,
  );
  return response.data as DocumentEvidenceGate;
}

export async function transitionDocumentState(
  clienteId: string,
  documentType: string,
  payload: { target_state: "reviewed" | "approved" | "issued"; reason?: string },
): Promise<ApiEnvelope<{ updated_version: DocumentVersion }>> {
  return authFetchJson<ApiEnvelope<{ updated_version: DocumentVersion }>>(
    `/reportes/${clienteId}/documentos/${encodeURIComponent(documentType)}/estado`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export async function issueDocumentFinal(
  clienteId: string,
  documentType: string,
  payload: { reason?: string },
): Promise<ApiEnvelope<{
  document_version: number;
  state: string;
  issued_by: string;
  issued_at: string;
  pdf_artifact_path: string;
  pdf_artifact_hash: string;
}>> {
  return authFetchJson(`/reportes/${clienteId}/documentos/${encodeURIComponent(documentType)}/emitir`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getDocumentSections(
  clienteId: string,
  documentType: string,
): Promise<DocumentSectionsPayload> {
  const response = await authFetchJson<ApiEnvelope<unknown>>(
    `/reportes/${clienteId}/documentos/${encodeURIComponent(documentType)}/secciones`,
  );
  return response.data as DocumentSectionsPayload;
}

export async function getDocumentSectionEvidence(
  clienteId: string,
  documentType: string,
  sectionId: string,
): Promise<DocumentSectionEvidencePayload> {
  const response = await authFetchJson<ApiEnvelope<unknown>>(
    `/reportes/${clienteId}/documentos/${encodeURIComponent(documentType)}/secciones/${encodeURIComponent(sectionId)}/evidencia`,
  );
  return response.data as DocumentSectionEvidencePayload;
}

export async function linkDocumentSectionEvidence(
  clienteId: string,
  documentType: string,
  sectionId: string,
  payload: {
    source_type: string;
    source_id: string;
    reference?: string;
    label: string;
    is_required?: boolean;
  },
): Promise<ApiEnvelope<{ section: DocumentSection }>> {
  return authFetchJson(
    `/reportes/${clienteId}/documentos/${encodeURIComponent(documentType)}/secciones/${encodeURIComponent(sectionId)}/evidencia`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}
