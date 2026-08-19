"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";

import { hasSessionState, logoutSession } from "../../../lib/auth-session";
import {
  deleteClienteDocumento,
  getClienteDocumentos,
  reprocessClienteDocumento,
  type ClienteDocumento,
  updateCliente,
  uploadClienteDocumento,
} from "../../../lib/api/clientes";
import {
  getTiposEntidad,
  type TipoEntidadOption,
} from "../../../lib/api/configuracion";
import { getPerfil, savePerfil } from "../../../lib/api/perfil";
import { authFetchJson } from "../../../lib/api";
import { useAppState } from "../../../components/providers/AppStateProvider";
import { SECTOR_OPTIONS } from "../../../lib/sectorCatalog";
import { normalizeClienteId } from "../../../lib/client-id";
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
  const clienteIdParam = useMemo(
    () => (Array.isArray(params?.clienteId) ? params?.clienteId[0] ?? "" : params?.clienteId ?? ""),
    [params],
  );
  const clienteId = useMemo(() => normalizeClienteId(clienteIdParam), [clienteIdParam]);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [saveError, setSaveError] = useState("");
  const [success, setSuccess] = useState("");
  const [loadRetryCount, setLoadRetryCount] = useState(0);

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
  const [scopeFinancials, setScopeFinancials] = useState("individual");
  const [visitPlan, setVisitPlan] = useState("preliminar_final");
  const [periodStart, setPeriodStart] = useState("2025-01-01");
  const [periodEnd, setPeriodEnd] = useState("2025-12-31");
  const [tbCutoffDate, setTbCutoffDate] = useState("2025-12-31");
  const [preliminaryDate, setPreliminaryDate] = useState("");
  const [finalDate, setFinalDate] = useState("");
  const [tbFile, setTbFile] = useState("");
  const [mayorFile, setMayorFile] = useState("");
  const [tbSelectedFile, setTbSelectedFile] = useState<File | null>(null);
  const [mayorSelectedFile, setMayorSelectedFile] = useState<File | null>(null);
  const [priorFinancialsFile, setPriorFinancialsFile] = useState("");
  const [priorFinancialsSelectedFiles, setPriorFinancialsSelectedFiles] = useState<File[]>([]);
  const [priorControlFile, setPriorControlFile] = useState("");
  const [priorControlSelectedFile, setPriorControlSelectedFile] = useState<File | null>(null);
  const [contextDocuments, setContextDocuments] = useState<ClienteDocumento[]>([]);
  const [tiposEntidad, setTiposEntidad] = useState<TipoEntidadOption[]>([]);
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
    if (clienteId && clienteId !== clienteIdParam) {
      router.replace(`/onboarding/${encodeURIComponent(clienteId)}`);
    }
  }, [clienteId, clienteIdParam, router]);

  useEffect(() => {
    if (!hasSessionState()) {
      router.replace("/");
      return;
    }

    let active = true;
    async function load(): Promise<void> {
      setLoading(true);
      setLoadError("");
      if (!clienteId) {
        if (active) {
          setLoadError("Cliente invalido.");
          setLoading(false);
        }
        return;
      }
      try {
        const [perfil, clienteResponse, tipos, contextDocuments] = await Promise.all([
          getPerfil(clienteId),
          authFetchJson<{ data?: Record<string, unknown> }>(`/api/clientes/${clienteId}`),
          getTiposEntidad(),
          getClienteDocumentos(clienteId),
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
        setTipoEntidad(toStringValue(clienteApi.tipo_entidad, tipos[0]?.tipo || "HOLDING"));
        setTamano(toStringValue(clienteApi.tamano, "Mediana"));
        setPais(typeof cliente.pais === "string" && cliente.pais.trim() ? cliente.pais : "Ecuador");
        setFiscalYear(String(encargo.anio_activo ?? "2025"));
        setMarco(typeof encargo.marco_referencial === "string" && encargo.marco_referencial.trim() ? encargo.marco_referencial : "NIIF para PYMES");
        setNormativaCliente(toStringValue(clienteApi.normativa, "NIIF"));
        setNorma(typeof encargo.norma_auditoria === "string" && encargo.norma_auditoria.trim() ? encargo.norma_auditoria : "NIAs");
        setFaseAuditoria(typeof encargo.fase_actual === "string" && encargo.fase_actual.trim() ? encargo.fase_actual : "planificacion");
        setScopeFinancials(toStringValue(encargo.alcance_estados, "individual"));
        setVisitPlan(toStringValue(encargo.esquema_visitas, "preliminar_final"));
        setPeriodStart(toStringValue(encargo.fecha_inicio_periodo, `${String(encargo.anio_activo ?? "2025")}-01-01`));
        setPeriodEnd(toStringValue(encargo.fecha_cierre_periodo, `${String(encargo.anio_activo ?? "2025")}-12-31`));
        setTbCutoffDate(toStringValue(encargo.fecha_corte_tb, `${String(encargo.anio_activo ?? "2025")}-12-31`));
        setPreliminaryDate(toStringValue(encargo.fecha_visita_preliminar));
        setFinalDate(toStringValue(encargo.fecha_visita_final));
        setContextDocuments(contextDocuments);
        setTbFile(typeof carga.trial_balance_nombre === "string" ? carga.trial_balance_nombre : "");
        setMayorFile(typeof carga.libro_mayor_nombre === "string" ? carga.libro_mayor_nombre : "");
        setPriorFinancialsFile(
          contextDocuments.find((item) => item.document_type === "prior_financial_statements")?.name ?? "",
        );
        setPriorControlFile(
          contextDocuments.find((item) => item.document_type === "prior_internal_control")?.name ?? "",
        );
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
      } catch (err) {
        if (!active) return;
        setLoadError(err instanceof Error ? err.message : "No se pudo cargar el onboarding.");
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [clienteId, router, loadRetryCount]);

  function retryLoad(): void {
    setLoadError("");
    setLoadRetryCount((count) => count + 1);
  }

  async function handleSave(): Promise<void> {
    if (!clienteId) return;
    setLoadError("");
    setSaveError("");
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

      const priorPeriod = String(Math.max(1900, Number(fiscalYear || new Date().getFullYear()) - 1));
      for (const file of priorFinancialsSelectedFiles) {
        const lower = file.name.toLowerCase();
        const role = lower.includes("nota") ? "notes" : lower.includes("opini") || lower.includes("informe") ? "audit_opinion" : "financial_statements";
        const document = await uploadClienteDocumento(clienteId, file, "prior_financial_statements", priorPeriod, role);
        setPriorFinancialsFile(document.name);
      }
      if (priorControlSelectedFile) {
        const document = await uploadClienteDocumento(
          clienteId,
          priorControlSelectedFile,
          "prior_internal_control",
          priorPeriod,
        );
        setPriorControlFile(document.name);
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
          alcance_estados: scopeFinancials,
          esquema_visitas: visitPlan,
          fecha_inicio_periodo: periodStart,
          fecha_cierre_periodo: periodEnd,
          fecha_corte_tb: tbCutoffDate,
          fecha_visita_preliminar: visitPlan === "preliminar_final" ? preliminaryDate : "",
          fecha_visita_final: finalDate,
          tipo_entidad: tipoEntidad,
          tamano,
          normativa_cliente: normativaCliente,
        },
        cuestionario_auditoria: qa,
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
      setPriorFinancialsSelectedFiles([]);
      setPriorControlSelectedFile(null);
      setSuccess("Fuentes guardadas. SocioAI está preparando el perfil de la entidad.");
      router.push(`/entity-profile/${clienteId}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "No se pudo guardar el onboarding.";
      setSaveError(message);
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

  if (loadError) {
    return (
      <div className="min-h-screen bg-[#f7fafc]">
        <nav className="fixed top-0 w-full z-40 bg-white border-b border-black/5 px-6 md:px-10 py-4 flex items-center justify-between">
          <div>
            <h1 className="font-headline text-3xl text-[#041627]">Onboarding de Cliente</h1>
            <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500">{clienteId}</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => router.push("/clientes")}
              className="sovereign-card !p-2 !px-3 text-[11px] uppercase tracking-[0.14em] text-slate-500"
            >
              Volver a clientes
            </button>
          </div>
        </nav>
        <main className="pt-28 px-6 md:px-10 pb-12 max-w-[1440px] mx-auto">
          <section role="alert" aria-live="assertive" className="sovereign-card max-w-2xl">
            <p className="text-xs uppercase tracking-[0.14em] text-red-700 font-bold">Error de carga</p>
            <h2 className="mt-2 font-headline text-3xl text-[#041627]">No se pudo cargar el onboarding.</h2>
            <p className="mt-3 text-sm text-slate-700">{loadError}</p>
            <div className="mt-6 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={retryLoad}
                className="rounded-xl bg-[#041627] px-4 py-2 text-sm font-semibold text-white hover:opacity-90"
              >
                Reintentar
              </button>
            </div>
          </section>
        </main>
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
  const tbCargado = Boolean(tbFile.trim());
  const mayorCargado = Boolean(mayorFile.trim());
  const informeAnteriorCargado = Boolean(priorFinancialsFile.trim());
  const faseDefinida = Boolean(scopeFinancials && visitPlan && periodStart && periodEnd && tbCutoffDate);

  const checklist = [
    { label: "Datos de cliente", ok: perfilCompleto },
    { label: "Configuración del encargo", ok: faseDefinida },
    { label: "Trial Balance", ok: tbCargado },
    { label: "Libro Mayor", ok: mayorCargado },
    { label: "Estados financieros anteriores (recomendado)", ok: informeAnteriorCargado },
    { label: "Fechas y visitas", ok: faseDefinida },
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
        {saveError ? <div role="alert" aria-live="polite" className="sovereign-card text-sm text-[#93000a] bg-[#ffdad6] border border-[#ba1a1a]/20">{saveError}</div> : null}
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
              <h2 className="font-headline text-3xl text-[#041627] mb-2">2. Configuración del encargo</h2>
              <p className="mb-6 text-sm text-slate-600">Estas preguntas ubican a SocioAI en el periodo y corte correctos. El conocimiento del negocio se completa después mediante preguntas adaptativas.</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <label className="md:col-span-2 flex flex-col gap-2 mb-2">
                  <span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Fase actual de auditoría</span>
                  <select className="ghost-input" value={faseAuditoria} onChange={(e) => setFaseAuditoria(e.target.value)}>
                    <option value="planificacion">Planificación</option>
                    <option value="preliminar">Visita preliminar</option>
                    <option value="final">Visita final</option>
                    <option value="cierre">Cierre e informe</option>
                  </select>
                </label>
                <label className="flex flex-col gap-2"><span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Estados a auditar</span><select className="ghost-input" value={scopeFinancials} onChange={(e) => setScopeFinancials(e.target.value)}><option value="individual">Individuales</option><option value="separate">Separados</option><option value="consolidated">Consolidados</option><option value="combined">Combinados</option><option value="undetermined">Aún no determinado</option></select></label>
                <label className="flex flex-col gap-2"><span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Esquema de visitas</span><select className="ghost-input" value={visitPlan} onChange={(e) => setVisitPlan(e.target.value)}><option value="single">Una sola visita</option><option value="preliminar_final">Preliminar y final</option><option value="custom">Varias visitas personalizadas</option><option value="undetermined">Aún no definido</option></select></label>
                <label className="flex flex-col gap-2"><span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Inicio del periodo</span><input type="date" className="ghost-input" value={periodStart} onChange={(e) => setPeriodStart(e.target.value)} /></label>
                <label className="flex flex-col gap-2"><span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Cierre del periodo</span><input type="date" className="ghost-input" value={periodEnd} onChange={(e) => setPeriodEnd(e.target.value)} /></label>
                <label className="flex flex-col gap-2"><span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Corte del balance cargado</span><input type="date" className="ghost-input" value={tbCutoffDate} onChange={(e) => setTbCutoffDate(e.target.value)} /></label>
                {visitPlan === "preliminar_final" ? <label className="flex flex-col gap-2"><span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">Visita preliminar</span><input type="date" className="ghost-input" value={preliminaryDate} onChange={(e) => setPreliminaryDate(e.target.value)} /></label> : null}
                <label className="flex flex-col gap-2"><span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">{visitPlan === "single" ? "Fecha de visita" : "Visita final"}</span><input type="date" className="ghost-input" value={finalDate} onChange={(e) => setFinalDate(e.target.value)} /></label>
                {scopeFinancials === "consolidated" ? <div className="md:col-span-2 rounded-xl border border-[#177e82]/25 bg-[#edfafa] p-4 text-sm text-[#155e63]">SocioAI abrirá preguntas específicas sobre controladora, componentes, eliminaciones y otros auditores en la segunda ronda.</div> : null}
              </div>
            </div>

            <div className="sovereign-card">
              <h2 className="font-headline text-3xl text-[#041627] mb-2">3. Fuentes para entender la entidad</h2>
              <p className="text-sm text-slate-600 mb-6">
                El balance actual es la base del análisis. Los documentos anteriores ayudan a SocioAI a comprender el negocio, sus políticas y antecedentes.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <label className="rounded-xl border-2 border-dashed border-black/15 p-5 bg-[#f8fafc]">
                  <p className="text-sm font-semibold text-[#041627]">Balance de comprobación preliminar</p>
                  <p className="text-xs text-slate-500 mt-1">Periodo actual · requerido · CSV/XLSX</p>
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
                  {tbSelectedFile ? <button type="button" onClick={() => { setTbSelectedFile(null); setTbFile(""); }} className="mt-2 text-xs font-semibold text-red-700">Quitar selección</button> : null}
                </label>

                <label className="rounded-xl border-2 border-dashed border-black/15 p-5 bg-[#f8fafc]">
                  <p className="text-sm font-semibold text-[#041627]">Libro Mayor</p>
                  <p className="text-xs text-slate-500 mt-1">Periodo actual · opcional · CSV/XLSX</p>
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
                  {mayorSelectedFile ? <button type="button" onClick={() => { setMayorSelectedFile(null); setMayorFile(""); }} className="mt-2 text-xs font-semibold text-red-700">Quitar selección</button> : null}
                </label>

                <label className="rounded-xl border-2 border-dashed border-[#89d3d4]/60 p-5 bg-[#f4fbfb]">
                  <p className="text-sm font-semibold text-[#041627]">Estados financieros auditados anteriores</p>
                  <p className="text-xs text-slate-500 mt-1">Opinión, estados y notas · recomendado · PDF/DOCX/XLSX</p>
                  <input
                    type="file" multiple
                    className="mt-4 text-sm"
                    onChange={(e) => {
                      const files = Array.from(e.target.files ?? []);
                      setPriorFinancialsSelectedFiles(files);
                      setPriorFinancialsFile(files.map((file) => file.name).join(", ") || priorFinancialsFile);
                    }}
                    accept=".pdf,.docx,.xlsx,.txt,.md,.csv"
                  />
                  {priorFinancialsFile ? <p className="text-xs text-slate-600 mt-2">Archivo: {priorFinancialsFile}</p> : null}
                  {priorFinancialsSelectedFiles.length ? <button type="button" onClick={() => { setPriorFinancialsSelectedFiles([]); setPriorFinancialsFile(""); }} className="mt-2 text-xs font-semibold text-red-700">Quitar {priorFinancialsSelectedFiles.length} archivo(s)</button> : null}
                </label>

                <label className="rounded-xl border-2 border-dashed border-black/15 p-5 bg-[#f8fafc]">
                  <p className="text-sm font-semibold text-[#041627]">Control interno o carta a la gerencia</p>
                  <p className="text-xs text-slate-500 mt-1">Periodo anterior · opcional · PDF/DOCX</p>
                  <input
                    type="file"
                    className="mt-4 text-sm"
                    onChange={(e) => {
                      const file = e.target.files?.[0] ?? null;
                      setPriorControlSelectedFile(file);
                      setPriorControlFile(file?.name ?? priorControlFile);
                    }}
                    accept=".pdf,.docx,.txt,.md"
                  />
                  {priorControlFile ? <p className="text-xs text-slate-600 mt-2">Archivo: {priorControlFile}</p> : null}
                  {priorControlSelectedFile ? <button type="button" onClick={() => { setPriorControlSelectedFile(null); setPriorControlFile(""); }} className="mt-2 text-xs font-semibold text-red-700">Quitar selección</button> : null}
                </label>
              </div>
              {contextDocuments.length ? <div className="mt-6 space-y-2"><p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-500">Archivos ya cargados</p>{contextDocuments.map((document) => <div key={document.id} className="flex flex-wrap items-center gap-3 rounded-xl border border-black/10 bg-white px-4 py-3 text-xs"><div className="min-w-0 flex-1"><p className="truncate font-semibold text-[#041627]">{document.name}</p><p className="text-slate-500">{document.document_role_label} · {document.ingestion?.extraction_method === "ocr" ? "Leído con OCR" : document.ingestion?.indexed ? "Texto extraído" : "Lectura pendiente"}{document.ingestion?.page_count ? ` · ${document.ingestion.pages_with_text ?? 0}/${document.ingestion.page_count} páginas` : ""}</p></div><button type="button" onClick={async () => { await reprocessClienteDocumento(clienteId, document.id); setContextDocuments(await getClienteDocumentos(clienteId)); }} className="font-semibold text-[#177e82]">Reprocesar</button><button type="button" onClick={async () => { await deleteClienteDocumento(clienteId, document.id); setContextDocuments((items) => items.filter((item) => item.id !== document.id)); }} className="font-semibold text-red-700">Eliminar</button></div>)}</div> : null}
            </div>
          </article>

          <aside className="xl:col-span-4 space-y-6">
            <div className="rounded-editorial p-7 text-white" style={{ background: "linear-gradient(135deg, #041627 0%, #1a2b3c 100%)" }}>
              <p className="text-xs uppercase tracking-[0.16em] text-[#89d3d4]">Socio AI</p>
              <h3 className="font-headline text-3xl mt-3">Motor listo para iniciar</h3>
              <p className="text-sm text-slate-200 mt-3 leading-relaxed">
                Cargamos las fuentes y luego te mostramos, de forma transparente, qué entendió SocioAI y qué necesita que confirmes.
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
                onClick={() => void handleSave()}
                disabled={saving}
                className="w-full py-3 rounded-xl border border-black/10 bg-white text-slate-700 font-semibold disabled:opacity-60"
              >
                {saving ? "Analizando fuentes..." : "Guardar y crear perfil de la entidad"}
              </button>
            </div>
          </aside>
        </section>
      </main>
    </div>
  );
}

