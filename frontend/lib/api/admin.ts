import { authFetchJson } from "../api";
import type { ApiEnvelope } from "../contracts";

export type AdminUser = {
  user_id: string;
  username: string;
  display_name: string;
  role: string;
  active: boolean;
  cliente_ids: string[];
  created_at: string;
  updated_at: string;
};

export type AdminUserCreateInput = {
  username: string;
  password: string;
  role: string;
  display_name?: string;
  active?: boolean;
  cliente_ids?: string[];
};

export type AdminUserPatchInput = Partial<{
  display_name: string;
  role: string;
  active: boolean;
  password: string;
}>;

type AdminUsersPayload = {
  users?: unknown;
};

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  const out: string[] = [];
  for (const entry of value) {
    const clean = String(entry || "").trim();
    if (!clean) continue;
    out.push(clean);
  }
  return Array.from(new Set(out));
}

function asAdminUser(value: unknown): AdminUser | null {
  if (!value || typeof value !== "object") return null;
  const row = value as Record<string, unknown>;
  const user_id = String(row.user_id || "").trim();
  const username = String(row.username || "").trim();
  if (!user_id || !username) return null;
  return {
    user_id,
    username,
    display_name: String(row.display_name || username).trim(),
    role: String(row.role || "auditor").trim().toLowerCase(),
    active: Boolean(row.active),
    cliente_ids: asStringArray(row.cliente_ids),
    created_at: String(row.created_at || ""),
    updated_at: String(row.updated_at || ""),
  };
}

export async function getAdminUsers(): Promise<AdminUser[]> {
  const response = await authFetchJson<ApiEnvelope<AdminUsersPayload>>("/api/admin/users");
  const raw = response?.data?.users;
  if (!Array.isArray(raw)) return [];
  return raw.map(asAdminUser).filter((item): item is AdminUser => item !== null);
}

export async function createAdminUser(input: AdminUserCreateInput): Promise<AdminUser> {
  const response = await authFetchJson<ApiEnvelope<{ user?: unknown }>>("/api/admin/users", {
    method: "POST",
    body: JSON.stringify({
      username: input.username.trim(),
      password: input.password,
      role: input.role,
      display_name: input.display_name?.trim() || "",
      active: input.active ?? true,
      cliente_ids: input.cliente_ids ?? [],
    }),
  });
  const user = asAdminUser(response?.data?.user);
  if (!user) {
    throw new Error("No se pudo crear el usuario.");
  }
  return user;
}

export async function patchAdminUser(userId: string, patch: AdminUserPatchInput): Promise<AdminUser> {
  const response = await authFetchJson<ApiEnvelope<{ user?: unknown }>>(`/api/admin/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
  const user = asAdminUser(response?.data?.user);
  if (!user) {
    throw new Error("No se pudo actualizar el usuario.");
  }
  return user;
}

export async function replaceAdminUserClientes(userId: string, clienteIds: string[]): Promise<string[]> {
  const response = await authFetchJson<ApiEnvelope<{ cliente_ids?: unknown }>>(
    `/api/admin/users/${userId}/clientes`,
    {
      method: "PUT",
      body: JSON.stringify({ cliente_ids: clienteIds }),
    },
  );
  return asStringArray(response?.data?.cliente_ids);
}

