import type { ApiEnvelope, ChatRequest, ChatResponse, MetodoRequest, MetodoResponse } from "./contracts";
import { getLsName, normalizeLsCode } from "./lsCatalog";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const DEMO_TOKEN_PREFIX = "demo_";
const DEMO_ONLY = process.env.NEXT_PUBLIC_DEMO_ONLY === "1";
const DEMO_CLIENTES_KEY = "socio_demo_clientes";

type UnknownRecord = Record<string, unknown>;

function nowIso(): string {
  return new Date().toISOString();
}

function envelope<T>(data: T): ApiEnvelope<T> {
  return {
    status: "ok",
    data,
    meta: { timestamp: nowIso() },
  };
}

function isDemoToken(token: string | null): boolean {
  return Boolean(token && token.startsWith(DEMO_TOKEN_PREFIX));
}

function parsePath(path: string): string[] {
  return path.split("?")[0].split("/").filter(Boolean);
}

function getDefaultDemoPerfil(clienteId: string): UnknownRecord {
  return {
    cliente: {
      nombre_legal: clienteId === "cliente_demo" ? "BF HOLDING S.A.S." : clienteId,
      sector: "Holding",
      pais: "Ecuador",
    },
    encargo: {
      firma_auditora: "Socio AI",
      encargado_asignado: "Joao Salas",
      anio_activo: 2025,
      marco_referencial: "NIIF para PYMES",
      norma_auditoria: "NIAs",
    },
    riesgo_global: {
      nivel: "MEDIO",
    },
    materialidad: {
      preliminar: {
        materialidad_global: 1200000,
        comentario_base: "Calculado automaticamente segun perfil del cliente.",
      },
    },
  };
}

function getDefaultDemoClientes(): UnknownRecord[] {
  return [
    { cliente_id: "cliente_demo", nombre: "BF HOLDING S.A.S.", sector: "Holding" },
    { cliente_id: "cliente_retail", nombre: "Retail Andino S.A.", sector: "Retail y Consumo" },
  ];
}

function getDemoClientes(): UnknownRecord[] {
  if (typeof window === "undefined") return getDefaultDemoClientes();
  const raw = localStorage.getItem(DEMO_CLIENTES_KEY);
  if (!raw) return getDefaultDemoClientes();
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return getDefaultDemoClientes();
    return parsed.filter((x) => typeof x === "object" && x !== null) as UnknownRecord[];
  } catch {
    return getDefaultDemoClientes();
  }
}

function setDemoClientes(clientes: UnknownRecord[]): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(DEMO_CLIENTES_KEY, JSON.stringify(clientes));
}

function getDemoPerfil(clienteId: string): UnknownRecord {
  if (typeof window === "undefined") return getDefaultDemoPerfil(clienteId);
  const key = `socio_demo_perfil_${clienteId}`;
  const raw = localStorage.getItem(key);
  if (!raw) return getDefaultDemoPerfil(clienteId);
  try {
    const parsed = JSON.parse(raw) as UnknownRecord;
    return parsed && typeof parsed === "object" ? parsed : getDefaultDemoPerfil(clienteId);
  } catch {
    return getDefaultDemoPerfil(clienteId);
  }
}

function setDemoPerfil(clienteId: string, perfil: UnknownRecord): void {
  if (typeof window === "undefined") return;
  const key = `socio_demo_perfil_${clienteId}`;
  localStorage.setItem(key, JSON.stringify(perfil));
}

function hashCode(text: string): number {
  let h = 0;
  for (let i = 0; i < text.length; i += 1) {
    h = (h << 5) - h + text.charCodeAt(i);
  }
  return Math.abs(h);
}

function buildDemoArea(areaCode: string): UnknownRecord {
  const code = normalizeLsCode(areaCode) || "130";
  const nombre = getLsName(code);
  const seed = hashCode(code);
  const base = 350000 + (seed % 12) * 95000;
  const saldoActual = Math.round(base * (2 + (seed % 5)));
  const saldoAnterior = Math.round(saldoActual * (0.78 + ((seed % 9) * 0.03)));
  const highRisk = code === "130" || code === "14" || seed % 4 === 0;

  return {
    encabezado: {
      area_code: code,
      nombre,
      responsable: "Joao Salas",
      estatus: highRisk ? "alto" : "medio",
      actual_year: "2025",
      anterior_year: "2024",
    },
    cuentas: [
      { codigo: code, nombre, saldo_actual: saldoActual, saldo_anterior: saldoAnterior, nivel: 1, checked: false },
      { codigo: `${code}.01`, nombre: "Subcuenta principal", saldo_actual: Math.round(saldoActual * 0.58), saldo_anterior: Math.round(saldoAnterior * 0.62), nivel: 2, checked: false },
      { codigo: `${code}.02`, nombre: "Subcuenta secundaria", saldo_actual: Math.round(saldoActual * 0.42), saldo_anterior: Math.round(saldoAnterior * 0.38), nivel: 2, checked: false },
    ],
    aseveraciones: [
      { nombre: "Valuacion", descripcion: `Validar medicion y estimaciones para el rubro ${nombre}.`, riesgo_tipico: highRisk ? "alto" : "medio", procedimiento_clave: "Recalculo y analitica de variaciones relevantes." },
      { nombre: "Existencia", descripcion: "Confirmar sustento documental y existencia economica de saldos.", riesgo_tipico: highRisk ? "alto" : "medio", procedimiento_clave: "Confirmaciones externas y pruebas de detalle." },
      { nombre: "Integridad", descripcion: "Verificar registro completo de notas credito y ajustes.", riesgo_tipico: "medio", procedimiento_clave: "Prueba de corte y secuencia documental." },
    ],
  };

  if (areaCode === "140") {
    return {
      encabezado: {
        area_code: "140",
        nombre: "Efectivo y equivalentes a efectivo",
        responsable: "Joao Salas",
        estatus: "medio",
        actual_year: "2025",
        anterior_year: "2024",
      },
      cuentas: [
        { codigo: "140", nombre: "Efectivo y equivalentes", saldo_actual: 950000, saldo_anterior: 870000, nivel: 1, checked: true },
        { codigo: "140.01", nombre: "Caja General", saldo_actual: 120000, saldo_anterior: 98000, nivel: 2, checked: false },
        { codigo: "140.02", nombre: "Bancos", saldo_actual: 830000, saldo_anterior: 772000, nivel: 2, checked: true },
      ],
      aseveraciones: [
        { nombre: "Existencia", descripcion: "Validar saldos con confirmaciones bancarias.", riesgo_tipico: "medio", procedimiento_clave: "Conciliaciones y confirmaciones." },
        { nombre: "Integridad", descripcion: "Revisar partidas en tránsito al cierre.", riesgo_tipico: "medio", procedimiento_clave: "Prueba de corte de movimientos." },
      ],
    };
  }

  return {
    encabezado: {
      area_code: "130",
      nombre: "Cuentas por cobrar corrientes",
      responsable: "Joao Salas",
      estatus: "alto",
      actual_year: "2025",
      anterior_year: "2024",
    },
    cuentas: [
      { codigo: "130", nombre: "Cuentas por cobrar corrientes", saldo_actual: 4200000, saldo_anterior: 3600000, nivel: 1, checked: false },
      { codigo: "130.1", nombre: "Clientes nacionales", saldo_actual: 2500000, saldo_anterior: 2050000, nivel: 2, checked: false },
      { codigo: "130.2", nombre: "Otras cuentas por cobrar", saldo_actual: 1700000, saldo_anterior: 1550000, nivel: 2, checked: false },
      { codigo: "130.2.01", nombre: "Partes relacionadas", saldo_actual: 780000, saldo_anterior: 600000, nivel: 3, checked: false },
    ],
    aseveraciones: [
      { nombre: "Valuacion", descripcion: "Riesgo de provision insuficiente en cartera vencida.", riesgo_tipico: "alto", procedimiento_clave: "Recalculo de deterioro bajo NIIF para PYMES." },
      { nombre: "Existencia", descripcion: "Necesidad de confirmaciones externas para saldos mayores.", riesgo_tipico: "alto", procedimiento_clave: "Circularizacion de terceros (NIA 505)." },
      { nombre: "Integridad", descripcion: "Verificar registro completo de notas credito y ajustes.", riesgo_tipico: "medio", procedimiento_clave: "Prueba de corte y secuencia documental." },
    ],
  };
}

function buildDemoRiskMatrix(): UnknownRecord {
  const rows = 5;
  const cols = 5;
  const quadrants: UnknownRecord[][] = [];
  for (let r = 0; r < rows; r += 1) {
    const row: UnknownRecord[] = [];
    for (let c = 0; c < cols; c += 1) {
      const frecuencia = rows - r;
      const impacto = c + 1;
      const score = Math.min(95, frecuencia * impacto * 4 + 15);
      const highCell = r === 0 && c >= 2;
      row.push({
        row: r + 1,
        col: c + 1,
        frecuencia,
        impacto,
        score,
        nivel: score >= 75 ? "ALTO" : score >= 50 ? "MEDIO" : "BAJO",
        area_id: highCell ? (c === 2 ? "130" : "140") : null,
        area_nombre: highCell ? (c === 2 ? "Cuentas por cobrar corrientes" : "Efectivo y equivalentes a efectivo") : null,
      });
    }
    quadrants.push(row);
  }

  return {
    cliente_id: "cliente_demo",
    eje_x: "Impacto",
    eje_y: "Frecuencia",
    quadrants,
    areas_criticas: [
      {
        area_id: "130",
        area_nombre: "Cuentas por cobrar corrientes",
        score: 0.86,
        nivel: "ALTO",
        frecuencia: 5,
        impacto: 4,
        hallazgos_abiertos: 3,
      },
      {
        area_id: "140",
        area_nombre: "Efectivo y equivalentes a efectivo",
        score: 0.71,
        nivel: "MEDIO",
        frecuencia: 4,
        impacto: 3,
        hallazgos_abiertos: 1,
      },
    ],
  };
}

function buildDemoDashboard(clienteId: string): UnknownRecord {
  return {
    cliente_id: clienteId,
    nombre_cliente: clienteId === "cliente_demo" ? "BF HOLDING S.A.S." : clienteId,
    periodo: "2025",
    sector: "Holding",
    riesgo_global: "MEDIO",
    materialidad_global: 1200000,
    balance: {
      activo: 14500000,
      pasivo: 8300000,
      patrimonio: 6200000,
      ingresos: 18200000,
      gastos: 11900000,
    },
    progreso: {
      pct_completado: 58,
      areas_completas: 7,
      areas_en_proceso: 4,
      areas_no_iniciadas: 3,
      total_areas: 14,
    },
    top_areas: [
      { codigo: "130", nombre: "Cuentas por cobrar corrientes", score_riesgo: 0.86, prioridad: "alta", saldo_total: 4200000, con_saldo: true },
      { codigo: "140", nombre: "Efectivo y equivalentes a efectivo", score_riesgo: 0.71, prioridad: "media", saldo_total: 950000, con_saldo: true },
      { codigo: "14", nombre: "Inversiones no corrientes", score_riesgo: 0.68, prioridad: "media", saldo_total: 3800000, con_saldo: true },
    ],
  };
}

function mockApi<T>(path: string, init?: RequestInit): T {
  const parts = parsePath(path);
  const method = (init?.method || "GET").toUpperCase();

  if (parts[0] === "clientes") {
    if (method === "POST") {
      const bodyRaw = typeof init?.body === "string" ? init.body : "{}";
      let bodyObj: UnknownRecord = {};
      try {
        bodyObj = JSON.parse(bodyRaw) as UnknownRecord;
      } catch {
        bodyObj = {};
      }

      const cliente_id = typeof bodyObj.cliente_id === "string" ? bodyObj.cliente_id.trim() : "";
      const nombre = typeof bodyObj.nombre === "string" ? bodyObj.nombre.trim() : "";
      const sector = typeof bodyObj.sector === "string" ? bodyObj.sector.trim() : null;
      if (!cliente_id || !nombre) {
        throw new Error("Datos incompletos para crear cliente.");
      }

      const clientes = getDemoClientes();
      const exists = clientes.some((c) => String(c.cliente_id ?? "") === cliente_id);
      if (exists) {
        throw new Error("Ya existe un cliente con ese identificador.");
      }

      const next = [...clientes, { cliente_id, nombre, sector }];
      setDemoClientes(next);
      return envelope({ cliente_id, nombre, sector }) as T;
    }

    return envelope(getDemoClientes()) as T;
  }

  if (parts[0] === "dashboard" && parts[1]) {
    return envelope(buildDemoDashboard(parts[1])) as T;
  }

  if (parts[0] === "risk-engine" && parts[1]) {
    return envelope(buildDemoRiskMatrix()) as T;
  }

  if (parts[0] === "areas" && parts[1] && parts[2]) {
    if (method === "PATCH") {
      return envelope({ ok: true }) as T;
    }
    return envelope(buildDemoArea(parts[2])) as T;
  }

  if (parts[0] === "perfil" && parts[1]) {
    const clienteId = parts[1];
    if (method === "PUT") {
      const bodyRaw = typeof init?.body === "string" ? init.body : "{}";
      let bodyObj: UnknownRecord = {};
      try {
        bodyObj = JSON.parse(bodyRaw) as UnknownRecord;
      } catch {
        bodyObj = {};
      }
      setDemoPerfil(clienteId, bodyObj);
      return envelope({ cliente_id: clienteId, perfil: bodyObj }) as T;
    }
    const perfil = getDemoPerfil(clienteId);
    return envelope({ cliente_id: clienteId, perfil }) as T;
  }

  if (parts[0] === "chat" && parts[1]) {
    return envelope({
      cliente_id: parts[1],
      answer: "Modo demo activo. Esta respuesta es simulada hasta conectar backend productivo.",
      context_sources: ["demo://chat"],
    }) as T;
  }

  if (parts[0] === "metodologia" && parts[1]) {
    return envelope({
      cliente_id: parts[1],
      area: "130",
      explanation: "Modo demo activo. Explicacion metodologica simulada.",
      context_sources: ["demo://metodologia"],
    }) as T;
  }

  return envelope({}) as T;
}

export class TokenExpiredError extends Error {
  constructor(message: string = "JWT token expired or invalid") {
    super(message);
    this.name = "TokenExpiredError";
  }
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("socio_token");
}

function requireToken(): string {
  const token = getToken();
  if (!token) {
    throw new Error("Missing JWT token in session");
  }
  return token;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  if (DEMO_ONLY || isDemoToken(token)) {
    return mockApi<T>(path, init);
  }

  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers,
    });
  } catch (error) {
    if (isDemoToken(token)) {
      return mockApi<T>(path, init);
    }
    throw error;
  }

  if (res.status === 401) {
    throw new TokenExpiredError("Token expired. Please login again.");
  }

  if (!res.ok) {
    throw new Error(`API error ${res.status}`);
  }

  return (await res.json()) as T;
}

export async function authFetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  requireToken();
  return apiFetch<T>(path, init);
}

export async function postChat(clienteId: string, payload: ChatRequest): Promise<ApiEnvelope<ChatResponse>> {
  requireToken();
  return apiFetch<ApiEnvelope<ChatResponse>>(`/chat/${clienteId}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function postMetodologia(
  clienteId: string,
  payload: MetodoRequest,
): Promise<ApiEnvelope<MetodoResponse>> {
  requireToken();
  return apiFetch<ApiEnvelope<MetodoResponse>>(`/metodologia/${clienteId}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
