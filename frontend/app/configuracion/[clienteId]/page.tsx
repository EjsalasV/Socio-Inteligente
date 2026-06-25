"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import QuestionHelp from "../../../components/ui/QuestionHelp";
import { authFetchJson } from "../../../lib/api";
import { updateCliente } from "../../../lib/api/clientes";
import {
  getClienteConfiguracion,
  getPreguntasDinamicas,
  getTiposEntidad,
  saveClienteConfiguracion,
  type ClienteConfiguracion,
  type PreguntaDinamica,
  type TipoEntidadOption,
} from "../../../lib/api/configuracion";
import { getPerfil } from "../../../lib/api/perfil";
import { getDashboardData } from "../../../lib/api/dashboard";
import { SECTOR_OPTIONS } from "../../../lib/sectorCatalog";

type Params = {
  clienteId?: string | string[];
};

type ClienteMeta = {
  nombre: string;
  sector: string;
  tipo_entidad: string;
  tamano: string;
  normativa: string;
};

function toClienteId(raw: string | string[] | undefined): string {
  if (Array.isArray(raw)) return raw[0] ?? "";
  return raw ?? "";
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function toStringValue(value: unknown, fallback = ""): string {
  return typeof value === "string" && value.trim() ? value : fallback;
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

function formatDate(value?: string | null): string {
  if (!value) return "Sin guardado previo";
  try {
    return new Intl.DateTimeFormat("es-CO", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

export default function ConfiguracionClientePage() {
  const params = useParams<Params>();
  const clienteId = useMemo(() => toClienteId(params?.clienteId), [params]);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [clienteMeta, setClienteMeta] = useState<ClienteMeta>({
    nombre: "",
    sector: "Holding",
    tipo_entidad: "HOLDING",
    tamano: "Mediana",
    normativa: "NIIF",
  });
  const [clienteNombre, setClienteNombre] = useState("");
  const [tipoOptions, setTipoOptions] = useState<TipoEntidadOption[]>([]);
  const [preguntas, setPreguntas] = useState<PreguntaDinamica[]>([]);
  const [respuestas, setRespuestas] = useState<Record<string, string>>({});
  const [configInfo, setConfigInfo] = useState<ClienteConfiguracion | null>(null);
  const [generalConfig, setGeneralConfig] = useState<Record<string, string>>({});

  useEffect(() => {
    let active = true;
    async function load(): Promise<void> {
      if (!clienteId) {
        setError("Cliente invÃ¡lido.");
        setLoading(false);
        return;
      }

      try {
        const [dashboard, clienteResponse, tipos, configuracion, perfil] = await Promise.all([
          getDashboardData(clienteId),
          authFetchJson<{ data?: Record<string, unknown> }>(`/api/clientes/${clienteId}`),
          getTiposEntidad(),
          getClienteConfiguracion(clienteId),
          getPerfil(clienteId),
        ]);
        if (!active) return;

        const cliente = isRecord(clienteResponse?.data) ? clienteResponse.data : {};
        const nombre = toStringValue(cliente.nombre, dashboard.nombre_cliente || clienteId);
        const tipo = configuracion?.tipo_entidad || toStringValue(cliente.tipo_entidad, tipos[0]?.tipo || "HOLDING");
        const meta: ClienteMeta = {
          nombre,
          sector: toStringValue(cliente.sector, dashboard.sector || "Holding"),
          tipo_entidad: tipo,
          tamano: toStringValue(cliente.tamano, "Mediana"),
          normativa: toStringValue(cliente.normativa, "NIIF"),
        };

        setClienteNombre(dashboard.nombre_cliente || nombre);
        setClienteMeta(meta);
        setTipoOptions(tipos);
        setConfigInfo(configuracion);
        const perfilRoot = isRecord(perfil?.perfil) ? perfil.perfil : {};
        const general = isRecord(perfilRoot.configuracion_general) ? perfilRoot.configuracion_general : {};
        setGeneralConfig(
          isRecord(general.respuestas)
            ? Object.fromEntries(Object.entries(general.respuestas).map(([key, value]) => [key, String(value ?? "")]))
            : {},
        );

        const preguntasTipo = await getPreguntasDinamicas(tipo);
        if (!active) return;
        setPreguntas(preguntasTipo);
        setRespuestas(buildInitialAnswers(preguntasTipo, configuracion?.respuestas || {}));
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "No se pudo cargar la configuraciÃ³n del cliente.");
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [clienteId]);

  useEffect(() => {
    let active = true;
    async function loadPreguntas(): Promise<void> {
      if (!clienteMeta.tipo_entidad.trim()) {
        if (active) setPreguntas([]);
        return;
      }
      try {
        const preguntasTipo = await getPreguntasDinamicas(clienteMeta.tipo_entidad);
        if (!active) return;
        setPreguntas(preguntasTipo);
        setRespuestas((prev) => buildInitialAnswers(preguntasTipo, prev));
      } catch {
        if (!active) setPreguntas([]);
      }
    }

    if (!loading) {
      void loadPreguntas();
    }
    return () => {
      active = false;
    };
  }, [clienteMeta.tipo_entidad, loading]);

  const criticalCount = useMemo(() => preguntas.filter((pregunta) => pregunta.critica).length, [preguntas]);
  const answeredCount = useMemo(
    () => preguntas.filter((pregunta) => String(respuestas[pregunta.id] || "").trim().length > 0).length,
    [preguntas, respuestas],
  );
  const criticalAnswered = useMemo(
    () =>
      preguntas.filter((pregunta) => pregunta.critica).every((pregunta) => String(respuestas[pregunta.id] || "").trim().length > 0),
    [preguntas, respuestas],
  );
  const dirty = useMemo(() => {
    const saved = configInfo?.respuestas || {};
    const metaMatches =
      clienteMeta.tipo_entidad === (configInfo?.tipo_entidad || clienteMeta.tipo_entidad);
    if (!metaMatches) return true;
    const questionIds = new Set([...Object.keys(saved), ...Object.keys(respuestas)]);
    for (const key of questionIds) {
      if (String(saved[key] || "") !== String(respuestas[key] || "")) return true;
    }
    return false;
  }, [clienteMeta.tipo_entidad, configInfo, respuestas]);

  async function handleSave(): Promise<void> {
    if (!clienteId) return;
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      await updateCliente(clienteId, {
        nombre: clienteMeta.nombre,
        sector: clienteMeta.sector,
        tipo_entidad: clienteMeta.tipo_entidad,
        tamano: clienteMeta.tamano,
        normativa: clienteMeta.normativa,
      });

      const savedConfig = await saveClienteConfiguracion(clienteId, {
        tipo_entidad: clienteMeta.tipo_entidad,
        respuestas,
      });
      setConfigInfo(savedConfig);
      setSuccess("ConfiguraciÃ³n guardada y lista para impactar anÃ¡lisis y hallazgos.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo guardar la configuraciÃ³n.");
    } finally {
      setSaving(false);
    }
  }

  function handleResetDefaults(): void {
    setRespuestas(buildInitialAnswers(preguntas, {}));
    setSuccess("");
  }

  if (loading) return <DashboardSkeleton />;
  if (error && !clienteNombre) return <ErrorMessage message={error} />;

  return (
    <div className="space-y-6 pb-8">
      <section className="sovereign-card">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">ConfiguraciÃ³n del cliente</p>
            <h1 className="font-headline text-4xl text-[#041627] mt-2">
              {clienteNombre || clienteMeta.nombre || clienteId}
            </h1>
            <p className="text-sm text-slate-600 mt-3 max-w-3xl">
              Define los parÃ¡metros de industria que van a contextualizar el anÃ¡lisis inteligente, el pipeline y la lectura del encargo.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <Link href={`/dashboard/${clienteId}`} className="px-4 py-2 rounded-xl border border-black/10 bg-white text-slate-700 text-sm font-semibold">
              Ver dashboard
            </Link>
            <Link href={`/perfil/${clienteId}`} className="px-4 py-2 rounded-xl border border-black/10 bg-white text-slate-700 text-sm font-semibold">
              Abrir perfil
            </Link>
            <Link href={`/onboarding/${clienteId}`} className="px-4 py-2 rounded-xl border border-black/10 bg-white text-slate-700 text-sm font-semibold">
              Ir a onboarding
            </Link>
          </div>
        </div>
      </section>

      {error ? <div className="sovereign-card text-sm text-[#93000a] bg-[#ffdad6] border border-[#ba1a1a]/20">{error}</div> : null}
      {success ? <div className="sovereign-card text-sm text-[#065f46] bg-[#ecfdf5] border border-[#047857]/20">{success}</div> : null}

      <section className="sovereign-card space-y-3">
        <p className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">ConfiguraciÃ³n general del encargo</p>
        <div className="flex flex-wrap gap-2 text-sm text-slate-700">
          <span className="rounded-full bg-slate-100 px-3 py-1">Guardada al crear el cliente</span>
          <span className="rounded-full bg-slate-100 px-3 py-1">
            {Object.keys(generalConfig).length} respuestas base
          </span>
        </div>
        {Object.keys(generalConfig).length ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
            {Object.entries(generalConfig).slice(0, 6).map(([key, value]) => (
              <div key={key} className="rounded-xl border border-[#041627]/10 bg-[#f8fafc] p-3">
                <p className="text-[11px] uppercase tracking-[0.14em] text-slate-500 font-bold">{key}</p>
                <p className="text-sm text-[#041627] mt-1">{value}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-600">
            AÃºn no hay configuraciÃ³n general guardada. Esta se captura al crear el cliente.
          </p>
        )}
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        <article className="sovereign-card">
          <p className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Preguntas activas</p>
          <p className="font-headline text-3xl text-[#041627] mt-2">{preguntas.length}</p>
          <p className="text-sm text-slate-500 mt-2">ParÃ¡metros cargados para {clienteMeta.tipo_entidad || "la industria actual"}.</p>
        </article>
        <article className="sovereign-card">
          <p className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">CrÃ­ticas respondidas</p>
          <p className="font-headline text-3xl text-[#041627] mt-2">
            {criticalCount === 0 ? "0" : `${preguntas.filter((p) => p.critica && String(respuestas[p.id] || "").trim()).length}/${criticalCount}`}
          </p>
          <p className="text-sm text-slate-500 mt-2">{criticalAnswered ? "Lista para anÃ¡lisis contextual." : "AÃºn faltan parÃ¡metros clave."}</p>
        </article>
        <article className="sovereign-card">
          <p className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Respuestas completas</p>
          <p className="font-headline text-3xl text-[#041627] mt-2">{answeredCount}/{preguntas.length}</p>
          <p className="text-sm text-slate-500 mt-2">Cobertura actual del cuestionario dinÃ¡mico.</p>
        </article>
        <article className="sovereign-card">
          <p className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Ãšltimo guardado</p>
          <p className="font-headline text-xl text-[#041627] mt-2">{formatDate(configInfo?.updated_at)}</p>
          <p className="text-sm text-slate-500 mt-2">{dirty ? "Tienes cambios sin guardar." : "Sin cambios pendientes."}</p>
        </article>
      </section>

      <section className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        <article className="xl:col-span-4 sovereign-card space-y-4">
          <div>
            <p className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Metadatos base</p>
            <h2 className="font-headline text-2xl text-[#041627] mt-2">Contexto del cliente</h2>
          </div>

          <label className="flex flex-col gap-2">
            <span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Nombre legal</span>
            <input
              className="ghost-input"
              value={clienteMeta.nombre}
              onChange={(e) => setClienteMeta((prev) => ({ ...prev, nombre: e.target.value }))}
            />
          </label>

          <label className="flex flex-col gap-2">
            <span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Sector</span>
            <select
              className="ghost-input"
              value={clienteMeta.sector}
              onChange={(e) => setClienteMeta((prev) => ({ ...prev, sector: e.target.value }))}
            >
              {SECTOR_OPTIONS.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-2">
            <span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Tipo de entidad</span>
            <select
              className="ghost-input"
              value={clienteMeta.tipo_entidad}
              onChange={(e) => setClienteMeta((prev) => ({ ...prev, tipo_entidad: e.target.value }))}
            >
              {tipoOptions.map((item) => (
                <option key={item.tipo} value={item.tipo}>{item.nombre}</option>
              ))}
            </select>
          </label>

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-1 gap-4">
            <label className="flex flex-col gap-2">
              <span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">TamaÃ±o</span>
              <select
                className="ghost-input"
                value={clienteMeta.tamano}
                onChange={(e) => setClienteMeta((prev) => ({ ...prev, tamano: e.target.value }))}
              >
                <option value="PyME">PyME</option>
                <option value="Mediana">Mediana</option>
                <option value="Grande">Grande</option>
              </select>
            </label>

            <label className="flex flex-col gap-2">
              <span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Normativa</span>
              <select
                className="ghost-input"
                value={clienteMeta.normativa}
                onChange={(e) => setClienteMeta((prev) => ({ ...prev, normativa: e.target.value }))}
              >
                <option value="NIIF">NIIF</option>
                <option value="NIIF PYMES">NIIF PYMES</option>
                <option value="USGAP">USGAP</option>
              </select>
            </label>
          </div>

          <div className="rounded-xl border border-[#041627]/10 bg-[#f8fafc] p-4">
            <p className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Impacto</p>
            <p className="text-sm text-slate-600 mt-2">
              Esta configuraciÃ³n ya alimenta el analizador inteligente y el pipeline de auditorÃ­a para ajustar expectativas segÃºn industria.
            </p>
          </div>
        </article>

        <article className="xl:col-span-8 sovereign-card space-y-5">
          <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">ParÃ¡metros dinÃ¡micos</p>
              <h2 className="font-headline text-2xl text-[#041627] mt-2">Cuestionario por industria</h2>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={handleResetDefaults}
                className="px-4 py-2 rounded-xl border border-black/10 bg-white text-slate-700 text-sm font-semibold"
              >
                Restaurar defaults
              </button>
              <button
                type="button"
                onClick={() => void handleSave()}
                disabled={saving}
                className="px-4 py-2 rounded-xl text-white text-sm font-semibold disabled:opacity-60"
                style={{ background: "linear-gradient(135deg, #041627 0%, #1a2b3c 100%)" }}
              >
                {saving ? "Guardando..." : "Guardar configuraciÃ³n"}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {preguntas.map((pregunta) => (
              <label key={pregunta.id} className={`flex flex-col gap-2 ${pregunta.tipo === "text" ? "md:col-span-2" : ""}`}>
                <span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold flex items-center gap-2">
                  {pregunta.texto}
                  {pregunta.critica ? <span className="rounded-full bg-[#ffdad6] px-2 py-0.5 text-[10px] text-[#93000a]">CrÃ­tica</span> : null}
                  <QuestionHelp text={pregunta.ayuda} />
                </span>
                {pregunta.tipo === "select" ? (
                  <select
                    className="ghost-input"
                    value={respuestas[pregunta.id] || pregunta.default || ""}
                    onChange={(e) => setRespuestas((prev) => ({ ...prev, [pregunta.id]: e.target.value }))}
                  >
                    <option value="">Selecciona una opciÃ³n</option>
                    {(pregunta.opciones || []).map((opcion) => (
                      <option key={`${pregunta.id}-${opcion.valor}`} value={opcion.valor}>{opcion.label}</option>
                    ))}
                  </select>
                ) : (
                  <input
                    className="ghost-input"
                    value={respuestas[pregunta.id] || ""}
                    onChange={(e) => setRespuestas((prev) => ({ ...prev, [pregunta.id]: e.target.value }))}
                    placeholder={pregunta.placeholder || pregunta.default || "Ingresa tu respuesta"}
                  />
                )}
              </label>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}

