import { authFetchJson } from "../api";
import type { ApiEnvelope } from "../contracts";
import type { WorkflowPhase, WorkflowState } from "../../types/workflow";

function asString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function normalize(raw: unknown, clienteId: string): WorkflowState {
  const data = typeof raw === "object" && raw !== null ? (raw as Record<string, unknown>) : {};
  const gates = Array.isArray(data.gates)
    ? data.gates
        .map((item) => (typeof item === "object" && item !== null ? (item as Record<string, unknown>) : null))
        .filter(Boolean)
        .map((g) => ({
          code: asString(g?.code),
          title: asString(g?.title),
          status: (asString(g?.status, "blocked") as "ok" | "blocked"),
          detail: asString(g?.detail),
        }))
    : [];

  return {
    cliente_id: asString(data.cliente_id, clienteId),
    previous_phase: asString(data.previous_phase, "planificacion") as WorkflowPhase,
    current_phase: asString(data.current_phase, "planificacion") as WorkflowPhase,
    changed: Boolean(data.changed),
    gates,
  };
}

export async function getWorkflowState(clienteId: string): Promise<WorkflowState> {
  const response = await authFetchJson<ApiEnvelope<unknown>>(`/workflow/${clienteId}`);
  return normalize(response?.data, clienteId);
}

export async function advanceWorkflow(clienteId: string, targetPhase?: WorkflowPhase): Promise<WorkflowState> {
  const response = await authFetchJson<ApiEnvelope<unknown>>(`/workflow/${clienteId}/advance`, {
    method: "POST",
    body: JSON.stringify({ target_phase: targetPhase ?? null }),
  });
  return normalize(response?.data, clienteId);
}
