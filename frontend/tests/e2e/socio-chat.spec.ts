import { expect, test, type Page, type Route } from "@playwright/test";

type LearningRole = "junior" | "semi" | "senior" | "socio";

type ChatConversation = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
};

type ChatMessage = {
  role: "user" | "assistant";
  text: string;
  timestamp: string;
  citations?: Array<Record<string, unknown>>;
  confidence?: number;
};

type MockOptions = {
  learningRole?: LearningRole;
  conversations?: ChatConversation[];
  histories?: Record<string, ChatMessage[]>;
  chatResponse?: {
    answer: string;
    citations?: Array<Record<string, unknown>>;
    confidence?: number;
    mode_used?: string;
    web_search_used?: boolean;
    expert_criteria_used?: boolean;
  };
  failChat?: boolean;
};

const FIXED_NOW = "2026-08-03T12:00:00.000Z";
const CLIENTE_ID = "demo";

function envelope<T>(data: T): { status: "ok"; data: T; meta: { timestamp: string } } {
  return {
    status: "ok",
    data,
    meta: { timestamp: FIXED_NOW },
  };
}

function iso(offsetMinutes = 0): string {
  return new Date(Date.parse(FIXED_NOW) + offsetMinutes * 60_000).toISOString();
}

function chatConversation(id: string, title: string): ChatConversation {
  return {
    id,
    title,
    created_at: iso(),
    updated_at: iso(5),
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

async function prepareSocioChat(page: Page, options: MockOptions = {}): Promise<{ chatBodies: string[] }> {
  const conversations = options.conversations ?? [chatConversation("c-001", "Cierre de mes")];
  const histories: Record<string, ChatMessage[]> = options.histories ?? {
    "c-001": [
      {
        role: "user",
        text: "Histórico inicial",
        timestamp: iso(-15),
      },
      {
        role: "assistant",
        text: "Respuesta previa",
        timestamp: iso(-14),
      },
    ],
  };
  const chatBodies: string[] = [];
  const preferences = {
    learning_role: options.learningRole ?? "semi",
    tour_completed_modules: [],
    tour_welcome_seen: false,
    onboarding_ui: {
      welcome_seen: false,
      dismissed: false,
      visited_modules_ui: [],
    },
    preferences_version: "v1.2.1",
  };

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
      await fulfillJson(route, envelope(preferences));
      return;
    }

    if (logicalPath === "/user/preferences" && method === "PATCH") {
      const patch = safeJsonBody(route);
      if (typeof patch.learning_role === "string") {
        preferences.learning_role = patch.learning_role as LearningRole;
      }
      await fulfillJson(route, envelope(preferences));
      return;
    }

    if (logicalPath.startsWith("/dashboard/") && method === "GET") {
      await fulfillJson(route, envelope({
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
        workflow_gates: [
          { code: "wf1", title: "Archivo base", status: "ok", detail: "Completo" },
        ],
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

    if (logicalPath.startsWith("/risk-engine/") && method === "GET") {
      await fulfillJson(route, envelope({
        cliente_id: CLIENTE_ID,
        eje_x: "Impacto",
        eje_y: "Frecuencia",
        quadrants: [
          [
            { row: 1, col: 1, frecuencia: 1, impacto: 1, score: 0.2, nivel: "BAJO", area_id: "410", area_nombre: "Ingresos" },
          ],
        ],
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

    if (logicalPath.startsWith("/workflow/") && method === "GET") {
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

    if (logicalPath.startsWith(`/trial-balance/${CLIENTE_ID}/status`) && method === "GET") {
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

    if (logicalPath === `/chat/${CLIENTE_ID}/conversations` && method === "GET") {
      await fulfillJson(route, envelope({ conversations }));
      return;
    }

    if (logicalPath === `/chat/${CLIENTE_ID}/conversations` && method === "POST") {
      const body = safeJsonBody(route);
      const title = String(body.title || "Nueva conversación").trim() || "Nueva conversación";
      const created = chatConversation(`c-${conversations.length + 1}`.padStart(5, "0"), title);
      conversations.unshift(created);
      histories[created.id] = [];
      await fulfillJson(route, envelope({ conversation: created }));
      return;
    }

    if (logicalPath.startsWith(`/chat/${CLIENTE_ID}/conversations/`) && method === "PATCH") {
      const conversationId = logicalPath.split("/").pop() || "";
      const body = safeJsonBody(route);
      const row = conversations.find((item) => item.id === conversationId);
      if (!row) {
        await fulfillJson(route, { status: "error", code: "CONVERSATION_NOT_FOUND", message: "Conversación no encontrada." }, 404);
        return;
      }
      row.title = String(body.title || row.title).trim() || row.title;
      row.updated_at = iso(10);
      await fulfillJson(route, envelope({ conversation: row }));
      return;
    }

    if (logicalPath.startsWith(`/chat/${CLIENTE_ID}/conversations/`) && method === "DELETE") {
      const conversationId = logicalPath.split("/").pop() || "";
      const index = conversations.findIndex((item) => item.id === conversationId);
      if (index === -1) {
        await fulfillJson(route, { status: "error", code: "CONVERSATION_NOT_FOUND", message: "Conversación no encontrada." }, 404);
        return;
      }
      conversations.splice(index, 1);
      delete histories[conversationId];
      await fulfillJson(route, envelope({ deleted: true }));
      return;
    }

    if (logicalPath === `/chat/${CLIENTE_ID}/history` && method === "GET") {
      const conversationId = url.searchParams.get("conversation_id") || conversations[0]?.id || "";
      await fulfillJson(route, envelope({ messages: histories[conversationId] ?? [] }));
      return;
    }

    if (logicalPath === `/chat/${CLIENTE_ID}` && method === "POST") {
      const body = safeJsonBody(route);
      chatBodies.push(String(body.message || ""));
      if (options.failChat) {
        await fulfillJson(route, {
          status: "error",
          code: "MENTOR_DOWN",
          message: "Servicio temporalmente no disponible",
        }, 500);
        return;
      }

      await fulfillJson(route, envelope({
        cliente_id: CLIENTE_ID,
        answer:
          options.chatResponse?.answer ||
          "## Evaluación\n- **Importante**: revisar el corte\n- Ver [NIA 315](https://example.com/nia315)",
        citations:
          options.chatResponse?.citations ||
          [
            {
              source: "docs/normativa/nia_315.md",
              excerpt: "Identificación y valoración del riesgo.",
              norma: "NIA 315",
              title: "NIA 315",
            },
            {
              source: "https://example.com/soporte",
              excerpt: "Referencia externa de apoyo.",
              norma: "Web",
              title: "Sitio web de respaldo",
            },
          ],
        confidence: options.chatResponse?.confidence ?? 0.91,
        prompt_id: "chat-v1",
        prompt_version: "1.0.0",
        mode_used: options.chatResponse?.mode_used ?? "chat",
        expert_criteria_used: options.chatResponse?.expert_criteria_used ?? false,
        web_search_used: options.chatResponse?.web_search_used ?? false,
      }));
      return;
    }

    if (logicalPath === "/user/learning-progress" && method === "GET") {
      await fulfillJson(route, envelope({
        total_practices: 0,
        competencies: [],
        frequent_resources: [],
        updated_at: FIXED_NOW,
        privacy: "local",
      }));
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

    if (logicalPath === "/api/auth/logout" && method === "POST") {
      await fulfillJson(route, envelope({ ok: true }));
      return;
    }

    throw new Error(`Unexpected API request: ${method} ${pathname}${url.search}`);
  });

  return { chatBodies };
}

async function openSocioChat(page: Page): Promise<void> {
  await page.goto("/socio-chat/demo");
  await expect(page.getByRole("group", { name: "Modo de mentoría" })).toBeVisible();
}

test.describe("Socio Chat E2E", () => {
  test("aplica el modo elegido al enviar la consulta", async ({ page }) => {
    const { chatBodies } = await prepareSocioChat(page);
    await openSocioChat(page);

    const textbox = page.getByRole("textbox");
    const submit = page.locator('form button[type="submit"]');

    await page.getByRole("button", { name: "Enséñame" }).click();
    await expect(page.getByRole("button", { name: "Enséñame" })).toHaveAttribute("aria-pressed", "true");
    await textbox.fill("revisa el corte de ingresos");
    await submit.click({ force: true });
    await expect.poll(() => chatBodies.length).toBe(1);
    expect(chatBodies[0]).toBe("Enséñame: revisa el corte de ingresos");

    await page.getByRole("button", { name: "Desafíame" }).click();
    await expect(page.getByRole("button", { name: "Desafíame" })).toHaveAttribute("aria-pressed", "true");
    await textbox.fill("cuestiona mi hipótesis");
    await submit.click({ force: true });
    await expect.poll(() => chatBodies.length).toBe(2);
    expect(chatBodies[1]).toBe("Desafía mi criterio: cuestiona mi hipótesis");

    await page.getByRole("button", { name: "Ayúdame" }).click();
    await expect(page.getByRole("button", { name: "Ayúdame" })).toHaveAttribute("aria-pressed", "true");
    await textbox.fill("ordena el siguiente paso");
    await submit.click({ force: true });
    await expect.poll(() => chatBodies.length).toBe(3);
    expect(chatBodies[2]).toBe("Ayúdame: ordena el siguiente paso");
  });

  test("no muestra la conversación hasta abrirla y el menú de perfil se abre y se cierra", async ({ page }) => {
    await prepareSocioChat(page);
    await openSocioChat(page);

    await expect(page.locator('[data-tour="sociochat-chat"]')).toHaveCount(0);

    const profileButton = page.getByRole("button", { name: "Abrir menú de usuario" });
    await profileButton.click();
    await expect(page.getByText("Perfil del auditor")).toBeVisible();
    await profileButton.click();
    await expect(page.getByText("Perfil del auditor")).toHaveCount(0);

    await page.getByRole("button", { name: /Cierre de mes/ }).click();
    await expect(page.locator('[data-tour="sociochat-chat"]')).toBeVisible();
    await expect(page.getByText("Histórico inicial")).toBeVisible();
  });

  test("renderiza markdown y fuentes confirmadas en la respuesta", async ({ page }) => {
    await prepareSocioChat(page, {
      chatResponse: {
        answer: "## Evaluación\n- **Importante**: revisar el corte\n- Ver [NIA 315](https://example.com/nia315)",
        citations: [
          {
            source: "docs/normativa/nia_315.md",
            excerpt: "Identificación y valoración del riesgo.",
            norma: "NIA 315",
            title: "NIA 315",
          },
          {
            source: "https://example.com/soporte",
            excerpt: "Referencia externa de apoyo.",
            norma: "Web",
            title: "Sitio web de respaldo",
          },
        ],
        confidence: 0.87,
      },
    });
    await openSocioChat(page);

    const textbox = page.getByRole("textbox");
    const submit = page.locator('form button[type="submit"]');

    await page.getByRole("button", { name: "Ayúdame" }).click();
    await textbox.fill("muéstrame evidencia de soporte");
    await submit.click();

    await expect(page.getByRole("heading", { name: "Evaluación" })).toBeVisible();
    await expect(page.getByText("Importante")).toBeVisible();
    await expect(page.getByText(/revisar el corte/i)).toBeVisible();
    await expect(page.getByText("Fuentes normativas")).toBeVisible();
    await expect(page.getByRole("link", { name: "NIA 315" })).toBeVisible();

    const webLink = page.locator('a[href="https://example.com/soporte"]');
    await expect(webLink).toBeVisible();
    await expect(webLink).toHaveAttribute("target", "_blank");
    await expect(page.getByText("Fuentes web")).toBeVisible();
  });

  test("muestra el error de API sin perder la conversación visible", async ({ page }) => {
    await prepareSocioChat(page, { failChat: true });
    await openSocioChat(page);

    await page.getByRole("button", { name: /Cierre de mes/ }).click();
    await expect(page.getByText("Histórico inicial")).toBeVisible();

    const textbox = page.getByRole("textbox");
    const submit = page.locator('form button[type="submit"]');
    await textbox.fill("provoca una falla");
    await submit.click({ force: true });

    await expect(page.getByText("Histórico inicial")).toBeVisible();
    await expect(page.getByText("Ayúdame: provoca una falla")).toBeVisible();
    await expect(page.getByText("Error interno del servidor")).toBeVisible();
    await expect(page.getByText("El servidor tuvo un problema interno. Inténtalo de nuevo en unos minutos.").first()).toBeVisible();
  });

  test("expone las acciones de conversación al enfocar y permite renombrar o eliminar", async ({ page }) => {
    await prepareSocioChat(page);
    await page.addInitScript(() => {
      window.prompt = () => "Cierre de mes actualizado";
      window.confirm = () => true;
    });
    await openSocioChat(page);

    const rowButton = page.getByRole("button", { name: "Cierre de mes" });
    const renameButton = page.getByRole("button", { name: "Renombrar conversación" });
    const deleteButton = page.getByRole("button", { name: "Eliminar conversación" });

    await expect(renameButton).toHaveCSS("opacity", "0");
    await rowButton.focus();
    await expect(renameButton).toHaveCSS("opacity", "1");
    await page.keyboard.press("Tab");
    await expect(renameButton).toBeFocused();
    await page.keyboard.press("Enter");
    const updatedRowButton = page.getByRole("button", { name: "Cierre de mes actualizado" });
    await expect(updatedRowButton).toBeVisible();

    await updatedRowButton.focus();
    await page.keyboard.press("Tab");
    await expect(renameButton).toBeFocused();
    await page.keyboard.press("Tab");
    await expect(deleteButton).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(page.getByText("Aún no hay conversaciones.")).toBeVisible();
  });

  test.describe("en pantallas táctiles", () => {
    test.use({ hasTouch: true, viewport: { width: 390, height: 844 } });

    test("muestra las acciones de conversación sin depender del hover", async ({ page }) => {
      await prepareSocioChat(page);
      await openSocioChat(page);

      const renameButton = page.getByRole("button", { name: "Renombrar conversación" });
      const deleteButton = page.getByRole("button", { name: "Eliminar conversación" });

      await expect(renameButton).toHaveCSS("opacity", "1");
      await expect(deleteButton).toHaveCSS("opacity", "1");
    });
  });
});
