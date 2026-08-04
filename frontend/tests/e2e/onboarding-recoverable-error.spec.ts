import { expect, test, type Page, type Route } from "@playwright/test";

const FIXED_NOW = "2026-08-04T12:00:00.000Z";
const CLIENTE_ID = "demo";

type MockOptions = {
  failLoadOnce?: boolean;
  failSave?: boolean;
};

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

async function prepareOnboardingPage(page: Page, options: MockOptions = {}): Promise<void> {
  let profileLoads = 0;

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

    if ((logicalPath === "/auth/me") && method === "GET") {
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
        onboarding_ui: {
          welcome_seen: false,
          dismissed: false,
          visited_modules_ui: [],
        },
        preferences_version: "v1.2.1",
      }));
      return;
    }

    if (logicalPath === `/perfil/${CLIENTE_ID}` && method === "GET") {
      profileLoads += 1;
      if (options.failLoadOnce && profileLoads === 1) {
        await fulfillJson(route, {
          status: "error",
          code: "MENTOR_DOWN",
          message: "Servicio temporalmente no disponible",
        }, 500);
        return;
      }
      await fulfillJson(route, envelope({
        cliente_id: CLIENTE_ID,
        perfil: {
          cliente: {
            nombre_legal: "Cliente Demo SA",
            sector: "Holding",
            pais: "Ecuador",
          },
          encargo: {
            anio_activo: 2025,
            marco_referencial: "NIIF para PYMES",
            norma_auditoria: "NIAs",
            fase_actual: "planificacion",
            alcance_estados: "individual",
            esquema_visitas: "preliminar_final",
            fecha_inicio_periodo: "2025-01-01",
            fecha_cierre_periodo: "2025-12-31",
            fecha_corte_tb: "2025-12-31",
            fecha_visita_preliminar: "",
            fecha_visita_final: "",
          },
          cuestionario_auditoria: {
            nomina: false,
            inventarios: false,
            ingresos_complejos: true,
            partes_relacionadas: true,
            multi_moneda: false,
            auditado_anteriormente: false,
            opinion_anterior_calificada: false,
            cambios_management: false,
            presion_resultados: false,
            regulado: false,
            subsidiarias: false,
            litigios: false,
            estimaciones_complejas: false,
            erp_implementado: false,
          },
          carga_archivos: {
            trial_balance_nombre: "tb-demo.xlsx",
            libro_mayor_nombre: "mayor-demo.xlsx",
          },
        },
      }));
      return;
    }

    if (logicalPath === `/clientes/${CLIENTE_ID}` && method === "GET") {
      await fulfillJson(route, envelope({
        data: {
          nombre: "Cliente Demo SA",
          sector: "Holding",
          tipo_entidad: "HOLDING",
          tamano: "Mediana",
          normativa: "NIIF",
        },
      }));
      return;
    }

    if (logicalPath === "/configuracion/tipos-entidad" && method === "GET") {
      await fulfillJson(route, envelope({
        tipos: [
          { tipo: "HOLDING", nombre: "Holding" },
          { tipo: "OPERATIVA", nombre: "Operativa" },
        ],
      }));
      return;
    }

    if (logicalPath === `/context-documents/${CLIENTE_ID}` && method === "GET") {
      await fulfillJson(route, envelope({
        documents: [],
      }));
      return;
    }

    if (logicalPath === `/clientes/${CLIENTE_ID}` && method === "PATCH") {
      await fulfillJson(route, envelope({
        cliente_id: CLIENTE_ID,
        nombre: "Cliente Demo SA",
        sector: "Holding",
        tipo_entidad: "HOLDING",
        tamano: "Mediana",
        normativa: "NIIF",
      }));
      return;
    }

    if (logicalPath === `/perfil/${CLIENTE_ID}` && method === "PUT") {
      if (options.failSave) {
        await fulfillJson(route, {
          status: "error",
          code: "MENTOR_DOWN",
          message: "Servicio temporalmente no disponible",
        }, 500);
        return;
      }
      await fulfillJson(route, envelope({
        cliente_id: CLIENTE_ID,
        perfil: safeJsonBody(route),
      }));
      return;
    }

    if (logicalPath.startsWith("/trial-balance/") && method === "POST") {
      await fulfillJson(route, envelope({
        data: {
          original_name: "tb-demo.xlsx",
          stored_as: "tb-demo.xlsx",
        },
      }));
      return;
    }

    if (logicalPath.startsWith("/context-documents/") && method === "POST") {
      await fulfillJson(route, envelope({
        document: {
          id: "doc-1",
          name: "Documento anterior.pdf",
          document_type: "prior_financial_statements",
          document_label: "Estados financieros auditados anteriores",
          period: "2024",
          status: "available",
          size_bytes: 1024,
          uploaded_at: FIXED_NOW,
          document_role: "financial_statements",
          document_role_label: "Estados financieros",
        },
      }));
      return;
    }

    await route.continue();
  });
}

test.describe("Onboarding recuperable", () => {
  test("muestra error de carga y permite reintentar", async ({ page }) => {
    await prepareOnboardingPage(page, { failLoadOnce: true });

    await page.goto(`/onboarding/${CLIENTE_ID}`);

    await expect(page.getByRole("heading", { name: "No se pudo cargar el onboarding." })).toBeVisible();
    await expect(page.getByRole("button", { name: "Reintentar" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Volver a clientes" })).toBeVisible();
    await expect(page.locator("section[role='alert']")).toContainText("Servicio temporalmente no disponible");

    await page.getByRole("button", { name: "Reintentar" }).click();

    await expect(page.getByRole("button", { name: "Guardar y crear perfil de la entidad" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "1. Datos base del cliente" })).toBeVisible();
  });

  test("distingue el error de guardado sin perder la vista cargada", async ({ page }) => {
    await prepareOnboardingPage(page, { failSave: true });

    await page.goto(`/onboarding/${CLIENTE_ID}`);

    await expect(page.getByRole("heading", { name: "1. Datos base del cliente" })).toBeVisible();
    await page.getByRole("button", { name: "Guardar y crear perfil de la entidad" }).click();

    await expect(page.locator("main > div[role='alert']")).toContainText("API error 500 (MENTOR_DOWN): Servicio temporalmente no disponible");
    await expect(page.getByRole("heading", { name: "1. Datos base del cliente" })).toBeVisible();
  });
});
