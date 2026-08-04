import { expect, test, type Page, type Route } from "@playwright/test";

const CLIENTE_ID = "demo";
const FIXED_NOW = "2026-08-03T12:00:00.000Z";

function envelope<T>(data: T): { status: "ok"; data: T; meta: { timestamp: string } } {
  return { status: "ok", data, meta: { timestamp: FIXED_NOW } };
}

async function fulfillJson(route: Route, data: unknown, status = 200): Promise<void> {
  await route.fulfill({ status, json: data });
}

function dashboardPayload() {
  return {
    cliente_id: CLIENTE_ID,
    nombre_cliente: "Cliente Demo SA",
    periodo: "2025",
    sector: "Retail",
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
    materialidad_por_area: [],
    top_areas_page: 1,
    top_areas_page_size: 8,
    top_areas_total: 1,
    top_areas_has_more: false,
  };
}

async function applySessionMocks(page: Page): Promise<void> {
  await page.addInitScript(
    ({ csrfToken, authToken }) => {
      window.localStorage.setItem("socio_session_active", "1");
      window.localStorage.setItem("socio_csrf_token", csrfToken);
      window.sessionStorage.setItem("socio_auth_token", authToken);
      window.localStorage.setItem("socio_auth_token", authToken);
      const nativeFetch = window.fetch.bind(window);
      window.fetch = async (input, init) => {
        const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
        const pathname = new URL(url, window.location.origin).pathname;
        const logicalPath = pathname.startsWith("/api/") ? pathname.slice(4) : pathname;
        if (logicalPath === "/auth/me") {
          return new Response(JSON.stringify({ status: "ok", data: { sub: "mentor-user" }, meta: { timestamp: "2026-08-03T12:00:00.000Z" } }), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          });
        }
        return nativeFetch(input, init);
      };
    },
    { csrfToken: "csrf-qa", authToken: "jwt-qa" },
  );

  await page.route("**/*", async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    const logicalPath = pathname.startsWith("/api/") ? pathname.slice(4) : pathname;
    if (logicalPath === "/auth/me") {
      await fulfillJson(route, envelope({
        sub: "mentor-user",
        user_id: "mentor-user",
        display_name: "Mentor QA",
        role: "auditor",
        org_id: "org_demo",
        allowed_clientes: [CLIENTE_ID],
      }));
      return;
    }
    if (logicalPath === "/user/preferences") {
      await fulfillJson(route, envelope({
        learning_role: "semi",
        tour_completed_modules: [],
        tour_welcome_seen: false,
        onboarding_ui: { welcome_seen: false, dismissed: false, visited_modules_ui: [] },
        preferences_version: "v1.2.1",
      }));
      return;
    }
    if (pathname.startsWith("/api/")) {
      await fulfillJson(route, envelope({}));
      return;
    }
    await route.continue();
  });
}

async function openAuthenticated(page: Page, path: string): Promise<void> {
  await page.goto("/landing");
  await page.evaluate(() => {
    window.localStorage.setItem("socio_session_active", "1");
    window.localStorage.setItem("socio_csrf_token", "csrf-qa");
    window.localStorage.setItem("socio_auth_token", "jwt-qa");
    window.sessionStorage.setItem("socio_auth_token", "jwt-qa");
  });
  await page.goto(path);
}

async function prepareDashboard(page: Page): Promise<void> {
  await page.route("**/*", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const { pathname } = url;
    const logicalPath = pathname.startsWith("/api/") ? pathname.slice(4) : pathname;
    const method = request.method().toUpperCase();

    if (!pathname.startsWith("/api/") && !pathname.startsWith("/dashboard/")) {
      await route.continue();
      return;
    }

    if (logicalPath === "/dashboard/demo" && method === "GET" && url.searchParams.has("areas_page")) {
      await fulfillJson(route, envelope(dashboardPayload()));
      return;
    }

    if (logicalPath === "/auth/me" && method === "GET") {
      await fulfillJson(route, envelope({
        sub: "mentor-user",
        user_id: "mentor-user",
        display_name: "Mentor QA",
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
        onboarding_ui: { welcome_seen: false, dismissed: false, visited_modules_ui: [] },
        preferences_version: "v1.2.1",
      }));
      return;
    }

    if (logicalPath === "/alertas/demo" && method === "GET") {
      await fulfillJson(route, envelope({ alertas: [], total_criticos: 0, total_altos: 0 }));
      return;
    }

    if (logicalPath === "/clientes" && method === "GET") {
      await fulfillJson(route, envelope({
        clientes: [
          {
            cliente_id: CLIENTE_ID,
            nombre: "Cliente Demo SA",
            sector: "Retail",
          },
        ],
      }));
      return;
    }

    if (logicalPath === "/clientes/progress" && method === "GET") {
      await fulfillJson(route, envelope({ clients: [] }));
      return;
    }

    if (logicalPath === "/workflow/demo" && method === "GET") {
      await fulfillJson(route, envelope({
        cliente_id: CLIENTE_ID,
        previous_phase: "planificacion",
        current_phase: "ejecucion",
        changed: true,
        gates: [
          { code: "wf1", title: "Archivo base", status: "ok", detail: "Completo" },
        ],
      }));
      return;
    }

    if (logicalPath === "/trial-balance/demo/status" && method === "GET") {
      await fulfillJson(route, envelope({
        cliente_id: CLIENTE_ID,
        has_tb: true,
        has_mayor: true,
        has_tb_cache: true,
        tb_size_bytes: 1024,
        tb_mtime_ns: 1234567890,
      }));
      return;
    }

    if (logicalPath === "/risk-engine/demo" && method === "GET") {
      await fulfillJson(route, envelope({
        cliente_id: CLIENTE_ID,
        eje_x: "Impacto",
        eje_y: "Frecuencia",
        quadrants: [],
        areas_criticas: [],
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

    if (pathname.startsWith("/dashboard/") && method === "GET") {
      await route.continue();
      return;
    }

    throw new Error(`Unexpected API request: ${method} ${pathname}${url.search}`);
  });
}

function entityProfileDraftPayload() {
  return {
    cliente_id: CLIENTE_ID,
    status: "confirmed",
    generated_at: FIXED_NOW,
    facts: [
      { key: "legal_name", label: "Nombre legal", value: "Cliente Demo SA", source: "onboarding", status: "confirmed" },
      { key: "period", label: "Periodo", value: "2025", source: "onboarding", status: "confirmed" },
      { key: "accounting_framework", label: "Marco contable", value: "NIIF para PYMES", source: "onboarding", status: "confirmed" },
    ],
    sources: [],
    questions: [],
    active_round: 1,
    max_rounds: 1,
    answers: {},
    unanswered_critical: [],
    pending_confirmations: [],
    pending_items: [],
    limitations: [],
    transparency_note: "Perfil preparado para revisión.",
    confirmed_by: "mentor-qa",
    confirmed_at: FIXED_NOW,
    analysis: {
      status: "ready",
      entity_summary: {
        activity: "Retail",
        revenue_model: "Venta directa",
        regulatory_context: "NIIF para PYMES",
        confidence: 0.88,
        evidence_refs: [],
      },
      changes: [],
      prior_findings: [],
      risk_hypotheses: [],
      estimate_hypotheses: [],
      missing_information: [],
      sources: [],
      model: { provider: "mock", model: "qa", input_tokens: "0", output_tokens: "0" },
      input_chars: 0,
      disclaimer: "Prueba simulada.",
    },
  };
}

async function prepareEntityProfile(page: Page): Promise<void> {
  await applySessionMocks(page);
  await page.route("**/api/entity-profile/demo/draft", async (route) => {
    await fulfillJson(route, envelope(entityProfileDraftPayload()));
  });
}

test.describe("Estados vacios", () => {
  test.use({
    storageState: {
      cookies: [],
      origins: [{
        origin: "http://127.0.0.1:3000",
        localStorage: [
          { name: "socio_session_active", value: "1" },
          { name: "socio_csrf_token", value: "csrf-qa" },
          { name: "socio_auth_token", value: "jwt-qa" },
        ],
      }],
    },
  });

  test("muestra un estado visible cuando no hay alertas de riesgo", async ({ page }) => {
    await applySessionMocks(page);
    await prepareDashboard(page);
    await openAuthenticated(page, `/dashboard/${CLIENTE_ID}`);

    await expect(page.getByRole("heading", { name: /dashboard/i }).first()).toBeVisible();
    await expect(page.getByText("Sin alertas activas")).toBeVisible();
    await expect(page.getByText("No hay alertas abiertas para este cliente. Cuando aparezcan, se mostrarán aquí sin bloquear la navegación.")).toBeVisible();
  });

  test("muestra biblioteca sin resultados cuando el filtro no coincide", async ({ page }) => {
    await applySessionMocks(page);
    await page.route("**/api/normativa/catalogo", async (route) => {
      await fulfillJson(route, envelope({ normas: [] }));
    });
    await openAuthenticated(page, "/biblioteca");

    await expect(page.getByRole("textbox", { name: "Buscar norma" })).toBeVisible();
    await page.getByLabel("Buscar norma").fill("xyz-no-match");
    await expect(page.getByText("No hay normas para mostrar con el filtro actual.")).toBeVisible();
  });

  test("muestra procedimientos sin coincidencias al filtrar areas", async ({ page }) => {
    await applySessionMocks(page);
    await page.route("**/api/areas", async (route) => {
      await fulfillJson(route, envelope({
        areas: [
          { area_codigo: "410", area_nombre: "Ingresos", procedures_count: 4 },
          { area_codigo: "510", area_nombre: "Compras", procedures_count: 2 },
        ],
      }));
    });
    await page.route("**/api/areas/*/procedimientos", async (route) => {
      await fulfillJson(route, envelope({
        area_codigo: "410",
        area_nombre: "Ingresos",
        procedimientos: [
          {
            id: "proc-1",
            descripcion: "Prueba de ingresos",
            tipo: "analitico",
            afirmacion: "exactitud",
            obligatorio: true,
            nia_ref: "NIA 500",
          },
        ],
        riesgos_tipicos: [],
        alertas_tributarias: [],
        requerimientos: [],
      }));
    });

    await openAuthenticated(page, "/procedimientos");
    await expect(page.getByRole("textbox", { name: "Buscar area" })).toBeVisible();
    await expect(page.getByRole("button", { name: /Ingresos/ })).toBeVisible();
    await page.getByLabel("Buscar area").fill("xyz-no-match");

    await expect(page.getByText("No hay areas para el filtro actual.")).toBeVisible();
  });

  test("muestra vacios consistentes en el perfil cuando no hay fuentes anteriores ni hipotesis", async ({ page }) => {
    await prepareEntityProfile(page);
    await openAuthenticated(page, `/entity-profile/${CLIENTE_ID}`);

    await expect(page.getByText("Resultado del conocimiento del cliente")).toBeVisible();
    await expect(page.getByText("No se identificaron fuentes anteriores.").last()).toBeVisible();
    await expect(page.getByText("No se identificaron antecedentes.")).toBeVisible();
    await expect(page.locator("p:visible").filter({ hasText: "No se identificaron hipótesis por validar." })).toBeVisible();
  });
});
