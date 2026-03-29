import { authFetchJson } from "../api";
import type { ApiEnvelope } from "../contracts";

export interface ClienteOption {
  cliente_id: string;
  nombre: string;
  sector: string | null;
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
