import { authFetchJson } from "../api";
import type { ApiEnvelope } from "../contracts";

export interface ClienteOption {
  cliente_id: string;
  nombre: string;
  sector: string | null;
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

export interface CreateClienteInput {
  cliente_id: string;
  nombre: string;
  sector?: string | null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function asClienteOption(value: unknown): ClienteOption | null {
  if (!isRecord(value)) return null;
  const cliente_id = typeof value.cliente_id === "string" ? value.cliente_id : "";
  if (!cliente_id) return null;
  const nombre = typeof value.nombre === "string" && value.nombre.trim() ? value.nombre : cliente_id;
  const sector = typeof value.sector === "string" && value.sector.trim() ? value.sector : null;
  return { cliente_id, nombre, sector };
}

export async function getClientes(): Promise<ClienteOption[]> {
  const response = await authFetchJson<ApiEnvelope<unknown>>("/clientes");
  const raw = response?.data;
  if (!Array.isArray(raw)) return [];
  return raw.map(asClienteOption).filter((item): item is ClienteOption => item !== null);
}

export async function createCliente(input: CreateClienteInput): Promise<ClienteOption> {
  const payload = {
    cliente_id: input.cliente_id.trim(),
    nombre: input.nombre.trim(),
    sector: input.sector?.trim() || null,
  };
  const response = await authFetchJson<ApiEnvelope<unknown>>("/clientes", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  const cliente = asClienteOption(response?.data);
  if (!cliente) {
    throw new Error("No se pudo crear el cliente.");
  }
  return cliente;
}

export async function deleteCliente(clienteId: string): Promise<void> {
  await authFetchJson<ApiEnvelope<unknown>>(`/clientes/${clienteId}`, {
    method: "DELETE",
  });
}

export async function uploadClienteArchivo(
  clienteId: string,
  kind: "tb" | "mayor",
  file: File,
): Promise<{ stored_as: string; original_name: string; rows: number }> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await authFetchJson<ApiEnvelope<unknown>>(
    `/clientes/${clienteId}/upload/${kind}`,
    {
      method: "POST",
      body: formData,
    },
  );

  const data = isRecord(response?.data) ? response.data : {};
  return {
    stored_as: typeof data.stored_as === "string" ? data.stored_as : "",
    original_name: typeof data.original_name === "string" ? data.original_name : file.name,
    rows: typeof data.rows === "number" ? data.rows : 0,
  };
}

export async function getClienteDocumentos(clienteId: string): Promise<ClienteDocumento[]> {
  const response = await authFetchJson<ApiEnvelope<unknown>>(`/clientes/${clienteId}/documentos`);
  const raw: unknown[] = Array.isArray(response?.data) ? response.data : [];
  return raw
    .map((item: unknown) => {
      if (!isRecord(item)) return null;
      return {
        id: typeof item.id === "string" ? item.id : "",
        name: typeof item.name === "string" ? item.name : "",
        kind: typeof item.kind === "string" ? item.kind : "documento",
        uploaded_at: typeof item.uploaded_at === "string" ? item.uploaded_at : "",
        path: typeof item.path === "string" ? item.path : "",
      };
    })
    .filter((item: ClienteDocumento | null): item is ClienteDocumento => item !== null && Boolean(item.id));
}

export interface DocumentoIngestionResult {
  indexed: boolean;
  text_chars: number;
}

export async function uploadClienteDocumento(
  clienteId: string,
  file: File,
): Promise<{ documentos: ClienteDocumento[]; ingestion: DocumentoIngestionResult }> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await authFetchJson<ApiEnvelope<unknown>>(`/clientes/${clienteId}/documentos/upload`, {
    method: "POST",
    body: formData,
  });
  const data = isRecord(response?.data) ? response.data : {};
  const docs: unknown[] = Array.isArray(data.documentos) ? data.documentos : [];
  const documentos = docs
    .map((item: unknown) => {
      if (!isRecord(item)) return null;
      return {
        id: typeof item.id === "string" ? item.id : "",
        name: typeof item.name === "string" ? item.name : "",
        kind: typeof item.kind === "string" ? item.kind : "documento",
        uploaded_at: typeof item.uploaded_at === "string" ? item.uploaded_at : "",
        path: typeof item.path === "string" ? item.path : "",
      };
    })
    .filter((item: ClienteDocumento | null): item is ClienteDocumento => item !== null && Boolean(item.id));
  const ingestionRaw = isRecord(data.ingestion) ? data.ingestion : {};
  return {
    documentos,
    ingestion: {
      indexed: Boolean(ingestionRaw.indexed),
      text_chars: typeof ingestionRaw.text_chars === "number" ? ingestionRaw.text_chars : 0,
    },
  };
}

export async function getClienteHallazgos(clienteId: string): Promise<ClienteHallazgo[]> {
  const response = await authFetchJson<ApiEnvelope<unknown>>(`/clientes/${clienteId}/hallazgos`);
  const raw: unknown[] = Array.isArray(response?.data) ? response.data : [];
  return raw
    .map((item: unknown) => {
      if (!isRecord(item)) return null;
      return {
        title: typeof item.title === "string" ? item.title : "Hallazgo",
        body: typeof item.body === "string" ? item.body : "",
      };
    })
    .filter((item: ClienteHallazgo | null): item is ClienteHallazgo => item !== null);
}
