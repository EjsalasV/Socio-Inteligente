import { authFetchJson } from "../api";
import type { ApiEnvelope } from "../contracts";

export type MentorGuide = {
  status: "ready";
  learning_role: "junior" | "semi" | "senior" | "socio";
  observation: string;
  why_relevant: string;
  guided_questions: string[];
  next_steps: string[];
  watch_outs: string[];
  concepts: Array<{ term: string; explanation: string }>;
  mentor_challenge: string;
  no_conclusion_note: string;
  model?: { model?: string; input_tokens?: string; output_tokens?: string };
  accepted_context_counts: Record<string, number>;
  disclaimer: string;
};

export type MentorAccountInput = {
  area_code: string;
  area_name: string;
  account_code: string;
  account_name: string;
  current_balance: number;
  prior_balance: number;
  variation_pct: number;
  area_assertions: Array<{
    nombre: string;
    descripcion: string;
    riesgo_tipico: string;
    procedimiento_clave: string;
  }>;
  area_accounts: Array<{
    code: string;
    name: string;
    current_balance: number;
    prior_balance: number;
    variation_pct: number;
  }>;
  force?: boolean;
};

export type MentorConversationTurn = {
  turn_number: number;
  created_at: string;
  auditor_response: string;
  mentor: {
    feedback: string;
    strength: string;
    reasoning_gap: string;
    follow_up_question: string;
    hint: string;
    progress_stage: "observe" | "connect" | "test" | "reflect";
    ready_to_continue: boolean;
    safety_note: string;
    recommended_resources?: {
      procedures: Array<{ id: string; title: string; nia_ref: string; assertion: string; why: string; href: string; source: string }>;
      norms: Array<{ code: string; title: string; category: string; why: string; href: string; source: string }>;
    };
  };
};

export type MentorReplyResult = {
  session_id: string;
  turn: MentorConversationTurn;
  turns_used: number;
  turns_remaining: number;
  learning_role: MentorGuide["learning_role"];
  memory_classification: "educational_dialogue_not_audit_evidence";
};

export async function getAccountMentorGuide(clienteId: string, input: MentorAccountInput): Promise<MentorGuide> {
  const response = await authFetchJson<ApiEnvelope<MentorGuide>>(`/api/mentor/${clienteId}/account`, {
    method: "POST",
    body: JSON.stringify(input),
  });
  return response.data;
}

export async function replyToMentor(
  clienteId: string,
  input: { session_id?: string; auditor_response: string; account_context: Record<string, unknown> },
): Promise<MentorReplyResult> {
  const response = await authFetchJson<ApiEnvelope<MentorReplyResult>>(`/api/mentor/${clienteId}/reply`, {
    method: "POST",
    body: JSON.stringify(input),
  });
  return response.data;
}
