"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { useUserPreferences } from "../../components/providers/UserPreferencesProvider";
import {
  createAdminUser,
  getAdminUsers,
  patchAdminUser,
  replaceAdminUserClientes,
  type AdminUser,
} from "../../lib/api/admin";
import { getClientes, type ClienteOption } from "../../lib/api/clientes";

const ROLE_OPTIONS = ["admin", "socio", "manager", "senior", "semi", "junior", "auditor"] as const;

function canManageUsers(role: string): boolean {
  const normalized = String(role || "").trim().toLowerCase();
  return normalized === "admin" || normalized === "socio";
}

export default function AdminUsersPage() {
  const router = useRouter();
  const { session, loading: sessionLoading } = useUserPreferences();

  const [users, setUsers] = useState<AdminUser[]>([]);
  const [clientes, setClientes] = useState<ClienteOption[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [okMessage, setOkMessage] = useState<string>("");
  const [selectedUserId, setSelectedUserId] = useState<string>("");
  const [selectedClienteIds, setSelectedClienteIds] = useState<string[]>([]);

  const [newUsername, setNewUsername] = useState<string>("");
  const [newDisplayName, setNewDisplayName] = useState<string>("");
  const [newPassword, setNewPassword] = useState<string>("");
  const [newRole, setNewRole] = useState<string>("auditor");
  const [newActive, setNewActive] = useState<boolean>(true);
  const [newClienteIds, setNewClienteIds] = useState<string[]>([]);

  const [editDisplayName, setEditDisplayName] = useState<string>("");
  const [editRole, setEditRole] = useState<string>("auditor");
  const [editActive, setEditActive] = useState<boolean>(true);
  const [editPassword, setEditPassword] = useState<string>("");

  const selectedUser = useMemo(
    () => users.find((user) => user.user_id === selectedUserId) ?? null,
    [users, selectedUserId],
  );

  const isAuthorized = canManageUsers(session?.role || "");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const token = window.localStorage.getItem("socio_token");
    if (!token) {
      router.replace("/");
      return;
    }
  }, [router]);

  useEffect(() => {
    if (sessionLoading) return;
    if (!isAuthorized) {
      setLoading(false);
      return;
    }

    let active = true;
    async function loadData(): Promise<void> {
      setLoading(true);
      setError("");
      try {
        const [usersData, clientesData] = await Promise.all([getAdminUsers(), getClientes()]);
        if (!active) return;
        setUsers(usersData);
        setClientes(clientesData);
        if (usersData.length > 0) {
          const first = usersData[0];
          setSelectedUserId(first.user_id);
          setSelectedClienteIds(first.cliente_ids);
          setEditDisplayName(first.display_name || "");
          setEditRole(first.role || "auditor");
          setEditActive(Boolean(first.active));
        }
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "No se pudo cargar la administracion de usuarios.");
      } finally {
        if (active) setLoading(false);
      }
    }
    void loadData();
    return () => {
      active = false;
    };
  }, [isAuthorized, sessionLoading]);

  useEffect(() => {
    if (!selectedUser) return;
    setSelectedClienteIds(selectedUser.cliente_ids);
    setEditDisplayName(selectedUser.display_name || "");
    setEditRole(selectedUser.role || "auditor");
    setEditActive(Boolean(selectedUser.active));
    setEditPassword("");
  }, [selectedUser]);

  function toggleInList(current: string[], value: string): string[] {
    if (current.includes(value)) return current.filter((item) => item !== value);
    return [...current, value];
  }

  function updateUserInState(nextUser: AdminUser): void {
    setUsers((prev) => prev.map((row) => (row.user_id === nextUser.user_id ? nextUser : row)));
  }

  async function handleCreateUser(event: React.FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!newUsername.trim() || !newPassword.trim()) {
      setError("Usuario y contrasena son obligatorios.");
      return;
    }
    setSaving(true);
    setError("");
    setOkMessage("");
    try {
      const created = await createAdminUser({
        username: newUsername.trim(),
        password: newPassword,
        role: newRole,
        display_name: newDisplayName.trim(),
        active: newActive,
        cliente_ids: newClienteIds,
      });
      setUsers((prev) => [created, ...prev.filter((item) => item.user_id !== created.user_id)]);
      setSelectedUserId(created.user_id);
      setNewUsername("");
      setNewDisplayName("");
      setNewPassword("");
      setNewRole("auditor");
      setNewActive(true);
      setNewClienteIds([]);
      setOkMessage("Usuario creado correctamente.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear el usuario.");
    } finally {
      setSaving(false);
    }
  }

  async function handleSaveUserPatch(): Promise<void> {
    if (!selectedUser) return;
    setSaving(true);
    setError("");
    setOkMessage("");
    try {
      const patchPayload: Record<string, unknown> = {};
      if (editDisplayName.trim() !== selectedUser.display_name) patchPayload.display_name = editDisplayName.trim();
      if (editRole !== selectedUser.role) patchPayload.role = editRole;
      if (editActive !== selectedUser.active) patchPayload.active = editActive;
      if (editPassword.trim()) patchPayload.password = editPassword;
      const updated = await patchAdminUser(selectedUser.user_id, patchPayload);
      updateUserInState(updated);
      setOkMessage("Usuario actualizado.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo actualizar el usuario.");
    } finally {
      setSaving(false);
    }
  }

  async function handleSaveAssignments(): Promise<void> {
    if (!selectedUser) return;
    setSaving(true);
    setError("");
    setOkMessage("");
    try {
      const assigned = await replaceAdminUserClientes(selectedUser.user_id, selectedClienteIds);
      updateUserInState({ ...selectedUser, cliente_ids: assigned });
      setOkMessage("Asignaciones guardadas.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudieron guardar las asignaciones.");
    } finally {
      setSaving(false);
    }
  }

  if (sessionLoading || loading) {
    return (
      <div className="min-h-screen bg-[#f7fafc] p-8">
        <div className="sovereign-card h-32 animate-pulse bg-[#edf2f7]" />
      </div>
    );
  }

  if (!isAuthorized) {
    return (
      <div className="min-h-screen bg-[#f7fafc] p-8">
        <div className="max-w-3xl mx-auto sovereign-card">
          <h1 className="font-headline text-4xl text-[#041627]">Acceso restringido</h1>
          <p className="text-slate-600 mt-3">
            Solo perfiles <b>admin</b> o <b>socio</b> pueden administrar usuarios y asignaciones.
          </p>
          <button
            type="button"
            onClick={() => router.push("/clientes")}
            className="mt-6 px-4 py-2 rounded-xl bg-[#041627] text-white text-sm font-semibold"
          >
            Volver a Clientes
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f7fafc] px-6 md:px-10 py-8">
      <header className="max-w-[1600px] mx-auto mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Administracion</p>
          <h1 className="font-headline text-5xl text-[#041627] mt-1">Usuarios y Asignaciones</h1>
          <p className="text-sm text-slate-600 mt-2">
            Gestiona acceso multiusuario por cliente asignado y roles globales.
          </p>
        </div>
        <button
          type="button"
          onClick={() => router.push("/clientes")}
          className="px-4 py-2 rounded-xl border border-[#041627]/20 bg-white text-[#041627] text-sm font-semibold"
        >
          Volver a Clientes
        </button>
      </header>

      <main className="max-w-[1600px] mx-auto grid grid-cols-1 xl:grid-cols-12 gap-6">
        <section className="xl:col-span-4 sovereign-card">
          <h2 className="font-headline text-3xl text-[#041627] mb-4">Crear Usuario</h2>
          <form className="space-y-3" onSubmit={handleCreateUser}>
            <input
              className="ghost-input"
              value={newUsername}
              onChange={(event) => setNewUsername(event.target.value)}
              placeholder="username (correo)"
            />
            <input
              className="ghost-input"
              value={newDisplayName}
              onChange={(event) => setNewDisplayName(event.target.value)}
              placeholder="Nombre visible"
            />
            <input
              className="ghost-input"
              type="password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
              placeholder="Contrasena inicial"
            />
            <div className="grid grid-cols-2 gap-3">
              <select className="ghost-input" value={newRole} onChange={(event) => setNewRole(event.target.value)}>
                {ROLE_OPTIONS.map((role) => (
                  <option key={role} value={role}>
                    {role}
                  </option>
                ))}
              </select>
              <label className="ghost-input flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={newActive}
                  onChange={(event) => setNewActive(event.target.checked)}
                />
                <span className="text-sm text-slate-700">Activo</span>
              </label>
            </div>
            <div className="rounded-xl border border-[#041627]/10 bg-[#f8fafc] p-3">
              <p className="text-xs uppercase tracking-[0.12em] text-slate-500 font-semibold mb-2">
                Clientes asignados al crear
              </p>
              <div className="max-h-40 overflow-auto space-y-1">
                {clientes.map((cliente) => (
                  <label key={cliente.cliente_id} className="flex items-center gap-2 text-sm text-slate-700">
                    <input
                      type="checkbox"
                      checked={newClienteIds.includes(cliente.cliente_id)}
                      onChange={() =>
                        setNewClienteIds((prev) => toggleInList(prev, cliente.cliente_id))
                      }
                    />
                    <span>{cliente.nombre}</span>
                  </label>
                ))}
              </div>
            </div>
            <button
              type="submit"
              disabled={saving}
              className="w-full py-2.5 rounded-xl bg-[#041627] text-white text-sm font-semibold disabled:opacity-60"
            >
              {saving ? "Guardando..." : "Crear Usuario"}
            </button>
          </form>
        </section>

        <section className="xl:col-span-8 space-y-6">
          <article className="sovereign-card">
            <h2 className="font-headline text-3xl text-[#041627] mb-4">Usuarios existentes</h2>
            {users.length === 0 ? (
              <p className="text-sm text-slate-500">No hay usuarios registrados.</p>
            ) : (
              <div className="space-y-2">
                {users.map((user) => (
                  <button
                    key={user.user_id}
                    type="button"
                    onClick={() => setSelectedUserId(user.user_id)}
                    className={`w-full text-left rounded-xl border px-3 py-3 ${
                      selectedUserId === user.user_id
                        ? "bg-[#041627] text-white border-[#041627]"
                        : "bg-white text-slate-700 border-slate-200"
                    }`}
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p className="text-sm font-semibold">{user.display_name || user.username}</p>
                        <p className={`text-xs ${selectedUserId === user.user_id ? "text-slate-200" : "text-slate-500"}`}>
                          @{user.username}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 text-xs">
                        <span className="px-2 py-1 rounded-full border border-white/30">{user.role}</span>
                        <span className="px-2 py-1 rounded-full border border-white/30">
                          {user.active ? "activo" : "inactivo"}
                        </span>
                        <span className="px-2 py-1 rounded-full border border-white/30">
                          {user.cliente_ids.length} clientes
                        </span>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </article>

          {selectedUser ? (
            <article className="sovereign-card">
              <h3 className="font-headline text-2xl text-[#041627] mb-4">Editar usuario seleccionado</h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <label className="space-y-2">
                  <span className="text-xs uppercase tracking-[0.12em] text-slate-500 font-semibold">Nombre visible</span>
                  <input
                    className="ghost-input"
                    value={editDisplayName}
                    onChange={(event) => setEditDisplayName(event.target.value)}
                  />
                </label>
                <label className="space-y-2">
                  <span className="text-xs uppercase tracking-[0.12em] text-slate-500 font-semibold">Rol</span>
                  <select className="ghost-input" value={editRole} onChange={(event) => setEditRole(event.target.value)}>
                    {ROLE_OPTIONS.map((role) => (
                      <option key={role} value={role}>
                        {role}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="space-y-2">
                  <span className="text-xs uppercase tracking-[0.12em] text-slate-500 font-semibold">Nueva contrasena (opcional)</span>
                  <input
                    className="ghost-input"
                    type="password"
                    value={editPassword}
                    onChange={(event) => setEditPassword(event.target.value)}
                    placeholder="Dejar vacio para no cambiar"
                  />
                </label>
                <label className="space-y-2">
                  <span className="text-xs uppercase tracking-[0.12em] text-slate-500 font-semibold">Estado</span>
                  <label className="ghost-input flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={editActive}
                      onChange={(event) => setEditActive(event.target.checked)}
                    />
                    <span className="text-sm text-slate-700">{editActive ? "Activo" : "Inactivo"}</span>
                  </label>
                </label>
              </div>

              <div className="mt-4 flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleSaveUserPatch}
                  disabled={saving}
                  className="px-4 py-2 rounded-xl bg-[#041627] text-white text-sm font-semibold disabled:opacity-60"
                >
                  Guardar Perfil Usuario
                </button>
              </div>

              <div className="mt-6 rounded-xl border border-[#041627]/10 bg-[#f8fafc] p-4">
                <p className="text-xs uppercase tracking-[0.12em] text-slate-500 font-semibold mb-3">
                  Clientes asignados
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-64 overflow-auto">
                  {clientes.map((cliente) => (
                    <label key={cliente.cliente_id} className="flex items-center gap-2 text-sm text-slate-700">
                      <input
                        type="checkbox"
                        checked={selectedClienteIds.includes(cliente.cliente_id)}
                        onChange={() =>
                          setSelectedClienteIds((prev) => toggleInList(prev, cliente.cliente_id))
                        }
                      />
                      <span>{cliente.nombre}</span>
                    </label>
                  ))}
                </div>
                <button
                  type="button"
                  onClick={handleSaveAssignments}
                  disabled={saving}
                  className="mt-4 px-4 py-2 rounded-xl border border-[#041627]/20 text-[#041627] text-sm font-semibold bg-white disabled:opacity-60"
                >
                  Guardar Asignaciones
                </button>
              </div>
            </article>
          ) : null}
        </section>
      </main>

      {error ? <div className="max-w-[1600px] mx-auto mt-6 text-sm text-[#93000a]">{error}</div> : null}
      {okMessage ? <div className="max-w-[1600px] mx-auto mt-2 text-sm text-emerald-700">{okMessage}</div> : null}
    </div>
  );
}
