"use client";

import { FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { setSessionState } from "../lib/auth-session";
import { getClientes } from "../lib/api/clientes";
import { buildApiUrl, getApiBase, getBrowserOrigin } from "../lib/api-base";

type LoginApiData = {
  access_token?: string;
  token_type?: string;
  expires_in?: number;
  csrf_token?: string;
};

type LoginApiResponse = {
  status?: "ok" | "error";
  data?: LoginApiData;
  detail?: string;
  message?: string;
};

function extractErrorMessage(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== "object") return fallback;
  const value = payload as Record<string, unknown>;
  if (typeof value.detail === "string" && value.detail.trim()) return value.detail;
  if (typeof value.message === "string" && value.message.trim()) return value.message;
  return fallback;
}

function extractToken(payload: unknown): string {
  if (!payload || typeof payload !== "object") return "";
  const value = payload as LoginApiResponse;
  const token = value?.data?.access_token;
  return typeof token === "string" && token.trim() ? token : "";
}

function extractCsrfToken(payload: unknown): string {
  if (!payload || typeof payload !== "object") return "";
  const value = payload as LoginApiResponse;
  const token = (value?.data as { csrf_token?: string } | undefined)?.csrf_token;
  return typeof token === "string" && token.trim() ? token : "";
}

export default function LoginPage() {
  const router = useRouter();

  const [username, setUsername] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  const isDisabled = useMemo(
    () => isLoading || !username.trim() || !password.trim(),
    [isLoading, username, password],
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const res = await fetch(buildApiUrl("/auth/login"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ username: username.trim(), password }),
      });

      let payload: unknown = null;
      try {
        payload = (await res.json()) as unknown;
      } catch {
        payload = null;
      }

      if (!res.ok) {
        setError(extractErrorMessage(payload, "No se pudo iniciar sesión."));
        return;
      }

      const token = extractToken(payload);
      if (!token) {
        setError("La respuesta de autenticación no incluyó token.");
        return;
      }
      const csrfToken = extractCsrfToken(payload);
      if (!csrfToken) {
        setError("La respuesta de autenticación no incluyó token CSRF.");
        return;
      }

      // Store token in sessionStorage so WebSocket can retrieve it (it's in httpOnly cookie but inaccessible to JS)
      if (typeof window !== "undefined" && window.sessionStorage) {
        window.sessionStorage.setItem("socio_auth_token", token);
      }

      setSessionState(csrfToken);

      try {
        await getClientes();
        router.push("/clientes");
      } catch {
        router.push("/clientes");
      }
    } catch {
      setError(
        `No se pudo conectar con el backend de autenticación (${getApiBase()}). Origin actual: ${getBrowserOrigin()}.`,
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-white text-slate-900 font-body">
      <main className="min-h-screen grid grid-cols-1 md:grid-cols-2">
        <section className="hidden md:flex bg-gradient-to-br from-[#041627] to-[#0d2a3f] text-white p-12 lg:p-16 flex-col justify-between">
          <div className="space-y-8">
            <div>
              <h1 className="font-headline text-6xl leading-none">Socio AI</h1>
              <p className="mt-4 text-lg text-slate-100 max-w-lg">
                El criterio auditor, asistido por inteligencia artificial
              </p>
            </div>

            <div className="space-y-5">
              <div className="flex items-start gap-3">
                <span className="material-symbols-outlined text-[#89d3d4]">psychology</span>
                <p className="text-sm text-slate-100">Criterio NIA y NIIF en cada área del encargo</p>
              </div>
              <div className="flex items-start gap-3">
                <span className="material-symbols-outlined text-[#89d3d4]">school</span>
                <p className="text-sm text-slate-100">Aprende auditoría en cada paso según tu rol</p>
              </div>
              <div className="flex items-start gap-3">
                <span className="material-symbols-outlined text-[#89d3d4]">route</span>
                <p className="text-sm text-slate-100">Del Trial Balance al informe en un flujo guiado</p>
              </div>
            </div>
          </div>

          <p className="text-xs uppercase tracking-[0.16em] text-[#a5eff0]">Para firmas de auditoría externa</p>
        </section>

        <section className="flex items-center justify-center p-6 md:p-12">
          <div className="w-full max-w-lg">
            <div className="mb-8">
              <p className="text-xs uppercase tracking-[0.16em] text-slate-500 font-semibold mb-2">Iniciar sesión</p>
              <h2 className="font-headline text-4xl text-[#041627] leading-tight">Bienvenido de nuevo</h2>
              <p className="text-slate-600 mt-2">Su entorno de auditoría está listo.</p>
            </div>

            <div className="rounded-xl p-8 md:p-10 shadow-[0_20px_40px_rgba(24,28,30,0.06)] bg-white border border-white/60">
              <form className="space-y-8" onSubmit={handleSubmit}>
                <div className="space-y-2">
                  <label className="text-[11px] uppercase tracking-widest font-semibold text-slate-500 block ml-1" htmlFor="username">
                    Correo electrónico profesional
                  </label>
                  <input
                    id="username"
                    name="username"
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="joaosalas123@gmail.com"
                    className="w-full bg-[#f1f4f6] border border-[rgba(196,198,205,0.35)] rounded-xl px-4 py-4 focus:ring-0 focus:border-[#89d3d4] transition-all outline-none text-slate-900 placeholder:text-slate-400"
                    autoComplete="username"
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between items-end">
                    <label className="text-[11px] uppercase tracking-widest font-semibold text-slate-500 block ml-1" htmlFor="password">
                      Contraseña
                    </label>
                    <button
                      type="button"
                      className="text-[11px] uppercase tracking-widest font-semibold text-[#002f30] hover:text-[#001919] transition-colors"
                      onClick={() => setShowPassword((v) => !v)}
                    >
                      {showPassword ? "Ocultar" : "Mostrar"}
                    </button>
                  </div>
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="1234"
                    className="w-full bg-[#f1f4f6] border border-[rgba(196,198,205,0.35)] rounded-xl px-4 py-4 focus:ring-0 focus:border-[#89d3d4] transition-all outline-none text-slate-900 placeholder:text-slate-400"
                    autoComplete="current-password"
                  />
                </div>

                <div className="flex items-start gap-3 p-4 bg-[#002f30]/5 rounded-xl border border-[#89d3d4]/25">
                  <span className="material-symbols-outlined text-[#529c9d] text-xl">verified_user</span>
                  <p className="text-[13px] text-[#004f50] font-medium">
                    Autenticación de dos factores (2FA) requerida para este entorno.
                  </p>
                </div>

                <div className="flex items-start gap-3 p-4 bg-[#f1f4f6] rounded-xl border border-[#c4c6cd]/35">
                  <span className="material-symbols-outlined text-[#041627] text-xl">info</span>
                  <p className="text-[13px] text-slate-600 font-medium">
                    Usa tus credenciales autorizadas para este cliente. Si no tienes acceso, solicita alta al administrador.
                  </p>
                </div>

                {error ? (
                  <div className="rounded-xl border border-[#ba1a1a]/20 bg-[#ffdad6] px-4 py-3 text-sm text-[#93000a]">
                    {error}
                  </div>
                ) : null}

                <button
                  type="submit"
                  disabled={isDisabled}
                  className="w-full text-white py-5 rounded-full font-label font-semibold tracking-wide shadow-lg shadow-[#041627]/20 hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-60 disabled:cursor-not-allowed"
                  style={{ background: "linear-gradient(135deg, #041627 0%, #1a2b3c 100%)" }}
                >
                  {isLoading ? "Validando credenciales..." : "Iniciar Sesión en Socio AI"}
                </button>
              </form>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
