"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";

import { hasSessionState, logoutSession } from "../../../lib/auth-session";
import { updateCliente } from "../../../lib/api/clientes";
import {
  getClienteConfiguracion,
  getPreguntasDinamicas,
  getTiposEntidad,
  saveClienteConfiguracion,
  type PreguntaDinamica,
  type TipoEntidadOption,
} from "../../../lib/api/configuracion";
import { getPerfil, savePerfil } from "../../../lib/api/perfil";
import { authFetchJson } from "../../../lib/api";
import { useAppState } from "../../../components/providers/AppStateProvider";
import { SECTOR_OPTIONS } from "../../../lib/sectorCatalog";
import type { PerfilPayload } from "../../../types/perfil";

type Params = {
  clienteId?: string | string[];
};

type QaState = {
  nomina: boolean;
  inventarios: boolean;
  ingresos_complejos: boolean;
  partes_relacionadas: boolean;
  multi_moneda: boolean;
  auditado_anteriormente: boolean;
  opinion_anterior_calificada: boolean;
  cambios_management: boolean;
  presion_resultados: boolean;
  regulado: boolean;
  subsidiarias: boolean;
  litigios: boolean;
  estimaciones_complejas: boolean;
  erp_implementado: boolean;
};

function toClienteId(raw: string | string[] | undefined): string {
  if (Array.isArray(raw)) return raw[0] ?? "";
  return raw ?? "";
}

function asRecord(value: unknown): Record<string, unknown> {
  return typeof value === "object" && value !== null ? (value as Record<string, unknown>) : {};
}

function toBool(value: unknown): boolean {
  return value === true;
}

function toStringValue(value: unknown, fallback = ""): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

export default function OnboardingClientePage() {
  const router = useRouter();
  const { resetClientState } = useAppState();
  const params = useParams<Params>();
  const clienteId = useMemo(() => toClienteId(params?.clienteId), [params]);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [nombreLegal, setNombreLegal] = useState("");
  const [sector, setSector] = useState("Holding");
  const [tipoEntidad, setTipoEntidad] = useState("HOLDING");
  const [tamano, setTamano] = useState("Mediana");
  const [pais, setPais] = useState("Ecuador");
  const [fiscalYear, setFiscalYear] = useState("2025");
  const [marco, setMarco] = useState("NIIF para PYMES");
  const [normativaCliente, setNormativaCliente] = useState("NIIF");
  const [norma, setNorma] = useState("NIAs");
  const [faseAuditoria, setFaseAuditoria] = useState("planificacion");
  const [tbFile, setTbFile] = useState("");
  const [mayorFile, setMayorFile] = useState("");
  const [tbSelectedFile, setTbSelectedFile] = useState<File | null>(null);
  const [mayorSelectedFile, setMayorSelectedFile] = useState<File | null>(null);
  const [tiposEntidad, setTiposEntidad] = useState<TipoEntidadOption[]>([]);
  const [preguntasDinamicas, setPreguntasDinamicas] = useState<PreguntaDinamica[]>([]);
  const [respuestasDinamicas, setRespuestasDinamicas] = useState<Record<string, string>>({});
  const [qa, setQa] = useState<QaState>({
    nomina: false,
    inventarios: false,
    ingresos_complejos: true,
    partes_relacionadas: true,
    multi_moneda: false,
    auditado_anteriormente: false,
    opinion_anterior_calificada: false,
    cambios_management: false,
    presion_resultados: false,
    regulado: false,
    subsidiarias: false,
    litigios: false,
    estimaciones_complejas: false,
    erp_implementado: false,
  });

  useEffect(() => {
    if (!hasSessionState()) {
      router.replace("/");
      return;
    }

    let active = true;
    async function load(): Promise<void> {
      if (!clienteId) {
        setError("Cliente invalido.");
        setLoading(false);
        return;
      }
      try {
        const [perfil, clienteResponse, tipos, configuracion] = await Promise.all([
          getPerfil(clienteId),
          authFetchJson<{ data?: Record<string, unknown> }>(`/api/clientes/${clienteId}`),
          getTiposEntidad(),
          getClienteConfiguracion(clienteId),
        ]);
        if (!active) return;

        const root = asRecord(perfil.perfil);
        const cliente = asRecord(root.cliente);
        const encargo = asRecord(root.encargo);
        const cuestionario = asRecord(root.cuestionario_auditoria);
        const carga = asRecord(root.carga_archivos);
        const clienteApi = asRecord(clienteResponse?.data);

        setTiposEntidad(tipos);
        setNombreLegal(typeof cliente.nombre_legal === "string" && cliente.nombre_legal.trim() ? cliente.nombre_legal : toStringValue(clienteApi.nombre, clienteId));
        setSector(
          typeof cliente.sector === "string" && cliente.sector.trim()
            ? cliente.sector
            : toStringValue(clienteApi.sector, "Holding"),
        );
        setTipoEntidad(configuracion?.tipo_entidad || toStringValue(clienteApi.tipo_entidad, tipos[0]?.tipo || "HOLDING"));
        setTamano(toStringValue(clienteApi.tamano, "Mediana"));
        setPais(typeof cliente.pais === "string" && cliente.pais.trim() ? cliente.pais : "Ecuador");
        setFiscalYear(String(encargo.anio_activo ?? "2025"));
        setMarco(typeof encargo.marco_referencial === "string" && encargo.marco_referencial.trim() ? encargo.marco_referencial : "NIIF para PYMES");
        setNormativaCliente(toStringValue(clienteApi.normativa, "NIIF"));
        setNorma(typeof encargo.norma_auditoria === "string" && encargo.norma_auditoria.trim() ? encargo.norma_auditoria : "NIAs");
        setFaseAuditoria(typeof encargo.fase_actual === "string" && encargo.fase_actual.trim() ? encargo.fase_actual : "planificacion");
        setTbFile(typeof carga.trial_balance_nombre === "string" ? carga.trial_balance_nombre : "");
        setMayorFile(typeof carga.libro_mayor_nombre === "string" ? carga.libro_mayor_nombre : "");
        setRespuestasDinamicas(configuracion?.respuestas || {});
        setQa({
          nomina: toBool(cuestionario.nomina),
          inventarios: toBool(cuestionario.inventarios),
          ingresos_complejos: toBool(cuestionario.ingresos_complejos),
          partes_relacionadas: toBool(cuestionario.partes_relacionadas),
          multi_moneda: toBool(cuestionario.multi_moneda),
          auditado_anteriormente: toBool(cuestionario.auditado_anteriormente),
          opinion_anterior_calificada: toBool(cuestionario.opinion_anterior_calificada),
          cambios_management: toBool(cuestionario.cambios_management),
          presion_resultados: toBool(cuestionario.presion_resultados),
          regulado: toBool(cuestionario.regulado),
          subsidiarias: toBool(cuestionario.subsidiarias),
          litigios: toBool(cuestionario.litigios),
          estimaciones_complejas: toBool(cuestionario.estimaciones_complejas),
          erp_implementado: toBool(cuestionario.erp_implementado),
        });
      } catch {
        if (!active) return;
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [clienteId, router]);

  useEffect(() => {
    let active = true;
    async function loadPreguntas(): Promise<void> {
      if (!tipoEntidad.trim()) {
        if (active) setPreguntasDinamicas([]);
        return;
      }
      try {
        const preguntas = await getPreguntasDinamicas(tipoEntidad);
        if (!active) return;
        setPreguntasDinamicas(preguntas);
        setRespuestasDinamicas((prev) => {
          const next = { ...prev };
          for (const pregunta of preguntas) {
            if (!next[pregunta.id] && pregunta.default) {
              next[pregunta.id] = pregunta.default;
            }
          }
          return next;
        });
      } catch {
        if (active) setPreguntasDinamicas([]);
      }
    }

    void loadPreguntas();
    return () => {
      active = false;
    };
  }, [tipoEntidad]);

  function updateQa(key: keyof QaState): void {
    setQa((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  function updateRespuestaDinamica(id: string, value: string): void {
    setRespuestasDinamicas((prev) => ({ ...prev, [id]: value }));
  }

  async function handleSave(goToDashboard: boolean): Promise<void> {
    if (!clienteId) return;
    setError("");
    setSuccess("");
    setSaving(true);

    try {
      let trialBalanceNombre = tbFile;
      let libroMayorNombre = mayorFile;

      if (tbSelectedFile) {
        const formData = new FormData();
        formData.append("file", tbSelectedFile);
        const result = await authFetchJson<{ data: { original_name: string; stored_as: string } }>(
          `/api/trial-balance/${clienteId}/upload?kind=tb`,
          { method: "POST", body: formData },
        );
        trialBalanceNombre = result?.data?.original_name || tbSelectedFile.name;
      }

      if (mayorSelectedFile) {
        const formData = new FormData();
        formData.append("file", mayorSelectedFile);
        const result = await authFetchJson<{ data: { original_name: string; stored_as: string } }>(
          `/api/trial-balance/${clienteId}/upload?kind=mayor`,
          { method: "POST", body: formData },
        );
        libroMayorNombre = result?.data?.original_name || mayorSelectedFile.name;
      }

      if (!trialBalanceNombre.trim()) {
        throw new Error("Debes seleccionar un archivo de Trial Balance para continuar.");
      }

      await updateCliente(clienteId, {
        nombre: nombreLegal,
        sector,
        tipo_entidad: tipoEntidad,
        tamano,
        normativa: normativaCliente,
      });

      if (tipoEntidad.trim()) {
        await saveClienteConfiguracion(clienteId, {
          tipo_entidad: tipoEntidad,
          respuestas: respuestasDinamicas,
        });
      }

      const payload: PerfilPayload = {
        cliente: {
          nombre_legal: nombreLegal,
          sector,
          pais,
        },
        encargo: {
          anio_activo: Number(fiscalYear),
          marco_referencial: marco,
          norma_auditoria: norma,
          fase_actual: faseAuditoria,
          tipo_entidad: tipoEntidad,
          tamano,
          normativa_cliente: normativaCliente,
        },
        cuestionario_auditoria: qa,
        configuracion_industria: {
          tipo_entidad: tipoEntidad,
          respuestas: respuestasDinamicas,
        },
        carga_archivos: {
          trial_balance_nombre: trialBalanceNombre,
          libro_mayor_nombre: libroMayorNombre,
        },
      };

      await savePerfil(clienteId, payload);
      resetClientState(clienteId);
      setTbFile(trialBalanceNombre);
      setMayorFile(libroMayorNombre);
      setTbSelectedFile(null);
      setMayorSelectedFile(null);
      setSuccess("Onboarding guardado correctamente.");
      router.push(goToDashboard ? `/dashboard/${clienteId}` : `/perfil/${clienteId}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "No se pudo guardar el onboarding.";
      setError(message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-surface px-6 py-10">
        <div className="sovereign-card h-24 animate-pulse bg-[#edf2f7]" />
      </div>
    );
  }

  const perfilCompleto = Boolean(
    nombreLegal.trim() &&
      sector.trim() &&
      pais.trim() &&
      fiscalYear.trim() &&
      marco.trim() &&
      norma.trim() &&
      tipoEntidad.trim() &&
      tamano.trim() &&
      normativaCliente.trim(),
  );
  const cuestionarioRespondido = Object.values(qa).some((value) => value === true);
  const configuracionIndustriaRespondida =
    preguntasDinamicas.length === 0 || preguntasDinamicas.every((pregunta) => String(respuestasDinamicas[pregunta.id] || "").trim().length > 0);
  const tbCargado = Boolean(tbFile.trim());
  const mayorCargado = Boolean(mayorFile.trim());
  const faseDefinida = ["planificacion", "ejecucion", "informe"].includes(faseAuditoria);

  const checklist = [
    { label: "Datos de cliente", ok: perfilCompleto },
    { label: "Configuración de industria", ok: configuracionIndustriaRespondida },
    { label: "Cuestionario de auditoria", ok: cuestionarioRespondido },
    { label: "Trial Balance", ok: tbCargado },
    { label: "Libro Mayor", ok: mayorCargado },
    { label: "Fase de auditoria", ok: faseDefinida },
  ];

  return (
    <div className="min-h-screen bg-[#f7fafc]">
      <nav className="fixed top-0 w-full z-40 bg-white border-b border-black/5 px-6 md:px-10 py-4 flex items-center justify-between">
        <div>
          <h1 className="font-headline text-3xl text-[#041627]">Onboarding de Cliente</h1>
          <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500">{clienteId}</p>
        </div>
        <div className="flex items-center gap-2">
          <button type="button" onClick={() => router.push("/clientes")} className="sovereign-card !p-2 !px-3 text-[11px] uppercase tracking-[0.14em] text-slate-500">
            Volver a clientes
          </button>
          <button
            type="button"
            onClick={() => {
              void logoutSession().finally(() => router.push("/"));
            }}
            className="sovereign-card !p-2 !px-3 text-[11px] uppercase tracking-[0.14em] text-slate-500 hover:text-[#041627]"
          >
            Cerrar sesión
          </button>
        </div>
      </nav>

      <main className="pt-28 px-6 md:px-10 pb-12 max-w-[1440px] mx-auto space-y-8">
        {error ? <div className="sovereign-card text-sm text-[#93000a] bg-[#ffdad6] border border-[#ba1a1a]/20">{error}</div> : null}
        {success ? <div className="sovereign-card text-sm text-[#065f46] bg-[#ecfdf5] border border-[#047857]/20">{success}</div> : null}

        <section className="grid grid-cols-1 xl:grid-cols-12 gap-8">
          <article className="xl:col-span-8 space-y-8">
            <div className="sovereign-card">
              <h2 className="font-headline text-3xl text-[#041627] mb-6">1. Datos base del cliente</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <label className="flex flex-col gap-2 md:col-span-2">
                  <span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Nombre legal</span>
                  <input className="ghost-input" value={nombreLegal} onChange={(e) => setNombreLegal(e.target.value)} />
                </label>
                <label className="flex flex-col gap-2">
                  <span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Sector</span>
                  <select className="ghost-input" value={sector} onChange={(e) => setSector(e.target.value)}>
                    {SECTOR_OPTIONS.map((item) => (
                      <option key={item} value={item}>{item}</option>
                    ))}
                  </select>
                </label>
                <label className="flex flex-col gap-2">
                  <span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">País</span>
                  <input className="ghost-input" value={pais} onChange={(e) => setPais(e.target.value)} />
                </label>
                <label className="flex flex-col gap-2">
                  <span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Tipo de entidad</span>
                  <select className="ghost-input" value={tipoEntidad} onChange={(e) => setTipoEntidad(e.target.value)}>
                    {tiposEntidad.map((item) => (
                      <option key={item.tipo} value={item.tipo}>{item.nombre}</option>
                    ))}
                  </select>
                </label>
                <label className="flex flex-col gap-2">
                  <span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Tamaño</span>
                  <select className="ghost-input" value={tamano} onChange={(e) => setTamano(e.target.value)}>
                    <option value="PyME">PyME</option>
                    <option value="Mediana">Mediana</option>
                    <option value="Grande">Grande</option>
                  </select>
                </label>
                <label className="flex flex-col gap-2">
                  <span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Año fiscal</span>
                  <input className="ghost-input" value={fiscalYear} onChange={(e) => setFiscalYear(e.target.value)} />
                </label>
                <label className="flex flex-col gap-2">
                  <span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Marco</span>
                  <select className="ghost-input" value={marco} onChange={(e) => setMarco(e.target.value)}>
                    <option>NIIF para PYMES</option>
                    <option>NIIF Plenas</option>
                    <option>US GAAP</option>
                  </select>
                </label>
                <label className="flex flex-col gap-2">
                  <span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Normativa cliente</span>
                  <select className="ghost-input" value={normativaCliente} onChange={(e) => setNormativaCliente(e.target.value)}>
                    <option value="NIIF">NIIF</option>
                    <option value="NIIF PYMES">NIIF PYMES</option>
                    <option value="USGAP">USGAP</option>
                  </select>
                </label>
                <label className="flex flex-col gap-2">
                  <span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Norma de auditoría</span>
                  <select className="ghost-input" value={norma} onChange={(e) => setNorma(e.target.value)}>
                    <option>NIAs</option>
                    <option>Normas Locales</option>
                    <option>PCAOB</option>
                  </select>
                </label>
              </div>
            </div>

            <div className="sovereign-card">
              <h2 className="font-headline text-3xl text-[#041627] mb-6">2. Configuración dinámica de industria</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {preguntasDinamicas.map((pregunta) => (
                  <label key={pregunta.id} className={`flex flex-col gap-2 ${pregunta.tipo === "text" ? "md:col-span-2" : ""}`}>
                    <span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold flex items-center gap-2">
                      {pregunta.texto}
                      {pregunta.critica ? <span className="rounded-full bg-[#ffdad6] px-2 py-0.5 text-[10px] text-[#93000a]">Crítica</span> : null}
                    </span>
                    {pregunta.tipo === "select" ? (
                      <select
                        className="ghost-input"
                        value={respuestasDinamicas[pregunta.id] || pregunta.default || ""}
                        onChange={(e) => updateRespuestaDinamica(pregunta.id, e.target.value)}
                      >
                        <option value="">Selecciona una opción</option>
                        {(pregunta.opciones || []).map((opcion) => (
                          <option key={`${pregunta.id}-${opcion.valor}`} value={opcion.valor}>{opcion.label}</option>
                        ))}
                      </select>
                    ) : (
                      <input
                        className="ghost-input"
                        value={respuestasDinamicas[pregunta.id] || ""}
                        onChange={(e) => updateRespuestaDinamica(pregunta.id, e.target.value)}
                        placeholder={pregunta.placeholder || pregunta.default || "Ingresa tu respuesta"}
                      />
                    )}
                    {pregunta.ayuda ? <span className="text-xs text-slate-500">{pregunta.ayuda}</span> : null}
                  </label>
                ))}
              </div>
            </div>

            <div className="sovereign-card">
              <h2 className="font-headline text-3xl text-[#041627] mb-6">3. Preguntas clave de auditoría</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <label className="md:col-span-2 flex flex-col gap-2 mb-2">
                  <span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Fase actual de auditoría</span>
                  <select className="ghost-input" value={faseAuditoria} onChange={(e) => setFaseAuditoria(e.target.value)}>
                    <option value="planificacion">Planificación</option>
                    <option value="ejecucion">Ejecución</option>
                    <option value="informe">Informe</option>
                  </select>
                </label>
                {[
                  { key: "nomina", label: "Tiene nómina relevante" },
                  { key: "inventarios", label: "Tiene inventarios materiales" },
                  { key: "ingresos_complejos", label: "Ingresos complejos / multiproducto" },
                  { key: "partes_relacionadas", label: "Hay partes relacionadas" },
                  { key: "multi_moneda", label: "Opera en multimoneda" },
                ].map((item) => {
                  const checked = qa[item.key as keyof QaState];
                  return (
                    <button
                      key={item.key}
                      type="button"
                      onClick={() => updateQa(item.key as keyof QaState)}
                      className={`text-left rounded-xl p-4 border transition-colors ${checked ? "bg-[#002f30] text-white border-[#002f30]" : "bg-white text-slate-700 border-black/10"}`}
                    >
                      <p className="text-sm font-semibold">{item.label}</p>
                    </button>
                  );
                })}

                <div className="md:col-span-2 mt-2 mb-1 flex items-center gap-3">
                  <span className="text-xs uppercase tracking-[0.16em] text-slate-500 font-bold whitespace-nowrap">Factores de Riesgo y Entorno</span>
                  <div className="flex-1 h-px bg-black/10" />
                </div>

                {[
                  { key: "auditado_anteriormente", label: "Cliente auditado en ejercicios anteriores" },
                  { key: "opinion_anterior_calificada", label: "Opinión anterior con salvedades o adversa", disabled: !qa.auditado_anteriormente },
                  { key: "cambios_management", label: "Cambios recientes en alta dirección o gerencia" },
                  { key: "presion_resultados", label: "Existe presión de resultados (deuda, cotización, bonos)" },
                  { key: "regulado", label: "Entidad regulada (superintendencia, bolsa, gobierno)" },
                  { key: "subsidiarias", label: "Tiene subsidiarias o estructura holding" },
                  { key: "litigios", label: "Litigios o contingencias significativas" },
                  { key: "estimaciones_complejas", label: "Estimaciones contables complejas (deterioro, provisiones, VR)" },
                  { key: "erp_implementado", label: "Tiene sistema ERP implementado (SAP, Oracle, etc.)" },
                ].map((item) => {
                  const checked = qa[item.key as keyof QaState];
                  const isDisabled = item.disabled === true;
                  return (
                    <button
                      key={item.key}
                      type="button"
                      onClick={() => !isDisabled && updateQa(item.key as keyof QaState)}
                      disabled={isDisabled}
                      className={`text-left rounded-xl p-4 border transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${checked ? "bg-[#002f30] text-white border-[#002f30]" : "bg-white text-slate-700 border-black/10"}`}
                    >
                      <p className="text-sm font-semibold">{item.label}</p>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="sovereign-card">
              <h2 className="font-headline text-3xl text-[#041627] mb-6">4. Carga de archivos base</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <label className="rounded-xl border-2 border-dashed border-black/15 p-5 bg-[#f8fafc]">
                  <p className="text-sm font-semibold text-[#041627]">Trial Balance</p>
                  <p className="text-xs text-slate-500 mt-1">CSV/XLSX</p>
                  <input
                    type="file"
                    className="mt-4 text-sm"
                    onChange={(e) => {
                      const file = e.target.files?.[0] ?? null;
                      setTbSelectedFile(file);
                      setTbFile(file?.name ?? "");
                    }}
                    accept=".csv,.xlsx,.xls"
                  />
                  {tbFile ? <p className="text-xs text-slate-600 mt-2">Archivo: {tbFile}</p> : null}
                </label>

                <label className="rounded-xl border-2 border-dashed border-black/15 p-5 bg-[#f8fafc]">
                  <p className="text-sm font-semibold text-[#041627]">Libro Mayor</p>
                  <p className="text-xs text-slate-500 mt-1">CSV/XLSX</p>
                  <input
                    type="file"
                    className="mt-4 text-sm"
                    onChange={(e) => {
                      const file = e.target.files?.[0] ?? null;
                      setMayorSelectedFile(file);
                      setMayorFile(file?.name ?? "");
                    }}
                    accept=".csv,.xlsx,.xls"
                  />
                  {mayorFile ? <p className="text-xs text-slate-600 mt-2">Archivo: {mayorFile}</p> : null}
                </label>
              </div>
            </div>
          </article>

          <aside className="xl:col-span-4 space-y-6">
            <div className="rounded-editorial p-7 text-white" style={{ background: "linear-gradient(135deg, #041627 0%, #1a2b3c 100%)" }}>
              <p className="text-xs uppercase tracking-[0.16em] text-[#89d3d4]">Socio AI</p>
              <h3 className="font-headline text-3xl mt-3">Motor listo para iniciar</h3>
              <p className="text-sm text-slate-200 mt-3 leading-relaxed">
                Con este onboarding terminamos setup de cliente. Luego ya puedes navegar Dashboard, Risk Engine y Áreas con contexto real.
              </p>
            </div>

            <div className="sovereign-card">
              <h4 className="font-headline text-2xl text-[#041627]">Checklist</h4>
              <ul className="mt-4 space-y-3 text-sm text-slate-700">
                {checklist.map((item) => (
                  <li key={item.label} className="flex gap-2">
                    <span className={`material-symbols-outlined text-base ${item.ok ? "text-[#002f30]" : "text-slate-400"}`}>
                      {item.ok ? "check_circle" : "radio_button_unchecked"}
                    </span>
                    <span>{item.label}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="grid grid-cols-1 gap-3">
              <button
                type="button"
                onClick={() => void handleSave(false)}
                disabled={saving}
                className="w-full py-3 rounded-xl border border-black/10 bg-white text-slate-700 font-semibold disabled:opacity-60"
              >
                {saving ? "Guardando..." : "Guardar y abrir perfil"}
              </button>
              <button
                type="button"
                onClick={() => void handleSave(true)}
                disabled={saving}
                className="w-full py-3 rounded-xl text-white font-semibold shadow-sm disabled:opacity-60"
                style={{ background: "linear-gradient(135deg, #041627 0%, #1a2b3c 100%)" }}
              >
                {saving ? "Guardando..." : "Arrancar sistema"}
              </button>
            </div>
          </aside>
        </section>
      </main>
    </div>
  );
}

