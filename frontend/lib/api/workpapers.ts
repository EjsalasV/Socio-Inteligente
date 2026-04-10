import { authFetchJson, TokenExpiredError } from "../api";
import type { ApiEnvelope } from "../contracts";
import type { WorkpaperPlanData } from "../../types/workpapers";

type UnknownRecord = Record<string, unknown>;

function asString(value: unknown, fallback: string = ""): string {
  return typeof value === "string" ? value : fallback;
}

function asBoolean(value: unknown, fallback: boolean = false): boolean {
  return typeof value === "boolean" ? value : fallback;
}

function asNumber(value: unknown, fallback: number = 0): number {
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function normalizePlan(clienteId: string, raw: UnknownRecord): WorkpaperPlanData {
  const tasksRaw = Array.isArray(raw.tasks) ? raw.tasks : [];
  const gatesRaw = Array.isArray(raw.gates) ? raw.gates : [];
  const coverageRaw = typeof raw.coverage_summary === "object" && raw.coverage_summary !== null
    ? (raw.coverage_summary as UnknownRecord)
    : {};

  return {
    cliente_id: asString(raw.cliente_id, clienteId),
    completion_pct: asNumber(raw.completion_pct, 0),
    tasks_page: asNumber(raw.tasks_page, 1),
    tasks_page_size: asNumber(raw.tasks_page_size, 0),
    tasks_total: asNumber(raw.tasks_total, tasksRaw.length),
    tasks_total_all: asNumber(raw.tasks_total_all, tasksRaw.length),
    tasks_has_more: asBoolean(raw.tasks_has_more, false),
    tasks: tasksRaw
      .map((item) => {
        const row = typeof item === "object" && item !== null ? (item as UnknownRecord) : null;
        if (!row) return null;
        const id = asString(row.id);
        if (!id) return null;
        return {
          id,
          area_code: asString(row.area_code),
          area_name: asString(row.area_name),
          title: asString(row.title),
          nia_ref: asString(row.nia_ref),
          prioridad: asString(row.prioridad, "media"),
          required: asBoolean(row.required, true),
          done: asBoolean(row.done, false),
          evidence_note: asString(row.evidence_note),
        };
      })
      .filter((x): x is WorkpaperPlanData["tasks"][number] => x !== null),
    gates: gatesRaw
      .map((item) => {
        const row = typeof item === "object" && item !== null ? (item as UnknownRecord) : null;
        if (!row) return null;
        const code = asString(row.code);
        if (!code) return null;
        return {
          code,
          title: asString(row.title),
          status: asString(row.status, "blocked") as "ok" | "blocked",
          detail: asString(row.detail),
        };
      })
      .filter((x): x is WorkpaperPlanData["gates"][number] => x !== null),
    coverage_summary: {
      total_assertions: asNumber(coverageRaw.total_assertions, 0),
      covered_assertions: asNumber(coverageRaw.covered_assertions, 0),
      coverage_pct: asNumber(coverageRaw.coverage_pct, 0),
      missing_by_area: typeof coverageRaw.missing_by_area === "object" && coverageRaw.missing_by_area !== null
        ? (coverageRaw.missing_by_area as Record<string, string[]>)
        : {},
    },
  };
}

type WorkpaperPlanQueryOptions = {
  page?: number;
  pageSize?: number;
  areaCode?: string;
  query?: string;
};

function buildWorkpaperPlanPath(clienteId: string, options?: WorkpaperPlanQueryOptions): string {
  const params = new URLSearchParams();
  if (options?.page && options.page > 0) {
    params.set("page", String(options.page));
  }
  if (options?.pageSize !== undefined && options.pageSize >= 0) {
    params.set("page_size", String(options.pageSize));
  }
  if (options?.areaCode && options.areaCode.trim()) {
    params.set("area_code", options.areaCode.trim());
  }
  if (options?.query && options.query.trim()) {
    params.set("q", options.query.trim());
  }
  const queryString = params.toString();
  return queryString ? `/papeles-trabajo/${clienteId}?${queryString}` : `/papeles-trabajo/${clienteId}`;
}

export async function getWorkpaperPlan(
  clienteId: string,
  options?: WorkpaperPlanQueryOptions,
): Promise<WorkpaperPlanData> {
  try {
    const response = await authFetchJson<ApiEnvelope<unknown>>(buildWorkpaperPlanPath(clienteId, options));
    const raw = typeof response?.data === "object" && response?.data !== null ? (response.data as UnknownRecord) : {};
    return normalizePlan(clienteId, raw);
  } catch (error) {
    if (error instanceof TokenExpiredError) {
      throw new TokenExpiredError("La sesión expiró. Vuelve a iniciar sesión.");
    }
    throw error;
  }
}

export async function patchWorkpaperTask(
  clienteId: string,
  taskId: string,
  payload: { done: boolean; evidence_note?: string },
): Promise<void> {
  await authFetchJson<ApiEnvelope<unknown>>(`/papeles-trabajo/${clienteId}/tasks/${encodeURIComponent(taskId)}`, {
    method: "PATCH",
    body: JSON.stringify({
      done: payload.done,
      evidence_note: payload.evidence_note ?? "",
    }),
  });
}

export async function createWorkpaperTask(
  clienteId: string,
  payload: {
    area_code: string;
    area_name: string;
    title: string;
    nia_ref?: string;
    prioridad?: string;
    required?: boolean;
    evidence_note?: string;
  },
): Promise<{ created: boolean; task: WorkpaperPlanData["tasks"][number] | null }> {
  const response = await authFetchJson<ApiEnvelope<unknown>>(`/papeles-trabajo/${clienteId}/tasks`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  const raw = typeof response?.data === "object" && response?.data !== null ? (response.data as UnknownRecord) : {};
  const taskRaw = typeof raw.task === "object" && raw.task !== null ? (raw.task as UnknownRecord) : null;
  if (!taskRaw) return { created: Boolean(raw.created), task: null };
  return {
    created: Boolean(raw.created),
    task: {
      id: asString(taskRaw.id),
      area_code: asString(taskRaw.area_code),
      area_name: asString(taskRaw.area_name),
      title: asString(taskRaw.title),
      nia_ref: asString(taskRaw.nia_ref),
      prioridad: asString(taskRaw.prioridad),
      required: asBoolean(taskRaw.required, true),
      done: asBoolean(taskRaw.done, false),
      evidence_note: asString(taskRaw.evidence_note),
    },
  };
}

export async function deleteWorkpaperTask(clienteId: string, taskId: string): Promise<void> {
  await authFetchJson<ApiEnvelope<unknown>>(
    `/papeles-trabajo/${clienteId}/tasks/${encodeURIComponent(taskId)}`,
    {
      method: "DELETE",
    },
  );
}
