import { authFetchJson } from "../api";
import type { ApiEnvelope } from "../contracts";

export type EntityProfileFact = {
  key: string;
  label: string;
  value: unknown;
  source: string;
  status: string;
};

export type EntityProfileSource = {
  type: string;
  label: string;
  name?: string;
  period?: string;
  available: boolean;
  status: string;
  authority: string;
};

export type EntityProfileQuestion = {
  id: string;
  text: string;
  reason: string;
  critical: boolean;
  round: number;
};

export type EntityProfilePendingItem = {
  question_id: string;
  question: string;
  reason: string;
  area: string;
  impact: string;
  answer: string;
  status: "pending" | "requested" | "received" | "confirmed" | "not_applicable";
  created_at: string;
  updated_at: string;
};

export type EntityProfileHypothesis = {
  id?: string;
  title: string;
  why_it_matters?: string;
  why_relevant?: string;
  affected_areas?: string[];
  assertions?: string[];
  inputs_to_understand?: string[];
  follow_up_question?: string;
  evidence_needed?: string[];
  confidence?: number;
  evidence_refs?: string[];
  status?: "proposed" | "accepted" | "rejected" | string;
  decision?: {
    status: "pending" | "accepted" | "rejected" | "antecedent" | "current_hypothesis" | "discarded" | "pending_validation";
    decided_by?: string;
    decided_at?: string;
    edited_title?: string;
    edited_reason?: string;
  };
};

export type EntityProfileAnalysis = {
  status: "ready";
  entity_summary?: {
    activity?: string;
    revenue_model?: string;
    regulatory_context?: string;
    confidence?: number;
    evidence_refs?: string[];
  };
  changes: EntityProfileHypothesis[];
  prior_findings: EntityProfileHypothesis[];
  risk_hypotheses: EntityProfileHypothesis[];
  estimate_hypotheses: EntityProfileHypothesis[];
  missing_information?: string[];
  sources: Array<{ source_id: string; name?: string; period?: string }>;
  model?: { provider?: string; model?: string; input_tokens?: string; output_tokens?: string };
  input_chars: number;
  disclaimer: string;
};

export type EntityProfileDraft = {
  cliente_id: string;
  status: "needs_answers" | "provisional" | "confirmed";
  generated_at: string;
  facts: EntityProfileFact[];
  sources: EntityProfileSource[];
  questions: EntityProfileQuestion[];
  active_round: number;
  max_rounds: number;
  answers: Record<string, string>;
  unanswered_critical: string[];
  pending_confirmations: string[];
  pending_items: EntityProfilePendingItem[];
  limitations: string[];
  transparency_note: string;
  confirmed_by?: string;
  confirmed_at?: string;
  analysis?: EntityProfileAnalysis;
};

export async function getEntityProfileDraft(clienteId: string): Promise<EntityProfileDraft> {
  const response = await authFetchJson<ApiEnvelope<EntityProfileDraft>>(
    `/api/entity-profile/${clienteId}/draft`,
  );
  return response.data;
}

export async function saveEntityProfileAnswers(
  clienteId: string,
  answers: Record<string, string>,
): Promise<EntityProfileDraft> {
  const response = await authFetchJson<ApiEnvelope<EntityProfileDraft>>(
    `/api/entity-profile/${clienteId}/answers`,
    { method: "PUT", body: JSON.stringify({ answers }) },
  );
  return response.data;
}

export async function confirmEntityProfile(clienteId: string): Promise<EntityProfileDraft> {
  const response = await authFetchJson<ApiEnvelope<EntityProfileDraft>>(
    `/api/entity-profile/${clienteId}/confirm`,
    { method: "POST" },
  );
  return response.data;
}

export async function updateEntityProfilePending(
  clienteId: string,
  questionId: string,
  input: { status: EntityProfilePendingItem["status"]; answer: string },
): Promise<EntityProfileDraft> {
  const response = await authFetchJson<ApiEnvelope<EntityProfileDraft>>(
    `/api/entity-profile/${clienteId}/pending/${encodeURIComponent(questionId)}`,
    { method: "PUT", body: JSON.stringify(input) },
  );
  return response.data;
}

export async function analyzeEntityProfile(
  clienteId: string,
  force = false,
): Promise<EntityProfileAnalysis> {
  const response = await authFetchJson<ApiEnvelope<EntityProfileAnalysis>>(
    `/api/entity-profile/${clienteId}/analyze`,
    { method: "POST", body: JSON.stringify({ force }) },
  );
  return response.data;
}

export async function decideEntityProfileHypothesis(
  clienteId: string,
  input: { hypothesis_id: string; status: "pending" | "accepted" | "rejected" | "antecedent" | "current_hypothesis" | "discarded" | "pending_validation"; edited_title?: string; edited_reason?: string },
): Promise<EntityProfileAnalysis> {
  const response = await authFetchJson<ApiEnvelope<EntityProfileAnalysis>>(
    `/api/entity-profile/${clienteId}/analysis/decision`,
    { method: "PUT", body: JSON.stringify(input) },
  );
  return response.data;
}
