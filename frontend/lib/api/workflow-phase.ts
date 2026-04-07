import { authFetchJson } from "../api";
import type { ApiEnvelope } from "../contracts";

export type PhaseTemplateResponse = {
  cliente_id: string;
  phase: string;
  template: {
    obligatorios: string[];
    autorrellenables: string[];
    solo_lectura_historica: string[];
  };
  prefilled: Record<string, unknown>;
  checklist: {
    missing_required: string[];
    can_advance: boolean;
  };
  field_history: Array<Record<string, unknown>>;
};

export async function getPhaseTemplate(clienteId: string, phase?: string): Promise<PhaseTemplateResponse> {
  const qs = phase ? `?phase=${encodeURIComponent(phase)}` : "";
  const response = await authFetchJson<ApiEnvelope<PhaseTemplateResponse>>(`/workflow/${clienteId}/phase-template${qs}`);
  return response.data;
}

export async function postWorkflowFieldHistory(
  clienteId: string,
  payload: {
    phase: string;
    field: string;
    old_value?: unknown;
    new_value?: unknown;
  },
): Promise<{ saved: boolean }> {
  const response = await authFetchJson<ApiEnvelope<{ saved: boolean }>>(`/workflow/${clienteId}/field-history`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return response.data;
}

