export type UiErrorSummary = {
  status?: number;
  title: string;
  detail: string;
};

function extractErrorText(error: unknown): string {
  if (error instanceof Error && typeof error.message === "string") {
    return error.message.trim();
  }
  if (typeof error === "string") {
    return error.trim();
  }
  return "";
}

function parseHttpStatus(text: string): number | undefined {
  const match = text.match(/API error (\d{3})/i);
  if (!match) return undefined;
  const status = Number(match[1]);
  return Number.isFinite(status) ? status : undefined;
}

function extractMessage(text: string): string {
  const match = text.match(/API error \d{3}(?: \([^)]+\))?:\s*(.*)$/i);
  return (match?.[1] || text).trim();
}

export function summarizeUiError(error: unknown, fallback: string, context = "esta acción"): UiErrorSummary {
  const text = extractErrorText(error);
  const status = parseHttpStatus(text);

  if (text.toLowerCase().includes("sesion expirada") || text.toLowerCase().includes("session expired")) {
    return {
      status: 401,
      title: "Sesión expirada",
      detail: "Tu sesión expiró. Vuelve a iniciar sesión para continuar.",
    };
  }

  if (status === 404) {
    return {
      status,
      title: "Recurso no encontrado",
      detail: `No encontramos ${context}.`,
    };
  }

  if (status === 409) {
    return {
      status,
      title: "Conflicto de actualización",
      detail: "Hay un proceso en curso o una versión distinta de este registro. Espera a que termine y vuelve a intentarlo.",
    };
  }

  if (status === 422) {
    return {
      status,
      title: "Validación rechazada",
      detail: "La información enviada no pasó la validación. Revisa los datos y vuelve a intentarlo.",
    };
  }

  if (status === 500) {
    return {
      status,
      title: "Error interno del servidor",
      detail: "El servidor tuvo un problema interno. Inténtalo de nuevo en unos minutos.",
    };
  }

  if (status) {
    return {
      status,
      title: `Error ${status}`,
      detail: extractMessage(text) || fallback,
    };
  }

  return {
    title: "No se pudo completar la acción",
    detail: text || fallback,
  };
}
