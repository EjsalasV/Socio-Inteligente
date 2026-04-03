"use client";

import { FormEvent, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { getClientes } from "../lib/api/clientes";
import { buildApiUrl, getApiBase } from "../lib/api-base";

type LoginApiData = {
  access_token?: string;
  token_type?: string;
  expires_in?: number;
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

export default function LoginPage() {
  const router = useRouter();

  const [username, setUsername] = useState<string>("joaosalas123@gmail.com");
  const [password, setPassword] = useState<string>("1234");
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
        body: JSON.stringify({ username: username.trim(), password }),
      });

      let payload: unknown = null;
      try {
        payload = (await res.json()) as unknown;
      } catch {
        payload = null;
      }

      if (!res.ok) {
        setError(extractErrorMessage(payload, "No se pudo iniciar sesion."));
        return;
      }

      const token = extractToken(payload);
      if (!token) {
        setError("La respuesta de autenticacion no incluyo token.");
        return;
      }

      localStorage.setItem("socio_token", token);

      try {
        await getClientes();
        router.push("/clientes");
      } catch {
        router.push("/clientes");
      }
    } catch {
      setError(`No se pudo conectar con el backend de autenticacion (${getApiBase()}).`);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-surface text-slate-900 font-body">
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 bg-[#041627]/5 z-10" />
        <img
          className="w-full h-full object-cover opacity-20 grayscale"
          src="https://lh3.googleusercontent.com/aida-public/AB6AXuAQmiNIqGU3a7SQsk-Qcs4zncgJoaZl-F0cRUV-WokgCOu9FtESa62hAhiVsLqXpSLHiYvMK3dMnyQJljfrPDgxk7oGJzWTRnjmGA8cGDn7RNbsuMrTTqeCflkfrEU8jvlDC5O_nkKESTwm99rVx-urEwHOomaxAMFxI6ys4Cc3O235owyHv1vwkM6lI5O3QRZ0tIhkqXdGx5QiP5ik9SI-Vc82GBTBDYl9ZbQyKXPvM7xzKliszLJ1Mn2pJWhRmHcbYYUBSgzBbOQ"
          alt="Fondo editorial de auditoria"
        />
      </div>

      <header className="fixed top-0 w-full z-50 bg-white/70 backdrop-blur-xl flex justify-between items-center px-8 py-4 shadow-sm shadow-slate-200/50">
        <div className="text-xl font-semibold tracking-tight text-slate-900 font-headline">
          Socio AI
        </div>
        <div className="flex items-center gap-2 text-slate-500">
          <span className="material-symbols-outlined text-sm">lock</span>
          <span className="text-[11px] uppercase tracking-widest font-medium">Entorno Encriptado</span>
        </div>
      </header>

      <main className="relative z-20 flex-grow flex items-center justify-center px-6 py-24">
        <div className="w-full max-w-lg">
          <div className="mb-12 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-white shadow-sm mb-6">
              <span
                className="material-symbols-outlined text-[#041627] text-3xl"
                style={{ fontVariationSettings: "'FILL' 1" }}
              >
                account_circle
              </span>
            </div>
            <h1 className="font-headline text-4xl md:text-5xl text-[#041627] mb-4 leading-tight">
              Acceso al Entorno de Auditoria
            </h1>
            <p className="text-slate-600 text-lg">
              Bienvenido de nuevo, Auditor. Su entorno seguro esta listo.
            </p>
          </div>

          <div className="rounded-xl p-8 md:p-12 shadow-[0_20px_40px_rgba(24,28,30,0.06)] bg-white/70 backdrop-blur-[20px] border border-white/60">
            <form className="space-y-8" onSubmit={handleSubmit}>
              <div className="space-y-2">
                <label className="text-[11px] uppercase tracking-widest font-semibold text-slate-500 block ml-1" htmlFor="username">
                  Correo electronico profesional
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
                    Contrasena
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
                  Autenticacion de dos factores (2FA) requerida para este entorno.
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
                {isLoading ? "Validando credenciales..." : "Iniciar Sesion en Socio AI"}
              </button>
            </form>
          </div>

          <div className="mt-8 text-center">
            <p className="text-[11px] uppercase tracking-widest font-medium text-slate-500">
              Problemas de acceso?{" "}
              <a className="text-[#041627] hover:underline underline-offset-4 decoration-2" href="mailto:soporte@socioai.app">
                Contactar Soporte
              </a>
            </p>
          </div>
        </div>
      </main>

      <footer className="relative z-20 w-full py-8 border-t border-slate-200/20 bg-slate-50/80 backdrop-blur-sm">
        <div className="flex flex-col md:flex-row justify-between items-center px-8 md:px-12 max-w-7xl mx-auto space-y-4 md:space-y-0">
          <div className="text-[11px] uppercase tracking-widest font-medium text-slate-400">
            © 2026 Socio AI. Todos los derechos reservados.
          </div>
          <div className="flex gap-6 md:gap-8 flex-wrap justify-center">
            <a className="text-[11px] uppercase tracking-widest font-medium text-slate-500 hover:text-[#0f766e] underline decoration-2 underline-offset-4 transition-opacity" href="https://socioai.app/privacy" target="_blank" rel="noreferrer">
              Privacy Policy
            </a>
            <a className="text-[11px] uppercase tracking-widest font-medium text-slate-500 hover:text-[#0f766e] underline decoration-2 underline-offset-4 transition-opacity" href="https://socioai.app/security" target="_blank" rel="noreferrer">
              Security Architecture
            </a>
            <a className="text-[11px] uppercase tracking-widest font-medium text-slate-500 hover:text-[#0f766e] underline decoration-2 underline-offset-4 transition-opacity" href="https://socioai.app/compliance" target="_blank" rel="noreferrer">
              Regulatory Compliance
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
