import { authFetchJson } from "../api";
import type { ApiEnvelope } from "../contracts";

export type TipoEntidadOption = {
  tipo: string;
  nombre: string;
};

export type PreguntaDinamica = {
  id: string;
  texto: string;
  tipo: "select" | "text";
  opciones?: Array<{ valor: string; label: string }>;
  default?: string;
  critica?: boolean;
  ayuda?: string;
  placeholder?: string;
};

export type ClienteConfiguracion = {
  tipo_entidad: string;
  respuestas: Record<string, string>;
  updated_at?: string | null;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

export async function getTiposEntidad(): Promise<TipoEntidadOption[]> {
  const response = await authFetchJson<ApiEnvelope<unknown>>("/api/configuracion/tipos-entidad");
  const data = isRecord(response?.data) ? response.data : {};
  const tipos = Array.isArray(data.tipos) ? data.tipos : [];
  return tipos
    .map((item) => {
      if (!isRecord(item)) return null;
      return {
        tipo: typeof item.tipo === "string" ? item.tipo : "",
        nombre: typeof item.nombre === "string" ? item.nombre : "",
      };
    })
    .filter((item): item is TipoEntidadOption => Boolean(item?.tipo));
}

export async function getPreguntasDinamicas(tipoEntidad: string): Promise<PreguntaDinamica[]> {
  if (!tipoEntidad.trim()) return [];
  const response = await authFetchJson<ApiEnvelope<unknown>>(`/api/configuracion/${tipoEntidad}/preguntas`);
  const data = isRecord(response?.data) ? response.data : {};
  const preguntas = Array.isArray(data.preguntas) ? data.preguntas : [];
  const parsed: PreguntaDinamica[] = [];
  for (const item of preguntas) {
    if (!isRecord(item)) continue;
    const id = typeof item.id === "string" ? item.id : "";
    if (!id) continue;
    parsed.push({
      id,
      texto: typeof item.texto === "string" ? item.texto : "",
      tipo: item.tipo === "select" ? "select" : "text",
      opciones: Array.isArray(item.opciones)
        ? item.opciones
            .map((opt) => {
              if (!isRecord(opt)) return null;
              return {
                valor: typeof opt.valor === "string" ? opt.valor : "",
                label: typeof opt.label === "string" ? opt.label : "",
              };
            })
            .filter((opt): opt is { valor: string; label: string } => Boolean(opt?.valor))
        : undefined,
      default: typeof item.default === "string" ? item.default : "",
      critica: item.critica === true,
      ayuda: typeof item.ayuda === "string" ? item.ayuda : "",
      placeholder: typeof item.placeholder === "string" ? item.placeholder : "",
    });
  }
  return parsed;
}

export async function getClienteConfiguracion(clienteId: string): Promise<ClienteConfiguracion | null> {
  const response = await authFetchJson<ApiEnvelope<unknown>>(`/api/configuracion/${clienteId}/obtener`);
  const data = isRecord(response?.data) ? response.data : {};
  const configuracion = isRecord(data.configuracion) ? data.configuracion : null;
  if (!configuracion) return null;
  return {
    tipo_entidad: typeof configuracion.tipo_entidad === "string" ? configuracion.tipo_entidad : "",
    respuestas: isRecord(configuracion.respuestas)
      ? Object.fromEntries(Object.entries(configuracion.respuestas).map(([key, value]) => [key, String(value ?? "")]))
      : {},
    updated_at: typeof configuracion.updated_at === "string" ? configuracion.updated_at : null,
  };
}

export async function saveClienteConfiguracion(
  clienteId: string,
  payload: { tipo_entidad: string; respuestas: Record<string, string> },
): Promise<ClienteConfiguracion> {
  const response = await authFetchJson<ApiEnvelope<unknown>>(`/api/configuracion/${clienteId}/guardar`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  const data = isRecord(response?.data) ? response.data : {};
  return {
    tipo_entidad: typeof data.tipo_entidad === "string" ? data.tipo_entidad : payload.tipo_entidad,
    respuestas: isRecord(data.respuestas)
      ? Object.fromEntries(Object.entries(data.respuestas).map(([key, value]) => [key, String(value ?? "")]))
      : payload.respuestas,
    updated_at: typeof data.updated_at === "string" ? data.updated_at : null,
  };
}
