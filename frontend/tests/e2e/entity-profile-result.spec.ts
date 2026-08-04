import { expect, test, type Page, type Route } from "@playwright/test";

type DecisionStatus = "antecedent" | "current_hypothesis" | "discarded" | "pending_validation";

type DraftQuestion = {
  id: string;
  text: string;
  reason: string;
  critical: boolean;
  round: number;
};

type DraftPayload = {
  cliente_id: string;
  status: "needs_answers" | "provisional" | "confirmed";
  generated_at: string;
  facts: Array<{ key: string; label: string; value: string; source: string; status: string }>;
  sources: Array<{ type: string; label: string; name: string; period: string; available: boolean; status: string; authority: string }>;
  questions: DraftQuestion[];
  active_round: number;
  max_rounds: number;
  answers: Record<string, string>;
  unanswered_critical: string[];
  pending_confirmations: string[];
  pending_items: Array<Record<string, never>>;
  limitations: string[];
  transparency_note: string;
  analysis: AnalysisPayload;
  confirmed_by?: string;
  confirmed_at?: string;
};

type AnalysisItem = {
  id: string;
  title: string;
  why_it_matters?: string;
  why_relevant?: string;
  confidence: number;
  evidence_refs: string[];
  decision: { status: "pending" | DecisionStatus };
};

type AnalysisPayload = {
  status: "ready";
  entity_summary: {
    activity: string;
    revenue_model: string;
    regulatory_context: string;
    confidence: number;
    evidence_refs: string[];
  };
  changes: AnalysisItem[];
  prior_findings: AnalysisItem[];
  risk_hypotheses: AnalysisItem[];
  estimate_hypotheses: AnalysisItem[];
  missing_information: string[];
  sources: Array<{ source_id: string; name: string; period: string }>;
  input_chars: number;
  disclaimer: string;
};

type MockOptions = {
  failDecisionStatus?: DecisionStatus;
  failConfirmOnce?: boolean;
};

const FIXED_NOW = "2026-08-04T12:30:00.000Z";
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

function safeJsonString(raw: string | null): Record<string, unknown> {
  if (!raw) return {};
  try {
    const parsed = JSON.parse(raw);
    return typeof parsed === "object" && parsed !== null ? (parsed as Record<string, unknown>) : {};
  } catch {
    return {};
  }
}

async function fulfillJson(route: Route, data: unknown, status = 200): Promise<void> {
  await route.fulfill({ status, json: data });
}

function baseAnalysis(): AnalysisPayload {
  return {
    status: "ready",
    entity_summary: {
      activity: "Servicios profesionales",
      revenue_model: "Honorarios por proyectos y contratos recurrentes",
      regulatory_context: "NIIF para PYMES y NIAs",
      confidence: 0.94,
      evidence_refs: ["Onboarding", "Estados anteriores"],
    },
    prior_findings: [
      {
        id: "prior-1",
        title: "Ventas parciales",
        why_it_matters: "Ayuda a distinguir continuidad del negocio y corte de ingresos.",
        confidence: 0.84,
        evidence_refs: ["Informe 2024"],
        decision: { status: "pending" },
      },
    ],
    changes: [
      {
        id: "change-1",
        title: "Crecimiento en contratos",
        why_it_matters: "Puede exigir ampliar pruebas sobre reconocimiento de ingresos.",
        confidence: 0.79,
        evidence_refs: ["Contrato", "Factura"],
        decision: { status: "pending" },
      },
    ],
    risk_hypotheses: [
      {
        id: "risk-1",
        title: "Riesgo de reconocimiento de ingresos",
        why_it_matters: "Debe validarse con evidencia suficiente y apropiada.",
        confidence: 0.91,
        evidence_refs: ["Ingresos", "Contratos"],
        decision: { status: "pending" },
      },
    ],
    estimate_hypotheses: [
      {
        id: "est-1",
        title: "Deterioro de cartera",
        why_relevant: "Requiere revisar supuestos y cobrabilidad.",
        confidence: 0.73,
        evidence_refs: ["CxC"],
        decision: { status: "pending" },
      },
    ],
    missing_information: [],
    sources: [{ source_id: "s1", name: "Onboarding", period: "2025" }],
    input_chars: 1492,
    disclaimer: "Simulación de pruebas E2E sin IA real.",
  };
}

function buildDraft(): DraftPayload {
  return {
    cliente_id: CLIENTE_ID,
    status: "confirmed",
    generated_at: FIXED_NOW,
    facts: [
      { key: "legal_name", label: "Nombre legal", value: "Cliente Demo SA", source: "onboarding", status: "confirmed" },
      { key: "period", label: "Periodo", value: "2025", source: "onboarding", status: "confirmed" },
      { key: "accounting_framework", label: "Marco contable", value: "NIIF para PYMES", source: "onboarding", status: "confirmed" },
    ],
    sources: [
      { type: "onboarding", label: "Onboarding", name: "Onboarding", period: "2025", available: true, status: "available", authority: "Sistema" },
      { type: "prior_financial_statements", label: "Estados financieros anteriores", name: "Informe 2024", period: "2024", available: true, status: "available", authority: "Repositorio" },
    ],
    questions: [
      { id: "q1", text: "¿Hay nómina formal?", reason: "Aporta contexto operativo.", critical: true, round: 1 },
      { id: "q2", text: "¿Hay inventarios?", reason: "No afecta el resumen final.", critical: false, round: 1 },
    ],
    active_round: 1,
    max_rounds: 2,
    answers: {
      q1: "Sí, existe nómina formal.",
      q2: "No hay inventarios relevantes.",
    },
    unanswered_critical: [],
    pending_confirmations: [],
    pending_items: [],
    limitations: ["Las hipótesis permanecen separadas de los hechos confirmados."],
    transparency_note: "Las respuestas del auditor se muestran sin usar IA real.",
    analysis: baseAnalysis(),
    confirmed_by: "auditor-qa",
    confirmed_at: FIXED_NOW,
  };
}

function withDecisionStatus(analysis: AnalysisPayload, status: DecisionStatus): AnalysisPayload {
  const next = structuredClone(analysis) as AnalysisPayload;
  for (const collection of [next.prior_findings, next.changes, next.risk_hypotheses, next.estimate_hypotheses]) {
    for (const item of collection) {
      if (item.id) item.decision.status = status;
    }
  }
  return next;
}

async function prepareEntityProfile(page: Page, options: MockOptions = {}): Promise<void> {
  let decisionFailureTriggered = false;
  let confirmFailureTriggered = false;
  let currentAnalysis = baseAnalysis();

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
    const pathname = url.pathname;
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
      await fulfillJson(route, envelope(buildDraft()));
      return;
    }

    if (logicalPath === `/entity-profile/${CLIENTE_ID}/answers` && method === "PUT") {
      await fulfillJson(route, envelope(buildDraft()));
      return;
    }

    if (logicalPath === `/entity-profile/${CLIENTE_ID}/analysis/decision` && method === "PUT") {
      const body = safeJsonBody(route);
      const status = String(body.status || "") as DecisionStatus;
      if (options.failDecisionStatus === status && !decisionFailureTriggered) {
        decisionFailureTriggered = true;
        await fulfillJson(route, {
          status: "error",
          code: "PROFILE_DECISION_INVALID",
          message: "La decisión no cumple la validación mínima.",
        }, 422);
        return;
      }
      currentAnalysis = withDecisionStatus(currentAnalysis, status || "pending_validation");
      await fulfillJson(route, envelope(currentAnalysis));
      return;
    }

    if (logicalPath === `/entity-profile/${CLIENTE_ID}/confirm` && method === "POST") {
      if (options.failConfirmOnce && !confirmFailureTriggered) {
        confirmFailureTriggered = true;
        await fulfillJson(route, {
          status: "error",
          code: "PROFILE_CONFIRMATION_INCOMPLETE",
          message: "Aún faltan respuestas por confirmar.",
        }, 422);
        return;
      }
      await fulfillJson(route, envelope(buildDraft()));
      return;
    }

    if (logicalPath === `/dashboard/${CLIENTE_ID}` && method === "GET") {
      await fulfillJson(route, envelope({
        cliente_id: CLIENTE_ID,
        nombre_cliente: "Cliente Demo SA",
        periodo: "2025",
        sector: "Servicios",
        riesgo_global: "MEDIO",
        balance: { activo: 100, pasivo: 60, patrimonio: 40, ingresos: 120, gastos: 70 },
        progreso: { pct_completado: 55 },
        top_areas: [
          { codigo: "410", nombre: "Ingresos", score_riesgo: 0.82, prioridad: "alta", saldo_total: 50000, con_saldo: true },
        ],
        materialidad_global: 1000,
        materialidad_ejecucion: 800,
        umbral_trivial: 50,
        materialidad_origen: "regla",
        tb_stage: "con_saldos",
        fase_actual: "ejecucion",
        workflow_phase: "ejecucion",
        workflow_gates: [{ code: "wf1", title: "Archivo base", status: "ok", detail: "Completo" }],
        balance_status: "cuadrado",
        resultado_periodo: 50,
        balance_delta: 0,
        materialidad_detalle: {
          nia_base: "NIA 320",
          base_usada: "Ingresos",
          base_valor: 120,
          porcentaje_aplicado: 0.5,
          porcentaje_rango_min: 0.5,
          porcentaje_rango_max: 1,
          criterio_seleccion_pct: "medio",
          origen_regla: "sector",
          minimum_threshold_aplicado: 25,
          minimum_threshold_origen: "cliente",
        },
        materialidad_por_area: [
          {
            area_codigo: "410",
            area_nombre: "Ingresos",
            porcentaje_aplicado: 0.5,
            base_referencia: 120,
            materialidad_sugerida: 60,
          },
        ],
        top_areas_page: 1,
        top_areas_page_size: 8,
        top_areas_total: 1,
        top_areas_has_more: false,
      }));
      return;
    }

    if (logicalPath === `/risk-engine/${CLIENTE_ID}` && method === "GET") {
      await fulfillJson(route, envelope({
        cliente_id: CLIENTE_ID,
        eje_x: "Impacto",
        eje_y: "Frecuencia",
        quadrants: [[{ row: 1, col: 1, frecuencia: 1, impacto: 1, score: 0.2, nivel: "BAJO", area_id: "410", area_nombre: "Ingresos" }]],
        areas_criticas: [
          {
            area_id: "410",
            area_nombre: "Ingresos",
            score: 9,
            nivel: "ALTO",
            frecuencia: 4,
            impacto: 5,
            hallazgos_abiertos: 1,
            drivers: ["Corte"],
            score_components: {},
          },
        ],
        strategy: {
          approach: "Mixto",
          control_pct: 40,
          substantive_pct: 60,
          rationale: "Datos suficientes para priorizar.",
          control_tests: [],
          substantive_tests: [],
        },
        recommended_tests: [],
        sin_datos: false,
        mensaje: "",
      }));
      return;
    }

    if (logicalPath === `/workflow/${CLIENTE_ID}` && method === "GET") {
      await fulfillJson(route, envelope({
        cliente_id: CLIENTE_ID,
        previous_phase: "planificacion",
        current_phase: "ejecucion",
        changed: true,
        gates: [{ code: "wf1", title: "Archivo base", status: "ok", detail: "Completo" }],
      }));
      return;
    }

    if (logicalPath === `/chat/${CLIENTE_ID}/conversations` && method === "GET") {
      await fulfillJson(route, envelope({
        conversations: [
          {
            id: "conv-1",
            title: "Cierre de mes",
            created_at: FIXED_NOW,
            updated_at: FIXED_NOW,
          },
        ],
      }));
      return;
    }

    if (logicalPath === `/chat/${CLIENTE_ID}/history` && method === "GET") {
      await fulfillJson(route, envelope({
        messages: [
          {
            role: "assistant",
            text: "Historial del Mentor listo para usar.",
            timestamp: FIXED_NOW,
            citations: [],
            confidence: 0.91,
          },
        ],
      }));
      return;
    }

    await route.continue();
  });
}

test.describe("Resultado del perfil", () => {
  test("se puede expandir por teclado y las decisiones usan el endpoint correcto", async ({ page }) => {
    const decisionCalls: Array<{ status: string; path: string }> = [];
    await prepareEntityProfile(page, { failDecisionStatus: "discarded" });

    page.on("request", (request) => {
      const pathname = new URL(request.url()).pathname;
      const logicalPath = pathname.startsWith("/api/") ? pathname.slice(4) : pathname;
      if (logicalPath === "/entity-profile/demo/analysis/decision" && request.method().toUpperCase() === "PUT") {
        const body = safeJsonString(request.postData());
        decisionCalls.push({ status: String(body.status || ""), path: logicalPath });
      }
    });

    await page.goto(`/entity-profile/${CLIENTE_ID}`);

    await expect(page.getByRole("heading", { name: /Ya tengo una primera comprensión de la entidad/ })).toBeVisible();
    await expect(page.locator("article").first().getByText("Resumen propuesto")).toBeVisible();
    await expect(page.locator("header").getByText("Cliente Demo SA")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Período anterior" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Período actual" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Riesgos por validar" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Por comprender" })).toBeVisible();

    const antecedentCard = page.locator("details").filter({ hasText: "Ventas parciales" }).first();
    await antecedentCard.locator("summary").press("Enter");
    await expect(antecedentCard.getByRole("button", { name: "Conservar antecedente" })).toBeVisible();
    await antecedentCard.getByRole("button", { name: "Conservar antecedente" }).click();

    const changeCard = page.locator("details").filter({ hasText: "Crecimiento en contratos" }).first();
    await changeCard.locator("summary").press("Enter");
    await changeCard.getByRole("button", { name: "Hipótesis actual" }).click();

    const riskCard = page.locator("details").filter({ hasText: "Riesgo de reconocimiento de ingresos" }).first();
    await riskCard.locator("summary").press("Enter");
    await riskCard.getByRole("button", { name: "Descartar" }).click();
    await expect(page.locator("main [role='alert']").first()).toContainText("La información enviada no pasó la validación.");

    await riskCard.getByRole("button", { name: "Descartar" }).click();

    const estimateCard = page.locator("details").filter({ hasText: "Deterioro de cartera" }).first();
    await estimateCard.locator("summary").press("Enter");
    await estimateCard.getByRole("button", { name: "Pendiente" }).click();

    expect(decisionCalls).toEqual([
      { path: "/entity-profile/demo/analysis/decision", status: "antecedent" },
      { path: "/entity-profile/demo/analysis/decision", status: "current_hypothesis" },
      { path: "/entity-profile/demo/analysis/decision", status: "discarded" },
      { path: "/entity-profile/demo/analysis/decision", status: "discarded" },
      { path: "/entity-profile/demo/analysis/decision", status: "pending_validation" },
    ]);
  });

  test("confirmar navega al Mentor solo con éxito y el error de confirmación no cambia de pantalla", async ({ page }) => {
    await prepareEntityProfile(page, { failConfirmOnce: true });

    await page.goto(`/entity-profile/${CLIENTE_ID}`);
    await expect(page.getByRole("heading", { name: /Ya tengo una primera comprensión de la entidad/ })).toBeVisible();

    await page.getByRole("button", { name: "Confirmar perfil y entrar al Mentor" }).click();
    await expect(page.locator("main [role='alert']").first()).toContainText("La información enviada no pasó la validación.");
    await expect(page).toHaveURL(/\/entity-profile\/demo$/);

    await page.getByRole("button", { name: "Confirmar perfil y entrar al Mentor" }).click();
    await expect(page).toHaveURL(/\/socio-chat\/demo$/);
  });
});
