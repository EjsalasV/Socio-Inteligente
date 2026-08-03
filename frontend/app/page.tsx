"use client";

import Image from "next/image";
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

      if (typeof window !== "undefined") {
        if (window.sessionStorage) {
          window.sessionStorage.setItem("socio_auth_token", token);
        }
        window.localStorage.setItem("socio_auth_token", token);
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
    <div className="min-h-screen overflow-hidden bg-[linear-gradient(180deg,#fbf8f1_0%,#f4ede1_100%)] text-slate-900">
      <main className="grid min-h-screen lg:grid-cols-[1.15fr_0.85fr]">
        <section className="relative hidden overflow-hidden bg-[#041627] text-white lg:block">
          <Image
            src="/images/login-bitacora-hero.png"
            alt="Bitácora de auditoría Socio AI"
            fill
            priority
            className="object-cover object-center"
          />
          <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(4,22,39,0.82)_0%,rgba(4,22,39,0.42)_48%,rgba(4,22,39,0.64)_100%)]" />
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_18%_18%,rgba(165,239,240,0.08),transparent_18%),radial-gradient(circle_at_75%_35%,rgba(184,154,90,0.08),transparent_20%)]" />

          <div className="relative flex h-full flex-col justify-between px-10 py-10 xl:px-14 xl:py-12">
            <div className="flex items-center gap-4">
              <div className="grid h-12 w-12 place-items-center rounded-2xl border border-white/10 bg-white/10 text-[#a5eff0] shadow-[0_10px_30px_rgba(0,0,0,0.18)] backdrop-blur-sm">
                <span className="material-symbols-outlined text-2xl">verified_user</span>
              </div>
              <div>
                <p className="text-[11px] uppercase tracking-[0.28em] text-[#b89a5a]">Dossier de auditoría</p>
                <h1 className="font-headline text-3xl tracking-wide">Socio AI</h1>
              </div>
            </div>

            <div className="max-w-xl pt-6">
              <p className="text-[11px] uppercase tracking-[0.28em] text-[#a7d9d3]">Inteligencia que respalda tu juicio</p>
              <h2 className="mt-4 font-headline text-5xl leading-[1.03] xl:text-6xl">
                Elevar el juicio.
                <br />
                Respaldar cada decisión.
                <br />
                <span className="text-[#a5eff0]">Consolidar la confianza.</span>
              </h2>
              <p className="mt-5 max-w-lg text-base leading-relaxed text-slate-200/85">
                Socio AI combina experiencia y tecnología para transformar auditorías en decisiones respaldadas,
                transparentes y defendibles.
              </p>
            </div>

            <div className="grid max-w-2xl gap-3 sm:grid-cols-3">
              <div className="rounded-2xl border border-white/10 bg-white/8 px-4 py-3 backdrop-blur-sm">
                <p className="text-[10px] uppercase tracking-[0.22em] text-[#a7d9d3]">NIA</p>
                <p className="mt-1 text-sm text-slate-100">Criterio consistente</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/8 px-4 py-3 backdrop-blur-sm">
                <p className="text-[10px] uppercase tracking-[0.22em] text-[#a7d9d3]">NIIF</p>
                <p className="mt-1 text-sm text-slate-100">Lectura financiera</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/8 px-4 py-3 backdrop-blur-sm">
                <p className="text-[10px] uppercase tracking-[0.22em] text-[#a7d9d3]">Trazabilidad</p>
                <p className="mt-1 text-sm text-slate-100">Evidencia verificable</p>
              </div>
            </div>
          </div>
        </section>

        <section className="relative flex items-center justify-center px-5 py-8 sm:px-8 lg:px-10">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(184,154,90,0.08),transparent_26%),radial-gradient(circle_at_80%_70%,rgba(59,127,122,0.08),transparent_30%)]" />
          <div className="relative w-full max-w-[540px]">
            <div className="mb-5 flex items-center gap-3 lg:hidden">
              <div className="grid h-11 w-11 place-items-center rounded-2xl bg-[#041627] text-[#a5eff0]">
                <span className="material-symbols-outlined text-2xl">verified_user</span>
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-[0.24em] text-[#b89a5a]">Dossier de auditoría</p>
                <h2 className="font-headline text-3xl text-[#041627]">Socio AI</h2>
              </div>
            </div>

            <div className="rounded-[32px] border border-[#d8e1e8] bg-[#fbf8f1] p-6 shadow-[0_24px_70px_rgba(24,28,30,0.1)] sm:p-8">
              <div className="mx-auto mb-6 flex h-12 w-12 items-center justify-center rounded-full border border-[#b89a5a]/40 bg-white text-[#b89a5a]">
                <span className="material-symbols-outlined text-2xl">lock</span>
              </div>

              <div className="text-center">
                <p className="text-[11px] uppercase tracking-[0.28em] text-[#b89a5a]">Iniciar sesión</p>
                <h2 className="mt-4 font-headline text-4xl text-[#041627]">Bienvenido de nuevo</h2>
                <p className="mt-2 text-sm text-slate-600">Accede a tu dossier y continúa con confianza.</p>
              </div>

              <div className="mt-8 rounded-[26px] border border-[#d8e1e8] bg-white/90 p-5 sm:p-6">
                <form className="space-y-5" onSubmit={handleSubmit}>
                  <div className="space-y-2">
                    <label
                      className="block text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500"
                      htmlFor="username"
                    >
                      Correo electrónico
                    </label>
                    <input
                      id="username"
                      name="username"
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder="tu@empresa.com"
                      className="w-full rounded-2xl border border-[#d8e1e8] bg-[#faf7f0] px-4 py-4 text-slate-900 outline-none transition focus:border-[#3b7f7a] focus:ring-2 focus:ring-[#a7d9d3]/60"
                      autoComplete="username"
                    />
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-end justify-between gap-4">
                      <label
                        className="block text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500"
                        htmlFor="password"
                      >
                        Contraseña
                      </label>
                      <button
                        type="button"
                        className="rounded-md text-[11px] font-semibold uppercase tracking-[0.18em] text-[#3b7f7a] transition hover:text-[#041627] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#a7d9d3]/70"
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
                      placeholder="Ingresa tu contraseña"
                      className="w-full rounded-2xl border border-[#d8e1e8] bg-[#faf7f0] px-4 py-4 text-slate-900 outline-none transition focus:border-[#3b7f7a] focus:ring-2 focus:ring-[#a7d9d3]/60"
                      autoComplete="current-password"
                    />
                  </div>

                  <div className="flex items-start gap-3 rounded-2xl border border-[#b89a5a]/20 bg-[#f5efe2] px-4 py-3">
                    <span className="material-symbols-outlined text-xl text-[#b89a5a]">verified_user</span>
                    <p className="text-[13px] font-medium text-[#243041]">
                      Autenticación empresarial y acceso seguro para tu equipo.
                    </p>
                  </div>

                  <div className="flex items-start gap-3 rounded-2xl border border-[#d8e1e8] bg-[#f3f7f8] px-4 py-3">
                    <span className="material-symbols-outlined text-xl text-[#041627]">info</span>
                    <p className="text-[13px] font-medium text-slate-600">
                      Usa tus credenciales autorizadas para este cliente. Si no tienes acceso, solicita alta al administrador.
                    </p>
                  </div>

                  {error ? (
                    <div className="rounded-2xl border border-[#ba1a1a]/20 bg-[#ffdad6] px-4 py-3 text-sm text-[#93000a]">
                      {error}
                    </div>
                  ) : null}

                  <button
                    type="submit"
                    disabled={isDisabled}
                    className="group inline-flex w-full items-center justify-center gap-2 rounded-full bg-[linear-gradient(135deg,#2f7c78_0%,#0f364a_100%)] px-6 py-4 text-sm font-semibold uppercase tracking-[0.18em] text-white shadow-[0_18px_34px_rgba(4,22,39,0.2)] transition hover:opacity-95 active:scale-[0.99] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#a7d9d3] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <span>{isLoading ? "Validando credenciales..." : "Iniciar sesión"}</span>
                    <span className="material-symbols-outlined text-[18px] transition-transform group-hover:translate-x-0.5">
                      arrow_forward
                    </span>
                  </button>
                </form>
              </div>

              <div className="mt-6 flex items-center justify-between gap-4 text-xs uppercase tracking-[0.18em] text-slate-500">
                <span>Cifrado empresarial</span>
                <span>Acceso con trazabilidad</span>
              </div>
            </div>

            <p className="mt-5 text-center text-sm text-[#243041]/70">
              <a className="underline underline-offset-4 transition hover:text-[#041627]" href="/landing">
                ¿Conoces Socio AI? Ver qué hacemos →
              </a>
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}
