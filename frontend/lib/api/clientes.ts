import { authFetchJson } from "../api";
import type { ApiEnvelope } from "../contracts";

export interface ClienteOption {
  cliente_id: string;
  nombre: string;
  sector: string | null;
  tipo_entidad?: string | null;
  tamano?: string | null;
  normativa?: string | null;
}

export interface ClienteDocumento {
  id: string;
  name: string;
  document_type: string;
  document_label: string;
  period: string;
  status: "available" | "available_with_warnings" | "processing_failed" | string;
  size_bytes: number;
  uploaded_at: string;
  ingestion?: DocumentoIngestionResult;
  document_role?: string;
  document_role_label?: string;
  cutoff_date?: string;
}

export interface ClienteHallazgo {
  title: string;
  body: string;
}

export interface ClienteTbStatus {
  cliente_id: string;
  has_tb: boolean;
  has_mayor: boolean;
  has_tb_cache: boolean;
  tb_size_bytes: number;
  tb_mtime_ns: number;
}

export interface ClienteProgress {
  cliente_id: string;
  stage: string;
  completion_pct: number;
  sources: { count: number; has_prior_financials: boolean; has_tb: boolean; has_mayor: boolean };
  profile: { confirmed: boolean; analysis_ready: boolean; pending_decisions: number };
  next_action: { key: string; label: string; href: string };
}

export interface CreateClienteInput {
  cliente_id: string;
  nombre: string;
  sector?: string | null;
  tipo_entidad?: string | null;
  tamano?: string | null;
  normativa?: string | null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function asClienteOption(value: unknown): ClienteOption | null {
  if (!isRecord(value)) return null;
  // Backend may return "client_id" (SQLAlchemy model) or "cliente_id" (legacy)
  const cliente_id =
    (typeof value.cliente_id === "string" ? value.cliente_id : "") ||
    (typeof value.client_id === "string" ? value.client_id : "");
  if (!cliente_id) return null;
  const nombre = typeof value.nombre === "string" && value.nombre.trim() ? value.nombre : cliente_id;
  const sector = typeof value.sector === "string" && value.sector.trim() ? value.sector : null;
  const tipo_entidad = typeof value.tipo_entidad === "string" && value.tipo_entidad.trim() ? value.tipo_entidad : null;
  const tamano = typeof value.tamano === "string" && value.tamano.trim() ? value.tamano : null;
  const normativa = typeof value.normativa === "string" && value.normativa.trim() ? value.normativa : null;
  return { cliente_id, nombre, sector, tipo_entidad, tamano, normativa };
}

export async function getClientes(): Promise<ClienteOption[]> {
  const response = await authFetchJson<ApiEnvelope<unknown>>("/api/clientes");
  const data = isRecord(response?.data) ? response.data : {};
  const raw = Array.isArray(data.clientes) ? data.clientes : [];
  return raw.map(asClienteOption).filter((item): item is ClienteOption => item !== null);
}

export async function getClientesProgress(): Promise<ClienteProgress[]> {
  let response: ApiEnvelope<unknown>;
  try {
    response = await authFetchJson<ApiEnvelope<unknown>>("/api/clientes/progress");
  } catch (error) {
    // Compatibilidad durante despliegues escalonados: la cartera básica sigue
    // disponible aunque el backend todavía no tenga el endpoint de progreso.
    if (error instanceof Error && error.message.includes("404")) return [];
    throw error;
  }
  const data = isRecord(response?.data) ? response.data : {};
  return (Array.isArray(data.clients) ? data.clients : []).filter(isRecord).map((item) => {
    const sources = isRecord(item.sources) ? item.sources : {};
    const profile = isRecord(item.profile) ? item.profile : {};
    const next = isRecord(item.next_action) ? item.next_action : {};
    return {
      cliente_id: String(item.cliente_id ?? ""), stage: String(item.stage ?? "Fuentes pendientes"), completion_pct: Number(item.completion_pct ?? 0),
      sources: { count: Number(sources.count ?? 0), has_prior_financials: Boolean(sources.has_prior_financials), has_tb: Boolean(sources.has_tb), has_mayor: Boolean(sources.has_mayor) },
      profile: { confirmed: Boolean(profile.confirmed), analysis_ready: Boolean(profile.analysis_ready), pending_decisions: Number(profile.pending_decisions ?? 0) },
      next_action: { key: String(next.key ?? "sources"), label: String(next.label ?? "Completar fuentes"), href: String(next.href ?? "/clientes") },
    };
  }).filter((item) => item.cliente_id);
}

export async function createCliente(input: CreateClienteInput): Promise<ClienteOption> {
  const payload = {
    cliente_id: input.cliente_id.trim() || undefined,
    nombre: input.nombre.trim(),
    sector: input.sector?.trim() || null,
    tipo_entidad: input.tipo_entidad?.trim() || null,
    tamano: input.tamano?.trim() || null,
    normativa: input.normativa?.trim() || "NIIF",
  };
  const response = await authFetchJson<ApiEnvelope<unknown>>("/api/clientes", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  const cliente = asClienteOption(response?.data);
  if (!cliente) {
    throw new Error("No se pudo crear el cliente.");
  }
  return cliente;
}

export async function updateCliente(
  clienteId: string,
  input: Partial<CreateClienteInput> & { nombre?: string },
): Promise<ClienteOption> {
  const payload = {
    nombre: input.nombre?.trim() || undefined,
    sector: input.sector?.trim() || null,
    tipo_entidad: input.tipo_entidad?.trim() || null,
    tamano: input.tamano?.trim() || null,
    normativa: input.normativa?.trim() || null,
  };
  const response = await authFetchJson<ApiEnvelope<unknown>>(`/api/clientes/${clienteId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
  const cliente = asClienteOption(response?.data);
  if (!cliente) {
    throw new Error("No se pudo actualizar el cliente.");
  }
  return cliente;
}

export async function archiveCliente(clienteId: string): Promise<void> {
  // Archivado logico: el backend conserva los datos y oculta el cliente de la cartera.
  await authFetchJson<ApiEnvelope<unknown>>(`/api/clientes/${clienteId}`, {
    method: "DELETE",
  });
}

/** @deprecated Usa archiveCliente: la operacion es un archivado logico, no un borrado. */
export async function deleteCliente(clienteId: string): Promise<void> {
  await archiveCliente(clienteId);
}

export async function permanentlyDeleteCliente(clienteId: string, confirmation: string): Promise<void> {
  await authFetchJson<ApiEnvelope<unknown>>(`/api/clientes/${clienteId}/permanent`, {
    method: "DELETE",
    body: JSON.stringify({ confirmation }),
  });
}

export async function uploadClienteArchivo(
  clienteId: string,
  kind: "tb" | "mayor",
  file: File,
): Promise<{ stored_as: string; original_name: string; rows: number }> {
  // Note: Upload endpoint not available in new API
  throw new Error("uploadClienteArchivo: Endpoint not available in new API. Use database persistence instead.");
}

export async function getClienteDocumentos(clienteId: string): Promise<ClienteDocumento[]> {
  const response = await authFetchJson<ApiEnvelope<unknown>>(`/api/context-documents/${clienteId}`);
  const data = isRecord(response?.data) ? response.data : {};
  const raw = Array.isArray(data.documents) ? data.documents : [];
  return raw.filter(isRecord).map((item) => ({
    id: typeof item.id === "string" ? item.id : "",
    name: typeof item.name === "string" ? item.name : "Documento",
    document_type: typeof item.document_type === "string" ? item.document_type : "other",
    document_label: typeof item.document_label === "string" ? item.document_label : "Documento de contexto",
    period: typeof item.period === "string" ? item.period : "",
    status: typeof item.status === "string" ? item.status : "processing_failed",
    size_bytes: typeof item.size_bytes === "number" ? item.size_bytes : 0,
    uploaded_at: typeof item.uploaded_at === "string" ? item.uploaded_at : "",
    ingestion: isRecord(item.ingestion)
      ? parseIngestion(item.ingestion)
      : undefined,
    document_role: typeof item.document_role === "string" ? item.document_role : "other",
    document_role_label: typeof item.document_role_label === "string" ? item.document_role_label : "Otro",
    cutoff_date: typeof item.cutoff_date === "string" ? item.cutoff_date : "",
  })).filter((item) => item.id);
}

export interface DocumentoIngestionResult {
  indexed: boolean;
  text_chars: number;
  extraction_method?: "native" | "ocr" | "metadata_only" | string;
  page_count?: number;
  pages_with_text?: number;
  ocr_used?: boolean;
  ocr_recommended?: boolean;
}

function parseIngestion(item: Record<string, unknown>): DocumentoIngestionResult {
  return {
    indexed: Boolean(item.indexed), text_chars: Number(item.text_chars || 0),
    extraction_method: typeof item.extraction_method === "string" ? item.extraction_method : undefined,
    page_count: typeof item.page_count === "number" ? item.page_count : undefined,
    pages_with_text: typeof item.pages_with_text === "number" ? item.pages_with_text : undefined,
    ocr_used: Boolean(item.ocr_used), ocr_recommended: Boolean(item.ocr_recommended),
  };
}

export async function uploadClienteDocumento(
  clienteId: string,
  file: File,
  documentType: "prior_financial_statements" | "prior_internal_control" | "current_preliminary_financials" | "accounting_policy" | "contract" | "other" = "other",
  period = "",
  documentRole = "other",
  cutoffDate = "",
): Promise<ClienteDocumento> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("document_type", documentType);
  formData.append("period", period);
  formData.append("document_role", documentRole);
  formData.append("cutoff_date", cutoffDate);
  const response = await authFetchJson<ApiEnvelope<unknown>>(`/api/context-documents/${clienteId}`, {
    method: "POST",
    body: formData,
  });
  const data = isRecord(response?.data) ? response.data : {};
  const document = isRecord(data.document) ? data.document : {};
  if (typeof document.id !== "string" || !document.id) {
    throw new Error("No se pudo registrar el documento de contexto.");
  }
  return {
    id: document.id,
    name: typeof document.name === "string" ? document.name : file.name,
    document_type: typeof document.document_type === "string" ? document.document_type : documentType,
    document_label: typeof document.document_label === "string" ? document.document_label : "Documento de contexto",
    period: typeof document.period === "string" ? document.period : period,
    status: typeof document.status === "string" ? document.status : "processing_failed",
    size_bytes: typeof document.size_bytes === "number" ? document.size_bytes : file.size,
    uploaded_at: typeof document.uploaded_at === "string" ? document.uploaded_at : "",
    ingestion: isRecord(document.ingestion)
      ? parseIngestion(document.ingestion)
      : undefined,
    document_role: typeof document.document_role === "string" ? document.document_role : documentRole,
    document_role_label: typeof document.document_role_label === "string" ? document.document_role_label : "Otro",
    cutoff_date: typeof document.cutoff_date === "string" ? document.cutoff_date : cutoffDate,
  };
}

export async function deleteClienteDocumento(clienteId: string, documentId: string): Promise<void> {
  await authFetchJson<ApiEnvelope<unknown>>(`/api/context-documents/${clienteId}/${documentId}`, { method: "DELETE" });
}

export async function reprocessClienteDocumento(clienteId: string, documentId: string): Promise<void> {
  await authFetchJson<ApiEnvelope<unknown>>(`/api/context-documents/${clienteId}/${documentId}/reprocess`, { method: "POST" });
}

export async function getClienteHallazgos(clienteId: string): Promise<ClienteHallazgo[]> {
  // Note: Hallazgos endpoint moved to separate API
  console.warn("getClienteHallazgos: Endpoint deprecated. Use /api/hallazgos instead");
  return [];
}

export async function getClienteTbStatus(clienteId: string): Promise<ClienteTbStatus> {
  const response = await authFetchJson<ApiEnvelope<unknown>>(`/api/trial-balance/${clienteId}/status`);
  const data = isRecord(response?.data) ? response.data : {};
  return {
    cliente_id: typeof data.cliente_id === "string" ? data.cliente_id : clienteId,
    has_tb: Boolean(data.has_tb),
    has_mayor: Boolean(data.has_mayor),
    has_tb_cache: Boolean(data.has_tb_cache),
    tb_size_bytes: typeof data.tb_size_bytes === "number" ? data.tb_size_bytes : 0,
    tb_mtime_ns: typeof data.tb_mtime_ns === "number" ? data.tb_mtime_ns : 0,
  };
}
