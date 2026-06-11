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
  kind: string;
  uploaded_at: string;
  path: string;
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

export async function uploadClienteArchivo(
  clienteId: string,
  kind: "tb" | "mayor",
  file: File,
): Promise<{ stored_as: string; original_name: string; rows: number }> {
  // Note: Upload endpoint not available in new API
  throw new Error("uploadClienteArchivo: Endpoint not available in new API. Use database persistence instead.");
}

export async function getClienteDocumentos(clienteId: string): Promise<ClienteDocumento[]> {
  // Note: Document endpoints not available in new API
  console.warn("getClienteDocumentos: Endpoint not available in new API");
  return [];
}

export interface DocumentoIngestionResult {
  indexed: boolean;
  text_chars: number;
}

export async function uploadClienteDocumento(
  clienteId: string,
  file: File,
): Promise<{ documentos: ClienteDocumento[]; ingestion: DocumentoIngestionResult }> {
  // Note: Document upload endpoint not available in new API
  throw new Error("uploadClienteDocumento: Endpoint not available in new API. Use database persistence instead.");
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
