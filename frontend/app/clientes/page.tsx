"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { useTour } from "../../components/tour/TourProvider";
import { hasSessionState, logoutSession } from "../../lib/auth-session";
import QuestionHelp from "../../components/ui/QuestionHelp";
import { archiveCliente, createCliente, getClientes, type ClienteOption } from "../../lib/api/clientes";
import {
  getPreguntasDinamicas,
  getTiposEntidad,
  type PreguntaDinamica,
  type TipoEntidadOption,
} from "../../lib/api/configuracion";
import { savePerfil } from "../../lib/api/perfil";
import { useUserPreferences } from "../../components/providers/UserPreferencesProvider";
import { SECTOR_OPTIONS } from "../../lib/sectorCatalog";

function slugify(input: string): string {
  return input
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 40);
}

function buildInitialAnswers(
  preguntas: PreguntaDinamica[],
  saved: Record<string, string>,
): Record<string, string> {
  const next: Record<string, string> = { ...saved };
  for (const pregunta of preguntas) {
    if (!next[pregunta.id] && pregunta.default) {
      next[pregunta.id] = pregunta.default;
    }
  }
  return next;
}

export default function ClientesPage() {
  const router = useRouter();
  const { activeModule, startTour, resetTours } = useTour();
  const { loading: prefsLoading, preferences, patchPreferences, session } = useUserPreferences();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [clientes, setClientes] = useState<ClienteOption[]>([]);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [showAllClients, setShowAllClients] = useState(false);

  const [nombre, setNombre] = useState("");
  const [sector, setSector] = useState("Holding");
  const [clienteIdManual, setClienteIdManual] = useState("");
  const [tipoEntidad, setTipoEntidad] = useState("HOLDING");
  const [tamano, setTamano] = useState("Mediana");
  const [normativa, setNormativa] = useState("NIIF");
  const [tiposEntidad, setTiposEntidad] = useState<TipoEntidadOption[]>([]);
  const [generalQuestions, setGeneralQuestions] = useState<PreguntaDinamica[]>([]);
  const [generalResponses, setGeneralResponses] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!hasSessionState()) {
      router.replace("/");
      return;
    }

    let active = true;
    async function load(): Promise<void> {
      try {
        const [list, tipos, general] = await Promise.all([
          getClientes(),
          getTiposEntidad(),
          getPreguntasDinamicas("GENERAL"),
        ]);
        if (!active) return;
        setClientes(list);
        setTiposEntidad(tipos);
        setGeneralQuestions(general);
        setGeneralResponses(buildInitialAnswers(general, {}));
      } catch (err) {
        if (!active) return;
        const message = err instanceof Error ? err.message : "No se pudo cargar la cartera de clientes.";
        setError(message);
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [router]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return clientes;
    return clientes.filter((c) => {
      const s = `${c.nombre} ${c.cliente_id} ${c.sector ?? ""}`.toLowerCase();
      return s.includes(q);
    });
  }, [clientes, search]);
  const firstClient = useMemo(() => clientes[0] ?? null, [clientes]);
  const visibleClients = useMemo(
    () => (showAllClients ? filtered : filtered.slice(0, 4)),
    [filtered, showAllClients],
  );
  const firstClientId = (visibleClients[0] ?? firstClient)?.cliente_id ?? "";
  const canManageUsers = useMemo(() => {
    const role = String(session?.role || "").toLowerCase();
    return role === "admin" || role === "socio";
  }, [session?.role]);
  const showIntroStrip = !prefsLoading && !preferences.onboarding_ui.welcome_seen;

  async function handleCreateClient(event: React.FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setError("");

    const cleanName = nombre.trim();
    if (!cleanName) {
      setError("Ingresa un nombre de cliente.");
      return;
    }

    const rawId = clienteIdManual.trim() || slugify(cleanName);
    if (!rawId) {
      setError("No se pudo generar el identificador del cliente.");
      return;
    }

    setSaving(true);
    try {
      const created = await createCliente({
        cliente_id: rawId,
        nombre: cleanName,
        sector,
        tipo_entidad: tipoEntidad,
        tamano,
        normativa,
      });

      await savePerfil(created.cliente_id, {
        cliente: {
          nombre_legal: cleanName,
          sector,
        },
        encargo: {
          anio_activo: new Date().getFullYear(),
          marco_referencial: normativa,
        },
        configuracion_general: {
          tipo_entidad: tipoEntidad,
          respuestas: generalResponses,
        },
      });

      setClientes((prev) => [created, ...prev.filter((x) => x.cliente_id !== created.cliente_id)]);
      setNombre("");
      setSector("Holding");
      setClienteIdManual("");
      setTipoEntidad("HOLDING");
      setTamano("Mediana");
      setNormativa("NIIF");
      setGeneralResponses(buildInitialAnswers(generalQuestions, {}));
      router.push(`/onboarding/${created.cliente_id}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "No se pudo crear el cliente.";
      setError(message);
    } finally {
      setSaving(false);
    }
  }

  async function handleArchiveClient(cliente: ClienteOption): Promise<void> {
    const confirmed = window.confirm(
      `Vas a archivar el cliente "${cliente.nombre}" (${cliente.cliente_id}). Dejará de mostrarse en la cartera, pero sus datos se conservan. ¿Continuar?`,
    );
    if (!confirmed) return;

    setDeletingId(cliente.cliente_id);
    setError("");
    try {
      await archiveCliente(cliente.cliente_id);
      setClientes((prev) => prev.filter((item) => item.cliente_id !== cliente.cliente_id));
    } catch (err) {
      const message = err instanceof Error ? err.message : "No se pudo archivar el cliente.";
      setError(message);
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#f4efe5_0%,#f8f4eb_40%,#f3eee4_100%)] text-slate-900">
      <div className="lg:grid lg:grid-cols-[262px_minmax(0,1fr)]">
        <aside className="hidden lg:flex lg:flex-col sticky top-0 h-screen bg-[#07182a] text-[#f6efe3] border-r border-white/10">
          <div className="px-6 py-6 border-b border-white/10">
            <div className="flex items-center gap-3">
              <div className="grid h-12 w-12 place-items-center rounded-2xl border border-[#a5eff0]/20 bg-white/5 text-[#a5eff0]">
                <span className="material-symbols-outlined text-[22px]">verified_user</span>
              </div>
              <div>
                <h1 className="font-headline text-3xl text-white">Socio AI</h1>
                <p className="text-[11px] uppercase tracking-[0.28em] text-[#c8b083]">Sovereign Intelligence</p>
              </div>
            </div>
          </div>

          <nav className="flex-1 px-4 py-5 overflow-y-auto">
            <p className="px-3 text-[10px] uppercase tracking-[0.28em] text-[#b8cbd8]/70">Navegación</p>
            <div className="mt-3 space-y-2">
              <Link href="/clientes" className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white shadow-[0_10px_30px_rgba(0,0,0,0.12)]">
                <span className="material-symbols-outlined text-[20px] text-[#c8b083]">folder_open</span>
                <span className="font-medium">Clientes</span>
              </Link>
              {firstClientId ? (
                <>
                  <Link href={`/perfil/${firstClientId}`} className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-[#d8e4ea] hover:bg-white/5">
                    <span className="material-symbols-outlined text-[20px] text-[#8ecfd3]">badge</span>
                    <span>Perfil Cliente</span>
                  </Link>
                  <Link href={`/dashboard/${firstClientId}`} className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-[#d8e4ea] hover:bg-white/5">
                    <span className="material-symbols-outlined text-[20px] text-[#8ecfd3]">dashboard</span>
                    <span>Dashboard</span>
                  </Link>
                  <Link href={`/risk-engine/${firstClientId}`} className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-[#d8e4ea] hover:bg-white/5">
                    <span className="material-symbols-outlined text-[20px] text-[#8ecfd3]">security</span>
                    <span>Risk Engine</span>
                  </Link>
                  <Link href={`/trial-balance/${firstClientId}`} className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-[#d8e4ea] hover:bg-white/5">
                    <span className="material-symbols-outlined text-[20px] text-[#8ecfd3]">account_balance_wallet</span>
                    <span>Trial Balance</span>
                  </Link>
                  <Link href={`/procedimientos`} className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-[#d8e4ea] hover:bg-white/5">
                    <span className="material-symbols-outlined text-[20px] text-[#8ecfd3]">fact_check</span>
                    <span>Procedimientos</span>
                  </Link>
                </>
              ) : null}
            </div>

            <div className="mt-8 border-t border-white/10 pt-5">
              <p className="px-3 text-[10px] uppercase tracking-[0.28em] text-[#b8cbd8]/70">Utilidades</p>
              <div className="mt-3 space-y-2">
                <button
                  type="button"
                  onClick={() => startTour("clientes")}
                  disabled={!activeModule}
                  className="w-full flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-[#d8e4ea] hover:bg-white/5 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span className="material-symbols-outlined text-[20px] text-[#c8b083]">book_2</span>
                  <span>Ver tutorial</span>
                </button>
                <button
                  type="button"
                  onClick={resetTours}
                  className="w-full flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-[#d8e4ea] hover:bg-white/5"
                >
                  <span className="material-symbols-outlined text-[20px] text-[#c8b083]">restart_alt</span>
                  <span>Reiniciar tutoriales</span>
                </button>
                {canManageUsers ? (
                  <button
                    type="button"
                    onClick={() => router.push("/admin")}
                    className="w-full flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-[#d8e4ea] hover:bg-white/5"
                  >
                    <span className="material-symbols-outlined text-[20px] text-[#c8b083]">admin_panel_settings</span>
                    <span>Admin</span>
                  </button>
                ) : null}
                <button
                  type="button"
                  onClick={() => {
                    void logoutSession().finally(() => router.push("/"));
                  }}
                  className="w-full flex items-center gap-3 rounded-2xl px-4 py-3 text-sm text-[#d8e4ea] hover:bg-white/5"
                >
                  <span className="material-symbols-outlined text-[20px] text-[#c8b083]">logout</span>
                  <span>Cerrar sesión</span>
                </button>
              </div>
            </div>
          </nav>

          <div className="px-6 py-5 border-t border-white/10 text-[11px] uppercase tracking-[0.24em] text-[#b8cbd8]/70">
            Centro de trabajo editorial
          </div>
        </aside>

        <div className="min-w-0">
          <header className="sticky top-0 z-30 border-b border-[#d9ccb6]/70 bg-[rgba(247,241,231,0.92)] backdrop-blur">
            <div className="flex items-center justify-between gap-4 px-5 py-4 lg:px-10">
              <div className="flex items-center gap-3 lg:hidden">
                <div className="grid h-11 w-11 place-items-center rounded-2xl bg-[#07182a] text-[#a5eff0]">
                  <span className="material-symbols-outlined text-[20px]">verified_user</span>
                </div>
                <div>
                  <h1 className="font-headline text-2xl text-[#041627]">Socio AI</h1>
                  <p className="text-[10px] uppercase tracking-[0.28em] text-[#8b7960]">Sovereign Intelligence</p>
                </div>
              </div>

              <div className="hidden lg:flex items-center gap-3">
                <span className="inline-flex items-center gap-2 rounded-full border border-[#d7cab4] bg-white/70 px-3 py-2 text-xs uppercase tracking-[0.2em] text-[#7f6b52]">
                  <span className="material-symbols-outlined text-[16px] text-[#b89a5a]">book_2</span>
                  Expediente clientes
                </span>
                <span className="inline-flex items-center gap-2 rounded-full border border-[#d7cab4] bg-white/70 px-3 py-2 text-xs uppercase tracking-[0.2em] text-[#7f6b52]">
                  <span className="material-symbols-outlined text-[16px] text-[#3b7f7a]">schedule</span>
                  Operativo
                </span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => startTour("clientes")}
                  disabled={!activeModule}
                  className="rounded-full border border-[#d7cab4] bg-white/70 px-4 py-2 text-[11px] uppercase tracking-[0.16em] text-[#7f6b52] hover:text-[#041627] disabled:opacity-50"
                >
                  Ver tutorial
                </button>
                <button
                  type="button"
                  onClick={resetTours}
                  className="rounded-full border border-[#d7cab4] bg-white/70 px-4 py-2 text-[11px] uppercase tracking-[0.16em] text-[#7f6b52] hover:text-[#041627]"
                >
                  Reiniciar tutoriales
                </button>
                {canManageUsers ? (
                  <button
                    type="button"
                    onClick={() => router.push("/admin")}
                    className="rounded-full border border-[#d7cab4] bg-white/70 px-4 py-2 text-[11px] uppercase tracking-[0.16em] text-[#7f6b52] hover:text-[#041627]"
                  >
                    Admin
                  </button>
                ) : null}
                <button
                  type="button"
                  onClick={() => {
                    void logoutSession().finally(() => router.push("/"));
                  }}
                  className="rounded-full border border-[#d7cab4] bg-white/70 px-4 py-2 text-[11px] uppercase tracking-[0.16em] text-[#7f6b52] hover:text-[#041627]"
                >
                  Cerrar sesión
                </button>
              </div>
            </div>
          </header>

          <main className="px-5 py-8 lg:px-10 lg:py-10 max-w-[1520px] mx-auto">
            <section className="relative overflow-hidden rounded-[34px] border border-[#d8cab2]/80 bg-[linear-gradient(180deg,#f7f2e9_0%,#f3ede1_100%)] px-5 py-6 shadow-[0_24px_80px_rgba(51,35,16,0.08)] lg:px-8 lg:py-8">
              <div className="relative grid gap-8 lg:grid-cols-[minmax(0,1.2fr)_340px]">
                <div className="min-w-0">
                  <p className="text-[11px] uppercase tracking-[0.34em] text-[#b38948]">Cartera de clientes</p>
                  <div className="mt-3 flex flex-wrap items-end gap-4">
                    <h2 data-tour="clientes-title" className="max-w-3xl font-headline text-5xl leading-[0.95] text-[#041627] lg:text-[4.8rem]">
                      Selecciona un cliente o crea uno nuevo
                    </h2>
                    <div className="hidden xl:flex items-center gap-3 rounded-[24px] border border-[#d7cab4] bg-white/70 px-4 py-3 shadow-[0_10px_30px_rgba(0,0,0,0.04)]">
                      <span className="material-symbols-outlined text-[22px] text-[#b89a5a]">attach_file</span>
                      <div className="text-left">
                        <p className="text-[10px] uppercase tracking-[0.2em] text-[#8b7960]">Expediente</p>
                        <p className="font-headline text-lg text-[#041627]">Clientes</p>
                      </div>
                    </div>
                  </div>
                  <p className="mt-4 max-w-3xl text-base leading-relaxed text-slate-600">
                    Gestiona tu cartera con claridad y arranca el siguiente encargo desde una vista más ligera, más editorial y más fácil de escanear.
                  </p>

                  <div className="mt-8 grid gap-3 md:grid-cols-5">
                    {[
                      ["1", "Cliente"],
                      ["2", "Onboarding"],
                      ["3", "Trial Balance"],
                      ["4", "Risk Engine"],
                      ["5", "Ejecución"],
                    ].map(([number, label]) => (
                      <div key={label} className="flex items-center gap-3 rounded-full border border-[#d7cab4] bg-white/70 px-4 py-3">
                        <span className="grid h-8 w-8 place-items-center rounded-full bg-[#3b7f7a] text-sm font-semibold text-white">{number}</span>
                        <span className="text-sm text-slate-700">{label}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="hidden lg:block">
                  <div className="relative h-full min-h-[260px] rounded-[28px] border border-[#d7cab4] bg-white/60 p-5 shadow-[0_18px_50px_rgba(24,28,30,0.08)]">
                    <div className="absolute -top-3 right-6 rounded-full border border-[#d7cab4] bg-[#f6f0e7] px-3 py-1 text-[10px] uppercase tracking-[0.26em] text-[#8b7960] shadow-sm">
                      Dossier
                    </div>
                    <div className="absolute top-4 right-4 h-28 w-28 rounded-full border border-[#d7cab4]/70 bg-white/50" />
                    <div className="absolute bottom-5 right-5 flex flex-col items-center gap-1 rounded-full border border-[#d7cab4] bg-[#f7f2e9] px-4 py-3">
                      <span className="font-headline text-2xl text-[#041627]">SA</span>
                      <span className="text-[9px] uppercase tracking-[0.22em] text-[#8b7960]">Sello AI</span>
                    </div>
                    <p className="text-[10px] uppercase tracking-[0.26em] text-[#8b7960]">Socio AI / Clientes</p>
                    <h3 className="mt-2 max-w-[220px] font-headline text-4xl leading-[0.98] text-[#041627]">
                      Un índice que parece expediente, no panel genérico.
                    </h3>
                    <p className="mt-4 max-w-[240px] text-sm leading-relaxed text-slate-600">
                      Un orden más silencioso para abrir clientes, continuar el onboarding y volver al trabajo sin ruido.
                    </p>
                  </div>
                </div>
              </div>
            </section>

            <section className="mt-5 rounded-[28px] border border-[#d7cab4]/80 bg-white/72 px-5 py-4 shadow-[0_12px_40px_rgba(24,28,30,0.05)]">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <p className="text-[10px] uppercase tracking-[0.24em] text-[#8b7960]">Ruta recomendada</p>
                  <p className="mt-1 font-headline text-2xl text-[#041627]">1) Crear cliente  2) Completar perfil  3) Revisar trial balance  4) Priorizar riesgos  5) Ejecutar</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => startTour("clientes")}
                    className="rounded-full border border-[#d7cab4] bg-white px-4 py-2 text-[11px] uppercase tracking-[0.16em] text-[#7f6b52]"
                  >
                    Ver tour clientes
                  </button>
                  {firstClientId ? (
                    <>
                      <Link
                        href={`/perfil/${firstClientId}`}
                        className="rounded-full bg-[#041627] px-4 py-2 text-[11px] uppercase tracking-[0.16em] text-white shadow-[0_12px_24px_rgba(4,22,39,0.22)]"
                      >
                        Empezar onboarding
                      </Link>
                      <Link
                        href={`/configuracion/${firstClientId}`}
                        className="rounded-full border border-[#d7cab4] bg-white px-4 py-2 text-[11px] uppercase tracking-[0.16em] text-[#7f6b52]"
                      >
                        Ajustes del cliente
                      </Link>
                      <Link
                        href={`/dashboard/${firstClientId}`}
                        className="rounded-full border border-[#d7cab4] bg-white px-4 py-2 text-[11px] uppercase tracking-[0.16em] text-[#7f6b52]"
                      >
                        Ir a dashboard
                      </Link>
                    </>
                  ) : null}
                </div>
              </div>
            </section>

            {showIntroStrip ? (
              <section className="mt-5 rounded-[28px] border border-[#d7cab4]/80 bg-[#07182a] px-5 py-4 text-white shadow-[0_18px_40px_rgba(4,22,39,0.18)]">
                <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.26em] text-[#a5eff0]">Bienvenida</p>
                    <h3 className="mt-1 font-headline text-3xl">Centro de Clientes</h3>
                    <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-200">
                      Aquí empieza todo el flujo. Puedes tomar un mini tutorial o ir directo a crear tu primer cliente.
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        void patchPreferences({
                          onboarding_ui: {
                            welcome_seen: true,
                            dismissed: false,
                          },
                        });
                        startTour("clientes");
                      }}
                      className="rounded-full bg-white px-4 py-2 text-[11px] uppercase tracking-[0.16em] text-[#041627]"
                    >
                      Iniciar tutorial
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        void patchPreferences({
                          onboarding_ui: {
                            welcome_seen: true,
                            dismissed: false,
                          },
                        });
                        document.querySelector('[data-tour="clientes-form"]')?.scrollIntoView({ behavior: "smooth", block: "center" });
                      }}
                      className="rounded-full border border-white/20 bg-white/5 px-4 py-2 text-[11px] uppercase tracking-[0.16em] text-white"
                    >
                      Crear cliente
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        void patchPreferences({
                          onboarding_ui: {
                            welcome_seen: true,
                          },
                        });
                      }}
                      className="rounded-full border border-white/20 bg-white/5 px-4 py-2 text-[11px] uppercase tracking-[0.16em] text-white/80"
                    >
                      Omitir por ahora
                    </button>
                  </div>
                </div>
              </section>
            ) : null}

            {error ? <div className="mt-5 rounded-[24px] border border-[#ba1a1a]/20 bg-[#ffdad6] px-5 py-4 text-sm text-[#93000a] shadow-[0_10px_30px_rgba(186,26,26,0.08)]">{error}</div> : null}

            <section className="mt-6 grid grid-cols-1 xl:grid-cols-[1.3fr_0.9fr] gap-6">
              <article className="sovereign-card !p-0 overflow-hidden bg-[#fbf8f2]">
                <div className="flex flex-col gap-4 border-b border-[#d7cab4]/70 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.24em] text-[#8b7960]">Índice de clientes</p>
                    <h3 className="font-headline text-3xl text-[#041627] mt-1">Clientes creados</h3>
                  </div>
                  <input
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Buscar por nombre, sector o ID"
                    data-tour="clientes-search"
                    className="ghost-input w-full lg:w-[320px] bg-white/80"
                  />
                </div>

                <div className="px-4 py-4 lg:px-6 lg:py-6">
                  {loading ? (
                    <div className="space-y-3">
                      <div className="h-20 rounded-[22px] bg-[#eef2f4] animate-pulse" />
                      <div className="h-20 rounded-[22px] bg-[#eef2f4] animate-pulse" />
                      <div className="h-20 rounded-[22px] bg-[#eef2f4] animate-pulse" />
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {visibleClients.map((cliente, index) => {
                        const stageLabel = index === 0 ? "En ejecución" : index === 1 ? "Onboarding" : index === 2 ? "Planificación" : "Pausado";
                        const stageTone =
                          index === 0
                            ? "bg-[#dceff0] text-[#356f70]"
                            : index === 1
                              ? "bg-[#f3ead7] text-[#8b6b2f]"
                              : index === 2
                                ? "bg-[#dfe8f1] text-[#496681]"
                                : "bg-[#ececec] text-[#737373]";
                        const initials = cliente.nombre
                          .split(" ")
                          .filter(Boolean)
                          .slice(0, 2)
                          .map((word) => word[0])
                          .join("")
                          .toUpperCase()
                          .slice(0, 2);

                        return (
                          <article
                            key={cliente.cliente_id}
                            className="rounded-[24px] border border-[#d7cab4]/70 bg-white px-4 py-4 shadow-[0_10px_25px_rgba(24,28,30,0.04)] transition hover:-translate-y-[1px] hover:shadow-[0_16px_36px_rgba(24,28,30,0.08)]"
                          >
                            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                              <div className="flex min-w-0 gap-4">
                                <div className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-[#07182a] text-lg font-headline text-white">
                                  {initials || "SA"}
                                </div>
                                <div className="min-w-0">
                                  <div className="flex flex-wrap items-center gap-2">
                                    <h4 className="min-w-0 font-headline text-2xl text-[#041627]">{cliente.nombre}</h4>
                                    <span className={`rounded-full px-3 py-1 text-[11px] uppercase tracking-[0.16em] ${stageTone}`}>{stageLabel}</span>
                                  </div>
                                  <p className="mt-1 text-sm text-slate-600">
                                    {cliente.sector || "Sin sector"} · ID: {cliente.cliente_id}
                                    {cliente.tipo_entidad ? ` · Tipo: ${cliente.tipo_entidad}` : ""}
                                  </p>
                                  <p className="mt-2 text-xs uppercase tracking-[0.18em] text-[#8b7960]">
                                    Última actividad: {index === 0 ? "Hoy, 10:24" : index === 1 ? "Ayer, 16:58" : index === 2 ? "23 may, 09:11" : "Sin actividad reciente"}
                                  </p>
                                </div>
                              </div>

                              <div className="flex flex-wrap items-center gap-2 lg:justify-end">
                                <Link
                                  data-tour="clientes-open-dashboard-link"
                                  href={`/dashboard/${cliente.cliente_id}`}
                                  className="inline-flex items-center gap-2 rounded-full bg-[#041627] px-4 py-2 text-[11px] uppercase tracking-[0.18em] text-white shadow-[0_12px_26px_rgba(4,22,39,0.22)]"
                                >
                                  Abrir dashboard
                                  <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
                                </Link>
                                <Link
                                  data-tour="clientes-onboarding-link"
                                  href={`/onboarding/${cliente.cliente_id}`}
                                  className="rounded-full border border-[#d7cab4] bg-white px-4 py-2 text-[11px] uppercase tracking-[0.16em] text-[#7f6b52]"
                                >
                                  Onboarding
                                </Link>
                                <Link
                                  href={`/configuracion/${cliente.cliente_id}`}
                                  className="rounded-full border border-[#d7cab4] bg-white px-4 py-2 text-[11px] uppercase tracking-[0.16em] text-[#7f6b52]"
                                >
                                  Ajustes
                                </Link>
                                <button
                                  type="button"
                                  onClick={() => void handleArchiveClient(cliente)}
                                  disabled={deletingId === cliente.cliente_id}
                                  className="rounded-full border border-[#ba1a1a]/20 bg-[#ffdad6]/40 px-4 py-2 text-[11px] uppercase tracking-[0.16em] text-[#93000a] disabled:opacity-60"
                                >
                                  {deletingId === cliente.cliente_id ? "Archivando..." : "Archivar"}
                                </button>
                              </div>
                            </div>

                            <div className="mt-4 flex items-center gap-3">
                              <div className="h-1.5 flex-1 rounded-full bg-[#eef0ec]">
                                <div
                                  className="h-full rounded-full bg-gradient-to-r from-[#3b7f7a] to-[#b89a5a]"
                                  style={{ width: `${72 - index * 11}%` }}
                                />
                              </div>
                              <span className="text-xs uppercase tracking-[0.16em] text-[#8b7960]">
                                Progreso {index === 0 ? "64%" : index === 1 ? "38%" : index === 2 ? "24%" : "12%"}
                              </span>
                            </div>
                          </article>
                        );
                      })}
                      {!visibleClients.length ? (
                        <div className="rounded-[22px] border border-dashed border-[#d7cab4] bg-white/70 px-5 py-8 text-sm text-slate-500">
                          No hay clientes con ese filtro.
                        </div>
                      ) : null}

                      {filtered.length > 4 ? (
                        <div className="rounded-[22px] border border-[#d7cab4] bg-white/70 px-5 py-4">
                          <button
                            type="button"
                            onClick={() => setShowAllClients((value) => !value)}
                            className="inline-flex items-center gap-2 text-sm text-[#041627]"
                          >
                            {showAllClients ? "Mostrar menos" : "Ver todos los clientes"}
                            <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                          </button>
                        </div>
                      ) : null}
                    </div>
                  )}
                </div>
              </article>

              <article data-tour="clientes-form" className="sovereign-card !p-0 overflow-hidden bg-[#fbf7f0]">
                <div className="flex items-start justify-between gap-4 border-b border-[#d7cab4]/70 px-6 py-5">
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.24em] text-[#8b7960]">Nuevo expediente</p>
                    <h3 className="font-headline text-3xl text-[#041627] mt-1">Nuevo cliente</h3>
                    <p className="mt-2 text-sm leading-relaxed text-slate-600">
                      Captura lo esencial y te llevo al onboarding inicial sin llenar la pantalla de ruido.
                    </p>
                  </div>
                  <div className="grid h-14 w-14 place-items-center rounded-full border border-[#d7cab4] bg-[#f6f0e7] text-[#b89a5a] shadow-sm">
                    <span className="material-symbols-outlined text-[22px]">description</span>
                  </div>
                </div>

                <form className="space-y-4 px-6 py-6" onSubmit={handleCreateClient}>
                  <label className="flex flex-col gap-2">
                    <span className="text-[10px] uppercase tracking-[0.24em] text-[#8b7960] font-bold">Nombre legal</span>
                    <input className="ghost-input bg-white/80" value={nombre} onChange={(e) => setNombre(e.target.value)} placeholder="Ej. Compañía del Sur S.A." />
                  </label>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <label className="flex flex-col gap-2">
                      <span className="text-[10px] uppercase tracking-[0.24em] text-[#8b7960] font-bold">Sector</span>
                      <select className="ghost-input bg-white/80" value={sector} onChange={(e) => setSector(e.target.value)}>
                        {SECTOR_OPTIONS.map((item) => (
                          <option key={item} value={item}>
                            {item}
                          </option>
                        ))}
                      </select>
                    </label>

                    <label className="flex flex-col gap-2">
                      <span className="text-[10px] uppercase tracking-[0.24em] text-[#8b7960] font-bold">Tipo de entidad</span>
                      <select className="ghost-input bg-white/80" value={tipoEntidad} onChange={(e) => setTipoEntidad(e.target.value)}>
                        {tiposEntidad.map((item) => (
                          <option key={item.tipo} value={item.tipo}>
                            {item.nombre}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <label className="flex flex-col gap-2">
                      <span className="text-[10px] uppercase tracking-[0.24em] text-[#8b7960] font-bold">Tamaño</span>
                      <select className="ghost-input bg-white/80" value={tamano} onChange={(e) => setTamano(e.target.value)}>
                        <option value="PyME">PyME</option>
                        <option value="Mediana">Mediana</option>
                        <option value="Grande">Grande</option>
                      </select>
                    </label>

                    <label className="flex flex-col gap-2">
                      <span className="text-[10px] uppercase tracking-[0.24em] text-[#8b7960] font-bold">Normativa</span>
                      <select className="ghost-input bg-white/80" value={normativa} onChange={(e) => setNormativa(e.target.value)}>
                        <option value="NIIF">NIIF</option>
                        <option value="NIIF PYMES">NIIF PYMES</option>
                        <option value="USGAP">USGAP</option>
                      </select>
                    </label>
                  </div>

                  <label className="flex flex-col gap-2">
                    <span className="text-[10px] uppercase tracking-[0.24em] text-[#8b7960] font-bold">Cliente ID (opcional)</span>
                    <input className="ghost-input bg-white/80" value={clienteIdManual} onChange={(e) => setClienteIdManual(e.target.value)} placeholder="si_99283_glc" />
                  </label>

                  <details className="rounded-[24px] border border-[#d7cab4]/70 bg-white/70 px-4 py-4">
                    <summary className="cursor-pointer list-none text-[10px] uppercase tracking-[0.24em] text-[#8b7960] font-bold">
                      Configuración general
                    </summary>
                    <p className="mt-3 text-sm leading-relaxed text-slate-600">
                      Estas respuestas calibran el análisis del encargo (riesgos, materialidad e IA). Se guardan al crear el cliente y el onboarding añade el bloque específico del sector.
                    </p>
                    <div className="mt-4 grid grid-cols-1 gap-4">
                      {generalQuestions.map((pregunta) => (
                        <label key={pregunta.id} className="flex flex-col gap-2">
                          <span className="text-[10px] uppercase tracking-[0.24em] text-[#8b7960] font-bold flex items-center gap-2">
                            {pregunta.texto}
                            {pregunta.critica ? <span className="rounded-full bg-[#ffdad6] px-2 py-0.5 text-[10px] text-[#93000a]">Crítica</span> : null}
                            <QuestionHelp text={pregunta.ayuda} />
                          </span>
                          {pregunta.tipo === "select" ? (
                            <select
                              className="ghost-input bg-white/80"
                              value={generalResponses[pregunta.id] || pregunta.default || ""}
                              onChange={(e) => setGeneralResponses((prev) => ({ ...prev, [pregunta.id]: e.target.value }))}
                            >
                              <option value="">Selecciona una opción</option>
                              {(pregunta.opciones || []).map((opcion) => (
                                <option key={`${pregunta.id}-${opcion.valor}`} value={opcion.valor}>
                                  {opcion.label}
                                </option>
                              ))}
                            </select>
                          ) : (
                            <input
                              className="ghost-input bg-white/80"
                              value={generalResponses[pregunta.id] || ""}
                              onChange={(e) => setGeneralResponses((prev) => ({ ...prev, [pregunta.id]: e.target.value }))}
                              placeholder={pregunta.placeholder || pregunta.default || "Ingresa tu respuesta"}
                            />
                          )}
                        </label>
                      ))}
                    </div>
                  </details>

                  <div className="pt-2">
                    <button
                      type="submit"
                      disabled={saving}
                      className="w-full rounded-full px-5 py-4 text-sm font-semibold uppercase tracking-[0.18em] text-white shadow-[0_16px_34px_rgba(4,22,39,0.18)] disabled:opacity-60"
                      style={{ background: "linear-gradient(135deg, #041627 0%, #1a2b3c 100%)" }}
                    >
                      {saving ? "Creando cliente..." : "Crear cliente y comenzar onboarding"}
                    </button>
                    <p className="mt-3 text-center text-xs text-slate-500">
                      Solo tú y tu equipo tienen acceso.
                    </p>
                  </div>
                </form>
              </article>
            </section>
          </main>
        </div>
      </div>
    </div>
  );
}
