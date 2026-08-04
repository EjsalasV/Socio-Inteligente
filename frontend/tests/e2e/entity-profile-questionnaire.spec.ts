import { expect, test, type Page, type Route } from "@playwright/test";

type EntityProfileQuestion = {
  id: string;
  text: string;
  reason: string;
  critical: boolean;
  round: number;
};

type EntityProfileAnalysis = {
  status: "ready";
  entity_summary: {
    activity: string;
    revenue_model: string;
    regulatory_context: string;
    confidence: number;
    evidence_refs: string[];
  };
  changes: Array<{ id: string; title: string; why_it_matters: string; confidence: number; evidence_refs: string[]; decision: { status: "pending" } }>;
  prior_findings: Array<{ id: string; title: string; why_it_matters: string; confidence: number; evidence_refs: string[]; decision: { status: "pending" } }>;
  risk_hypotheses: Array<{ id: string; title: string; why_it_matters: string; confidence: number; evidence_refs: string[]; decision: { status: "pending" } }>;
  estimate_hypotheses: Array<{ id: string; title: string; why_relevant: string; confidence: number; evidence_refs: string[]; decision: { status: "pending" } }>;
  missing_information: string[];
  sources: Array<{ source_id: string; name: string; period: string }>;
  input_chars: number;
  disclaimer: string;
};

type DraftPayload = {
  cliente_id: string;
  status: "needs_answers" | "provisional" | "confirmed";
  generated_at: string;
  facts: Array<{ key: string; label: string; value: string; source: string; status: string }>;
  sources: Array<{ type: string; label: string; available: boolean; status: string; authority: string }>;
  questions: EntityProfileQuestion[];
  active_round: number;
  max_rounds: number;
  answers: Record<string, string>;
  unanswered_critical: string[];
  pending_confirmations: string[];
  pending_items: Array<Record<string, never>>;
  limitations: string[];
  transparency_note: string;
  analysis?: EntityProfileAnalysis;
};

const FIXED_NOW = "2026-08-04T12:00:00.000Z";
const CLIENTE_ID = "demo";

function envelope<T>(data: T): { status: "ok"; data: T; meta: { timestamp: string } } {
  return {
    status: "ok",
    data,
    meta: { timestamp: FIXED_NOW },
  };
}

function safeJsonBody(route: Route): Record<string, unknown> {
  try {
    const body = route.request().postDataJSON();
    return typeof body === "object" && body !== null ? (body as Record<string, unknown>) : {};
  } catch {
    return {};
  }
}

async function fulfillJson(route: Route, data: unknown, status = 200): Promise<void> {
  await route.fulfill({
    status,
    json: data,
  });
}

function buildQuestions(): EntityProfileQuestion[] {
  return [
    {
      id: "q1",
      text: "¿La entidad mantiene nómina formal?",
      reason: "Ayuda a distinguir costos de personal y riesgos laborales.",
      critical: true,
      round: 1,
    },
    {
      id: "q2",
      text: "¿Existen inventarios relevantes?",
      reason: "Permite decidir si hace falta trabajo específico sobre existencia y valuación.",
      critical: false,
      round: 1,
    },
    {
      id: "q3",
      text: "¿La entidad consolida subsidiarias?",
      reason: "Ajusta el alcance cuando hay grupo y eliminaciones.",
      critical: false,
      round: 2,
    },
  ];
}

function buildDraft(overrides: Partial<DraftPayload> = {}): DraftPayload {
  return {
    cliente_id: CLIENTE_ID,
    status: "needs_answers",
    generated_at: FIXED_NOW,
    facts: [
      { key: "legal_name", label: "Nombre legal", value: "Cliente Demo SA", source: "onboarding", status: "confirmed" },
      { key: "period", label: "Periodo", value: "2025", source: "onboarding", status: "confirmed" },
      { key: "accounting_framework", label: "Marco contable", value: "NIIF para PYMES", source: "onboarding", status: "confirmed" },
    ],
    sources: [
      { type: "onboarding", label: "Onboarding", available: true, status: "available", authority: "Sistema" },
    ],
    questions: buildQuestions(),
    active_round: 1,
    max_rounds: 2,
    answers: {},
    unanswered_critical: ["q1"],
    pending_confirmations: [],
    pending_items: [],
    limitations: [],
    transparency_note: "Las respuestas se validan sin usar IA real.",
    ...overrides,
  };
}

function buildAnalysis(): EntityProfileAnalysis {
  return {
    status: "ready",
    entity_summary: {
      activity: "Prestación de servicios profesionales",
      revenue_model: "Honorarios por contratos recurrentes",
      regulatory_context: "NIIF para PYMES y NIAs",
      confidence: 0.93,
      evidence_refs: ["Onboarding", "Fuentes confirmadas"],
    },
    changes: [
      {
        id: "change-1",
        title: "Crecimiento de ingresos",
        why_it_matters: "Puede cambiar el enfoque de pruebas sobre corte y reconocimiento.",
        confidence: 0.72,
        evidence_refs: ["Ingresos"],
        decision: { status: "pending" },
      },
    ],
    prior_findings: [
      {
        id: "prior-1",
        title: "Sin inventarios significativos",
        why_it_matters: "Reduce el alcance sobre existencias.",
        confidence: 0.84,
        evidence_refs: ["Onboarding"],
        decision: { status: "pending" },
      },
    ],
    risk_hypotheses: [
      {
        id: "risk-1",
        title: "Riesgo de reconocimiento de ingresos",
        why_it_matters: "Debe validarse con evidencia suficiente y apropiada.",
        confidence: 0.88,
        evidence_refs: ["Ingresos"],
        decision: { status: "pending" },
      },
    ],
    estimate_hypotheses: [
      {
        id: "est-1",
        title: "Deterioro de cartera",
        why_relevant: "Requiere revisar supuestos y cobrabilidad.",
        confidence: 0.76,
        evidence_refs: ["CxC"],
        decision: { status: "pending" },
      },
    ],
    missing_information: [],
    sources: [{ source_id: "s1", name: "Onboarding", period: "2025" }],
    input_chars: 1234,
    disclaimer: "Salida simulada para pruebas E2E.",
  };
}

async function prepareEntityProfile(page: Page, options: { failSave422Once?: boolean } = {}): Promise<void> {
  let savedAnswersCount = 0;
  let draft = buildDraft();

  await page.addInitScript(
    ({ csrfToken, authToken }) => {
      window.localStorage.setItem("socio_session_active", "1");
      window.localStorage.setItem("socio_csrf_token", csrfToken);
      window.sessionStorage.setItem("socio_auth_token", authToken);
      window.localStorage.setItem("socio_auth_token", authToken);
    },
    { csrfToken: "csrf-qa", authToken: "jwt-qa" },
  );

  await page.route("**/*", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const { pathname } = url;
    const logicalPath = pathname.startsWith("/api/") ? pathname.slice(4) : pathname;
    const method = request.method().toUpperCase();

    if (
      !pathname.startsWith("/auth/") &&
      !pathname.startsWith("/api/auth/") &&
      !pathname.startsWith("/api/") &&
      !pathname.startsWith("/dashboard/") &&
      !pathname.startsWith("/risk-engine/") &&
      !pathname.startsWith("/workflow/") &&
      !pathname.startsWith("/chat/")
    ) {
      await route.continue();
      return;
    }

    if (logicalPath === "/auth/me" && method === "GET") {
      await fulfillJson(route, envelope({
        sub: "entity-profile-tester",
        user_id: "entity-profile-tester",
        display_name: "QA Auditor",
        role: "auditor",
        org_id: "org_demo",
        allowed_clientes: [CLIENTE_ID],
      }));
      return;
    }

    if (logicalPath === "/user/preferences" && method === "GET") {
      await fulfillJson(route, envelope({
        learning_role: "semi",
        tour_completed_modules: [],
        tour_welcome_seen: false,
        onboarding_ui: {
          welcome_seen: false,
          dismissed: false,
          visited_modules_ui: [],
        },
        preferences_version: "v1.2.1",
      }));
      return;
    }

    if (logicalPath === `/entity-profile/${CLIENTE_ID}/draft` && method === "GET") {
      await fulfillJson(route, envelope(draft));
      return;
    }

    if (logicalPath === `/entity-profile/${CLIENTE_ID}/answers` && method === "PUT") {
      if (options.failSave422Once && savedAnswersCount === 0) {
        savedAnswersCount += 1;
        await fulfillJson(
          route,
          {
            status: "error",
            code: "PROFILE_422",
            message: "Las respuestas no cumplen la validación mínima.",
          },
          422,
        );
        return;
      }

      const body = safeJsonBody(route);
      const answers = typeof body.answers === "object" && body.answers !== null ? (body.answers as Record<string, string>) : {};
      savedAnswersCount += 1;
      const activeRound = savedAnswersCount === 1 ? 2 : 2;
      const mergedAnswers = { ...draft.answers, ...answers };
      draft = buildDraft({
        active_round: activeRound,
        answers: mergedAnswers,
        unanswered_critical: [],
        questions: buildQuestions(),
      });
      await fulfillJson(route, envelope(draft));
      return;
    }

    if (logicalPath === `/entity-profile/${CLIENTE_ID}/analyze` && method === "POST") {
      await fulfillJson(route, envelope(buildAnalysis()));
      return;
    }

    await route.continue();
  });
}

test.describe("Cuestionario adaptativo", () => {
  test("muestra una pregunta por vez, conserva respuestas y abre el resultado final", async ({ page }) => {
    await prepareEntityProfile(page);

    await page.goto(`/entity-profile/${CLIENTE_ID}`);

    await expect(page.getByRole("heading", { name: "¿La entidad mantiene nómina formal?" })).toBeVisible();
    await expect(page.getByText("¿La entidad consolida subsidiarias?", { exact: true })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Continuar" })).toBeDisabled();

    const answerBox = page.getByRole("textbox", { name: "Respuesta del auditor" });
    await answerBox.fill("Sí, existe nómina formal y contratos laborales.");
    await expect(page.getByRole("button", { name: "Continuar" })).toBeEnabled();

    await page.getByRole("button", { name: "Continuar" }).click();
    await expect(page.getByRole("heading", { name: "¿Existen inventarios relevantes?" })).toBeVisible();

    await page.getByRole("button", { name: "Anterior" }).click();
    await expect(answerBox).toHaveValue("Sí, existe nómina formal y contratos laborales.");

    await page.getByRole("button", { name: "Continuar" }).click();
    await expect(page.getByRole("heading", { name: "¿Existen inventarios relevantes?" })).toBeVisible();
    await page.getByRole("textbox", { name: "Respuesta del auditor" }).fill("No existen inventarios relevantes.");
    await page.getByRole("button", { name: "Evaluar esta ronda" }).click();

    await expect(page.getByText("Necesito una aclaración adicional.")).toBeVisible();
    await expect(page.getByRole("heading", { name: "¿La entidad consolida subsidiarias?" })).toBeVisible();
    await expect(page.getByRole("textbox", { name: "Respuesta del auditor" })).toHaveValue("");
  });

  test("la segunda ronda abre el resultado final y permite volver a la entrevista", async ({ page }) => {
    await prepareEntityProfile(page);

    await page.goto(`/entity-profile/${CLIENTE_ID}`);

    const answerBox = page.getByRole("textbox", { name: "Respuesta del auditor" });
    await answerBox.fill("Sí, existe nómina formal y contratos laborales.");
    await page.getByRole("button", { name: "Continuar" }).click();
    await expect(page.getByRole("heading", { name: "¿Existen inventarios relevantes?" })).toBeVisible();
    await page.getByRole("textbox", { name: "Respuesta del auditor" }).fill("No existen inventarios relevantes.");
    await page.getByRole("button", { name: "Evaluar esta ronda" }).click();
    await expect(page.getByRole("heading", { name: "¿La entidad consolida subsidiarias?" })).toBeVisible();
    await page.getByRole("textbox", { name: "Respuesta del auditor" }).fill("No consolida subsidiarias.");
    await page.getByRole("button", { name: "Evaluar esta ronda" }).click();

    await expect(page.getByRole("heading", { name: /Ya tengo una primera comprensión de la entidad/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Lo que SocioAI entendió" })).toBeVisible();

    await page.getByRole("button", { name: "Modificar respuestas que originaron este resumen" }).click();

    await expect(page.getByRole("heading", { name: /Conozcamos esta entidad/i })).toBeVisible();
    await expect(page.getByRole("button", { name: "Evaluar esta ronda" })).toBeVisible();
  });

  test("un error 422 conserva las respuestas del cuestionario", async ({ page }) => {
    await prepareEntityProfile(page, { failSave422Once: true });

    await page.goto(`/entity-profile/${CLIENTE_ID}`);

    const answerBox = page.getByRole("textbox", { name: "Respuesta del auditor" });
    await answerBox.fill("Sí, existe nómina formal y contratos laborales.");
    await page.getByRole("button", { name: "Continuar" }).click();
    await expect(page.getByRole("heading", { name: "¿Existen inventarios relevantes?" })).toBeVisible();
    await page.getByRole("textbox", { name: "Respuesta del auditor" }).fill("No existen inventarios relevantes.");
    await page.getByRole("button", { name: "Evaluar esta ronda" }).click();

    await expect(
      page.getByRole("alert").filter({ hasText: "La información enviada no pasó la validación" }).first(),
    ).toBeVisible();
    await expect(page.getByRole("textbox", { name: "Respuesta del auditor" })).toHaveValue("No existen inventarios relevantes.");
    await expect(page.getByRole("heading", { name: "¿La entidad consolida subsidiarias?" })).not.toBeVisible();
  });
});
