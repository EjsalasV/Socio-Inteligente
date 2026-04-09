import { authFetchJson, TokenExpiredError } from "../api";
import type { ApiEnvelope } from "../contracts";
import type { ClienteProfileData, PerfilPayload } from "../../types/perfil";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function normalizePerfilResponse(clienteId: string, raw: unknown): ClienteProfileData {
  const data = isRecord(raw) ? raw : {};
  const profileRoot = isRecord(data.perfil) ? data.perfil : {};
  const resolvedId = typeof data.cliente_id === "string" && data.cliente_id.trim() ? data.cliente_id : clienteId;

  return {
    cliente_id: resolvedId,
    perfil: profileRoot,
  };
}

export async function getPerfil(clienteId: string): Promise<ClienteProfileData> {
  try {
    const response = await authFetchJson<ApiEnvelope<unknown>>(`/perfil/${clienteId}`);
    return normalizePerfilResponse(clienteId, response?.data);
  } catch (error) {
    if (error instanceof TokenExpiredError) {
      throw new TokenExpiredError("La sesión expiró. Vuelve a iniciar sesión.");
    }
    throw error;
  }
}

export async function savePerfil(clienteId: string, perfil: PerfilPayload): Promise<ClienteProfileData> {
  try {
    const response = await authFetchJson<ApiEnvelope<unknown>>(`/perfil/${clienteId}`, {
      method: "PUT",
      body: JSON.stringify(perfil),
    });
    return normalizePerfilResponse(clienteId, response?.data);
  } catch (error) {
    if (error instanceof TokenExpiredError) {
      throw new TokenExpiredError("La sesión expiró. Vuelve a iniciar sesión.");
    }
    throw error;
  }
}
