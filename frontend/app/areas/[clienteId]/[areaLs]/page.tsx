"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import LeadSchedule from "../../../../components/areas/LeadSchedule";
import DashboardSkeleton from "../../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../../components/dashboard/ErrorMessage";
import ContextualHelp from "../../../../components/help/ContextualHelp";
import { patchAreaCheck } from "../../../../lib/api/areas";
import { postAreaBriefing } from "../../../../lib/api/briefing";
import { postBriefingTiempo, postEstructurarHallazgo } from "../../../../lib/api/hallazgos";
import { getAreaProcedures, type AreaProcedureDetail } from "../../../../lib/api/procedimientos";
import { useAreaDetail } from "../../../../lib/hooks/useAreaDetail";
import { useLearningRole } from "../../../../lib/hooks/useLearningRole";
import { getLsName, getLsOptions, getLsShortName } from "../../../../lib/lsCatalog";
import type { AreaCuenta } from "../../../../types/area";

type Params = {
  clienteId?: string | string[];
  areaLs?: string | string[];
};

function badgeTone(value: string): string {
  const v = value.toLowerCase();
  if (v.includes("alto")) return "bg-red-50 text-red-700";
  if (v.includes("medio")) return "bg-amber-50 text-amber-700";
  return "bg-emerald-50 text-emerald-700";
}

function isHighRisk(status: string, aseveraciones: { riesgo_tipico: string }[]): boolean {
  if (status.toLowerCase().includes("alto")) return true;
  return aseveraciones.some((a) => a.riesgo_tipico.toLowerCase().includes("alto"));
}

export default function AreaWorkspacePage() {
  const router = useRouter();
  const params = useParams<Params>();
  const clienteId = useMemo(() => {
    const raw = params?.clienteId;
    return Array.isArray(raw) ? raw[0] : raw ?? "";
  }, [params]);
  const areaCode = useMemo(() => {
    const raw = params?.areaLs;
    return Array.isArray(raw) ? raw[0] : raw ?? "";
  }, [params]);

  const { data, isLoading, error } = useAreaDetail(clienteId, areaCode);
  const { role } = useLearningRole();
  const [cuentas, setCuentas] = useState<AreaCuenta[]>([]);
  const [briefing, setBriefing] = useState<string>("");
  const [briefingLoading, setBriefingLoading] = useState<boolean>(false);
  const [briefingError, setBriefingError] = useState<string>("");
  const [normasActivadas, setNormasActivadas] = useState<string[]>([]);
  const [chunksUsados, setChunksUsados] = useState<Array<{ norma: string; fuente: string; excerpt: string }>>([]);
  const [selectedNorma, setSelectedNorma] = useState<string>("");
  const [condicionHallazgo, setCondicionHallazgo] = useState<string>("");
  const [hallazgoGenerado, setHallazgoGenerado] = useState<string>("");
  const [hallazgoLoading, setHallazgoLoading] = useState<boolean>(false);
  const [hallazgoError, setHallazgoError] = useState<string>("");
  const [manualMinutes, setManualMinutes] = useState<string>("");
  const [tiempoManual, setTiempoManual] = useState<string>("");
  const [tiempoAI, setTiempoAI] = useState<string>("");
  const [logTiempoMsg, setLogTiempoMsg] = useState<string>("");
  const [proceduresDetail, setProceduresDetail] = useState<AreaProcedureDetail | null>(null);
  const [proceduresLoading, setProceduresLoading] = useState<boolean>(false);
  const [proceduresError, setProceduresError] = useState<string>("");
  const areaNavOptions = useMemo(() => {
    const opts = getLsOptions();
    if (!areaCode) return opts;
    if (opts.some((x) => x.codigo === areaCode)) return opts;
    return [{ codigo: areaCode, nombre: getLsName(areaCode) }, ...opts];
  }, [areaCode]);

  useEffect(() => {
    setCuentas(data?.cuentas ?? []);
  }, [data]);

  useEffect(() => {
    if (!areaCode) return;
    let active = true;
    const run = async () => {
      setProceduresLoading(true);
      setProceduresError("");
      try {
        const payload = await getAreaProcedures(areaCode);
        if (!active) return;
        setProceduresDetail(payload);
      } catch (error: unknown) {
        if (!active) return;
        setProceduresError(error instanceof Error ? error.message : "No se pudieron cargar los procedimientos del area.");
        setProceduresDetail(null);
      } finally {
        if (active) setProceduresLoading(false);
      }
    };
    void run();
    return () => {
      active = false;
    };
  }, [areaCode]);

  async function handleToggleCheck(codigo: string, checked: boolean): Promise<void> {
    setCuentas((prev) => prev.map((c) => (c.codigo === codigo ? { ...c, checked } : c)));
    try {
      await patchAreaCheck(clienteId, areaCode, codigo, checked);
    } catch {
      setCuentas((prev) => prev.map((c) => (c.codigo === codigo ? { ...c, checked: !checked } : c)));
    }
  }

  function normalizeRisk(status: string): string {
    const s = (status || "").toLowerCase();
    if (s.includes("alto")) return "alto";
    if (s.includes("bajo")) return "bajo";
    return "medio";
  }

  function normalizeMarco(value: string): string {
    const v = (value || "").toLowerCase();
    if (v.includes("pymes")) return "niif_pymes";
    if (v.includes("completa")) return "niif_completas";
    if (v.includes("full")) return "niif_completas";
    return "niif_pymes";
  }

  function normalizeAfirmacion(value: string): string {
    const v = (value || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    if (v.includes("exist")) return "existencia";
    if (v.includes("integ")) return "integridad";
    if (v.includes("valu")) return "valuacion";
    if (v.includes("cort")) return "corte";
    if (v.includes("ocurr")) return "ocurrencia";
    if (v.includes("present")) return "presentacion";
    return v || "integridad";
  }

  async function handleGenerateBriefing(): Promise<void> {
    if (!clienteId || !data) return;
    setBriefingLoading(true);
    setBriefingError("");
    try {
      const ctx = data.briefing_context;
      const payload = {
        cliente_id: clienteId,
        area_codigo: ctx.area_codigo || data.encabezado.area_code,
        area_nombre: ctx.area_nombre || data.encabezado.nombre,
        marco: normalizeMarco(ctx.marco || "niif_pymes"),
        riesgo: normalizeRisk(ctx.riesgo || data.encabezado.estatus),
        afirmaciones_criticas: (ctx.afirmaciones_criticas.length > 0
          ? ctx.afirmaciones_criticas.map((a) => normalizeAfirmacion(a))
          : data.aseveraciones.slice(0, 3).map((a) => normalizeAfirmacion(a.nombre))),
        materialidad: Number(ctx.materialidad || 0),
        patrones_historicos: ctx.patrones_historicos,
        hallazgos_previos: ctx.hallazgos_previos,
        etapa: String(ctx.etapa || "ejecucion"),
      };

      const response = await postAreaBriefing(payload);
      setBriefing(response.briefing || "");
      setNormasActivadas(Array.isArray(response.normas_activadas) ? response.normas_activadas : []);
      setChunksUsados(Array.isArray(response.chunks_usados) ? response.chunks_usados : []);
      setSelectedNorma("");
    } catch (err: unknown) {
      setBriefingError(err instanceof Error ? err.message : "No se pudo generar el briefing.");
    } finally {
      setBriefingLoading(false);
    }
  }

  async function handleEstructurarHallazgo(): Promise<void> {
    if (!clienteId || !data || !condicionHallazgo.trim()) return;
    setHallazgoLoading(true);
    setHallazgoError("");
    try {
      const ctx = data.briefing_context;
      const response = await postEstructurarHallazgo({
        cliente_id: clienteId,
        area_codigo: ctx.area_codigo || data.encabezado.area_code,
        area_nombre: ctx.area_nombre || data.encabezado.nombre,
        marco: normalizeMarco(ctx.marco || "niif_pymes"),
        riesgo: normalizeRisk(ctx.riesgo || data.encabezado.estatus),
        afirmaciones_criticas: (ctx.afirmaciones_criticas.length > 0
          ? ctx.afirmaciones_criticas
          : ["integridad", "valuacion", "corte"]).map((x) => normalizeAfirmacion(x)),
        etapa: String(ctx.etapa || "ejecucion"),
        condicion_detectada: condicionHallazgo.trim(),
        guardar_en_hallazgos: false,
      });
      setHallazgoGenerado(response.hallazgo || "");
    } catch (err: unknown) {
      setHallazgoError(err instanceof Error ? err.message : "No se pudo estructurar el hallazgo.");
    } finally {
      setHallazgoLoading(false);
    }
  }

  async function handleGuardarTiempo(manualOverride?: number): Promise<void> {
    if (!clienteId || !data) return;
    const manual = typeof manualOverride === "number" ? manualOverride : Number(tiempoManual);
    const aiParsed = Number(tiempoAI);
    const ai = Number.isFinite(aiParsed) ? aiParsed : 0;
    if (!Number.isFinite(manual)) {
      setLogTiempoMsg("Ingresa tiempos validos en minutos.");
      return;
    }
    try {
      const res = await postBriefingTiempo({
        cliente_id: clienteId,
        area_codigo: data.encabezado.area_code,
        area_nombre: data.encabezado.nombre,
        tiempo_manual_min: manual,
        tiempo_ai_min: ai,
        notas: "registro desde vista de area activa",
      });
      setLogTiempoMsg(`Guardado. Ahorro: ${res.delta_min.toFixed(2)} min (${res.ahorro_pct.toFixed(1)}%).`);
    } catch (err: unknown) {
      setLogTiempoMsg(err instanceof Error ? err.message : "No se pudo guardar la metrica.");
    }
  }

  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorMessage message={error} />;
  if (!data) return <ErrorMessage message="No hay información para esta área." />;

  const highRisk = isHighRisk(data.encabezado.estatus, data.aseveraciones);
  const checkedCount = cuentas.filter((c) => c.checked).length;
  const pendingCount = Math.max(cuentas.length - checkedCount, 0);
  const blockingCount = data.aseveraciones.filter((a) => a.riesgo_tipico.toLowerCase().includes("alto")).length;
  const areaProcedures = proceduresDetail?.procedimientos ?? [];
  const mandatoryProcedures = areaProcedures.filter((proc) => proc.obligatorio).slice(0, 5);
  const criticalAssertions = new Set(
    data.aseveraciones
      .filter((aseveracion) => aseveracion.riesgo_tipico.toLowerCase().includes("alto"))
      .map((aseveracion) => normalizeAfirmacion(aseveracion.nombre)),
  );
  const socioKeyProcedures = areaProcedures
    .filter((proc) => proc.obligatorio || criticalAssertions.has(normalizeAfirmacion(proc.afirmacion)))
    .slice(0, 6);

  return (
    <div className="space-y-8 pt-4 pb-8">
      <section className="flex flex-col xl:flex-row justify-between items-start gap-6">
        <div className="space-y-4">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`px-3 py-1 rounded text-[10px] font-bold tracking-[0.14em] uppercase ${highRisk ? "bg-[#ba1a1a] text-white" : "bg-emerald-100 text-emerald-700"}`}>
              {highRisk ? "Riesgo Alto" : "Riesgo Controlado"}
            </span>
            <span className={`px-3 py-1 rounded text-[10px] font-bold tracking-[0.14em] uppercase ${badgeTone(data.encabezado.estatus)}`}>
              {data.encabezado.estatus}
            </span>
          </div>
          <div>
            <p className="font-body text-xs uppercase tracking-[0.16em] text-slate-500">Workspace de Área</p>
            <h2 data-tour="area-title" className="font-headline text-5xl text-[#041627] mt-1 tracking-tight">
              {data.encabezado.area_code} - {data.encabezado.nombre}
            </h2>
            <p className="text-slate-500 mt-3 font-body text-sm">
              Ejercicio {data.encabezado.actual_year} · Responsable <b>{data.encabezado.responsable}</b>
            </p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-black/10 shadow-editorial flex gap-8">
          <div>
            <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">Checks</p>
            <p className="font-headline text-4xl text-[#041627] mt-2">{checkedCount}</p>
          </div>
          <div className="w-px bg-slate-200" />
          <div>
            <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">Pendientes</p>
            <p className="font-headline text-4xl text-[#ba1a1a] mt-2">{pendingCount}</p>
          </div>
        </div>
      </section>

      <section className="sovereign-card border border-[#041627]/10" aria-label="Navegación principal del área">
        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
          <div>
            <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold">Navegación rápida</p>
            <h3 className="font-headline text-2xl text-[#041627] mt-1">Cambiar de área y módulo sin salir del flujo</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => router.push(`/risk-engine/${clienteId}`)}
              className="px-3 py-2 rounded-lg border border-[#041627]/20 text-slate-700 text-xs font-semibold uppercase tracking-[0.08em] bg-white"
            >
              Risk Engine
            </button>
            <button
              type="button"
              onClick={() => router.push(`/papeles-trabajo/${clienteId}`)}
              className="px-3 py-2 rounded-lg border border-[#041627]/20 text-slate-700 text-xs font-semibold uppercase tracking-[0.08em] bg-white"
            >
              Papeles
            </button>
          </div>
        </div>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-[1fr_auto] gap-3 items-center">
          <select
            value={areaCode}
            onChange={(e) => router.push(`/areas/${clienteId}/${e.target.value}`)}
            className="ghost-input w-full"
          >
            {areaNavOptions.map((item) => (
              <option key={item.codigo} value={item.codigo}>
                {getLsShortName(item.codigo)} · {item.codigo}
              </option>
            ))}
          </select>
          <p className="text-sm text-slate-600 md:text-right">
            Área activa: <span className="font-semibold text-[#041627]">{getLsName(areaCode)}</span>
          </p>
        </div>
      </section>

      {/* Panel de rol */}
      {role === "junior" && (
        <section className="bg-[#a5eff0]/10 border border-[#a5eff0]/30 rounded-xl p-6 space-y-4">
          <div className="flex items-center gap-3">
            <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#041627] text-[#a5eff0] text-xs font-bold">NIA</span>
            <div>
              <p className="text-xs uppercase tracking-[0.15em] text-[#041627]/60 font-bold">Guía de trabajo — Vista Junior</p>
              <p className="text-sm font-semibold text-[#041627]">{data.encabezado.area_code} — {data.encabezado.nombre}</p>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {[
              { num: 1, accion: "Revisa cada cuenta en el Lead Schedule", nia: "NIA 230", detalle: "Marca check solo cuando tengas soporte documental. Deja nota si hay diferencia con el año anterior." },
              { num: 2, accion: "Genera el Briefing del área", nia: "NIA 500", detalle: "El briefing te dice qué procedimiento aplicar primero y por qué, según las aseveraciones en riesgo." },
              { num: 3, accion: data.aseveraciones.length > 0 ? `Documenta ${data.aseveraciones[0]?.nombre ?? "aseveración clave"}` : "Documenta la aseveración principal", nia: "NIA 315", detalle: "Si encuentras desviación, usa el Estructurador de Hallazgo para redactarla correctamente." },
            ].map((step) => (
              <div key={step.nia} className="flex gap-3 p-4 bg-white rounded-lg border border-slate-100">
                <span className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#041627] text-white text-xs font-bold mt-0.5">{step.num}</span>
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <p className="font-semibold text-[#041627] text-sm">{step.accion}</p>
                    <span className="shrink-0 px-2 py-0.5 rounded-full bg-[#041627]/10 text-[#041627] text-[10px] font-bold uppercase">{step.nia}</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1 leading-relaxed">{step.detalle}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {role === "socio" && (
        <section className="rounded-xl p-6 bg-[#001919] border border-[#a5eff0]/20 shadow-md text-white">
          <p className="text-[10px] uppercase tracking-[0.2em] text-[#a5eff0] font-bold mb-3">Resumen Ejecutivo — Vista Socio</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white/10 rounded-lg p-4">
              <p className="text-[10px] uppercase tracking-[0.12em] text-slate-300">Estado</p>
              <p className={`font-headline text-xl mt-1 font-semibold ${highRisk ? "text-rose-400" : "text-emerald-400"}`}>
                {highRisk ? "Requiere acción" : "Lista para cierre"}
              </p>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <p className="text-[10px] uppercase tracking-[0.12em] text-slate-300">Aseveraciones</p>
              <p className="font-headline text-xl mt-1 font-semibold text-white">{data.aseveraciones.length}</p>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <p className="text-[10px] uppercase tracking-[0.12em] text-slate-300">Pendientes</p>
              <p className={`font-headline text-xl mt-1 font-semibold ${pendingCount > 0 ? "text-amber-400" : "text-emerald-400"}`}>{pendingCount}</p>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <p className="text-[10px] uppercase tracking-[0.12em] text-slate-300">Alto riesgo</p>
              <p className={`font-headline text-xl mt-1 font-semibold ${blockingCount > 0 ? "text-rose-400" : "text-emerald-400"}`}>{blockingCount}</p>
            </div>
          </div>
          {data.aseveraciones.filter((a) => a.riesgo_tipico.toLowerCase().includes("alto")).length > 0 && (
            <div className="mt-4 pt-4 border-t border-white/10">
              <p className="text-xs text-slate-300 mb-2">Aseveraciones de alto riesgo que requieren evidencia suficiente:</p>
              <div className="flex flex-wrap gap-2">
                {data.aseveraciones.filter((a) => a.riesgo_tipico.toLowerCase().includes("alto")).map((a, i) => (
                  <span key={`${a.nombre}-${i}`} className="px-3 py-1 rounded-full bg-rose-900/60 text-rose-200 text-xs font-semibold border border-rose-700/50">{a.nombre}</span>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      <section className="sovereign-card space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold">Procedimientos por área</p>
            <h3 className="font-headline text-2xl text-[#041627] mt-1">
              {role === "socio" ? "Riesgo critico → procedimientos clave" : "Panel operativo de procedimientos"}
            </h3>
          </div>
          <button
            type="button"
            onClick={() => router.push("/procedimientos")}
            className="rounded-lg border border-[#041627]/20 px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-[#041627]"
          >
            Ver biblioteca completa
          </button>
        </div>

        {proceduresLoading ? <p className="text-sm text-slate-500">Cargando procedimientos del area...</p> : null}
        {proceduresError ? <p className="text-sm text-rose-700">{proceduresError}</p> : null}

        {!proceduresLoading && !proceduresError ? (
          role === "junior" ? (
            mandatoryProcedures.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {mandatoryProcedures.map((proc) => (
                  <article key={proc.id} className="rounded-lg border border-rose-200 bg-rose-50 p-4">
                    <p className="text-[11px] uppercase tracking-[0.1em] text-rose-700 font-bold">{proc.id}</p>
                    <p className="font-semibold text-[#041627] mt-1">{proc.descripcion}</p>
                    <p className="text-xs text-slate-600 mt-2">{proc.afirmacion} · {proc.nia_ref}</p>
                  </article>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-600">No hay procedimientos obligatorios definidos para esta area.</p>
            )
          ) : role === "socio" ? (
            socioKeyProcedures.length > 0 ? (
              <div className="space-y-2">
                {socioKeyProcedures.map((proc) => (
                  <article key={proc.id} className="rounded-lg border border-[#041627]/15 bg-[#f1f4f6] p-4">
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-semibold text-[#041627]">{proc.id} · {proc.descripcion}</p>
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${proc.obligatorio ? "bg-rose-100 text-rose-700" : "bg-slate-200 text-slate-700"}`}>
                        {proc.obligatorio ? "Clave" : "Complementario"}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 mt-1">{proc.afirmacion} · {proc.tipo} · {proc.nia_ref}</p>
                  </article>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-600">No hay procedimientos priorizados para esta area.</p>
            )
          ) : areaProcedures.length > 0 ? (
            <div className="space-y-2">
              {areaProcedures.slice(0, 8).map((proc) => (
                <article key={proc.id} className="rounded-lg border border-black/10 bg-white p-4">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-semibold text-[#041627]">{proc.id} · {proc.descripcion}</p>
                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${proc.obligatorio ? "bg-rose-100 text-rose-700" : "bg-slate-100 text-slate-700"}`}>
                      {proc.obligatorio ? "Obligatorio" : "Opcional"}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 mt-1">{proc.afirmacion} · {proc.tipo} · {proc.nia_ref}</p>
                </article>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-600">No hay procedimientos definidos para esta area en el catalogo.</p>
          )
        ) : null}
      </section>

      <section className={`rounded-[2rem] p-1 shadow-editorial ${highRisk ? "bg-gradient-to-br from-[#ba1a1a] to-[#93000a]" : "bg-gradient-to-br from-[#041627] to-[#1a2b3c]"}`}>
        <div className={`rounded-[1.9rem] p-8 border ${highRisk ? "bg-[#ba1a1a] border-white/10" : "bg-[#1a2b3c] border-white/10"} text-white`}>
          <div className="flex flex-col xl:flex-row xl:items-center xl:justify-between gap-6">
            <div className="flex items-start gap-5">
              <div className="bg-white/10 p-4 rounded-2xl border border-white/20">
                <span
                  className={`inline-flex h-12 w-12 items-center justify-center rounded-full text-2xl font-bold ${
                    highRisk ? "bg-red-700 text-white" : "bg-emerald-700 text-white"
                  }`}
                  aria-hidden="true"
                >
                  {highRisk ? "!" : "✓"}
                </span>
              </div>
              <div>
                <h3 className="font-headline text-4xl leading-tight">
                  {highRisk ? "Estado: No lista para cierre" : "Estado: Lista para cierre técnico"}
                </h3>
                <p className="font-headline italic text-lg text-slate-200 mt-3 max-w-3xl leading-relaxed">
                  {highRisk
                    ? "El área requiere procedimientos adicionales antes de emitir criterio final. Se observan alertas abiertas en aseveraciones clave."
                    : "El área mantiene consistencia en saldos y procedimientos, con pendientes menores de documentación."}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 min-w-[220px]">
              <div className="bg-black/20 px-4 py-3 rounded-xl border border-white/10 flex items-center justify-between">
                <span className="text-xs uppercase tracking-[0.12em] text-slate-200 font-bold">Hallazgos</span>
                <span className="text-xl font-bold">{blockingCount}</span>
              </div>
              <div className="bg-black/20 px-4 py-3 rounded-xl border border-white/10 flex items-center justify-between">
                <span className="text-xs uppercase tracking-[0.12em] text-slate-200 font-bold">Pendientes</span>
                <span className="text-xl font-bold">{pendingCount}</span>
              </div>
            </div>
          </div>

          <div className="mt-7 pt-6 border-t border-white/10">
            <h4 className="text-xs font-bold tracking-[0.2em] uppercase mb-4 flex items-center">
              <span className="inline-flex h-4 w-4 items-center justify-center rounded-full bg-white/20 text-white text-[10px] mr-2">•</span>
              Acciones requeridas para cierre
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {(data.aseveraciones.length > 0
                ? data.aseveraciones.slice(0, 3).map((a) => a.procedimiento_clave || `Completar prueba de ${a.nombre}`)
                : ["Completar revisión de soportes", "Actualizar papeles de trabajo", "Documentar conclusión del área"]
              ).map((task) => (
                <div key={task} className="bg-white/5 border border-white/10 rounded-xl p-4 flex items-center gap-3">
                  <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-white/15 text-white text-xs">✓</span>
                  <span className="text-sm text-white">{task}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
        <section data-tour="area-lead-schedule" className="xl:col-span-8 space-y-8">
          <ContextualHelp
            title="Ayuda del modulo Workspace Areas"
            items={[
              {
                label: "Lead Schedule",
                byRole: {
                  junior:
                    "Revisa cuenta por cuenta, marca checks solo cuando tengas evidencia y deja nota breve de soporte.",
                  semi:
                    "Valida saldos, variaciones y checkea cada cuenta con evidencia suficiente para conclusion del area.",
                  senior:
                    "Confirma que el lead schedule soporte la conclusion tecnica y que la evidencia sea trazable.",
                  socio:
                    "Verifica que el soporte del area sea suficiente para sostener conclusion y eventual opinion.",
                },
              },
              {
                label: "Briefing",
                byRole: {
                  junior:
                    "Usalo como guia practica: te dice que procedimiento ejecutar primero y por que.",
                  semi:
                    "Genera recomendaciones concretas de procedimientos con normativa activada para la area.",
                  senior:
                    "Verifica que el briefing este alineado al riesgo y materialidad asignada.",
                  socio:
                    "Usa el briefing para validar si el equipo cubre riesgos de negocio y de reporte financiero.",
                },
              },
              {
                label: "Hallazgo y tiempo",
                byRole: {
                  junior:
                    "Si encuentras desviacion, estructura el hallazgo y registra tiempo para medir mejora personal.",
                  semi:
                    "Estructura hallazgos con criterio y mide ahorro real manual vs AI.",
                  senior:
                    "Controla calidad del hallazgo (criterio-efecto-recomendacion) y productividad del equipo.",
                  socio:
                    "Evalua impacto material, respuesta de gerencia y efecto en comunicacion final.",
                },
              },
            ]}
          />
          <LeadSchedule
            cuentas={cuentas}
            currentYear={data.encabezado.actual_year}
            previousYear={data.encabezado.anterior_year}
            title={`${data.encabezado.area_code} - ${data.encabezado.nombre}`}
            onToggleCheck={handleToggleCheck}
          />
        </section>

        <section className="xl:col-span-4 space-y-6">
          <article className="sovereign-card">
            <h3 className="font-headline text-2xl text-[#041627] mb-4">Aseveraciones vinculadas</h3>
            <div className="space-y-3">
              {data.aseveraciones.map((a, idx) => (
                <article key={`${a.nombre}-${idx}`} className="bg-[#f1f4f6] rounded-editorial p-4">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-headline text-xl text-[#041627]">{a.nombre}</p>
                    <span className={`text-[10px] px-2 py-1 rounded uppercase tracking-[0.1em] font-bold ${badgeTone(a.riesgo_tipico)}`}>{a.riesgo_tipico}</span>
                  </div>
                  <p className="font-body text-sm text-slate-600 mt-2 leading-relaxed">{a.descripcion}</p>
                </article>
              ))}
            </div>
          </article>

          <article className="sovereign-card">
            <div className="flex items-center justify-between gap-3 mb-4">
              <h4 className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">Briefing de Área</h4>
              <button
                type="button"
                onClick={handleGenerateBriefing}
                disabled={briefingLoading}
                data-tour="btn-generar-briefing"
                className="px-3 py-2 rounded-lg bg-[#041627] text-white text-xs font-bold tracking-[0.08em] uppercase disabled:opacity-60"
              >
                {briefingLoading ? "Generando..." : "Generar Briefing"}
              </button>
            </div>
            {briefingError ? <p className="text-sm text-red-700">{briefingError}</p> : null}
            {briefing ? (
              <div className="space-y-4">
                <pre className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700 font-body bg-[#f7f8fa] p-4 rounded-xl border border-black/5">
                  {briefing}
                </pre>
                {normasActivadas.length > 0 ? (
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.16em] text-slate-500 font-bold mb-2">Normas activadas</p>
                    <div className="flex flex-wrap gap-2">
                      {normasActivadas.map((norma) => (
                        <button
                          key={norma}
                          type="button"
                          onClick={() => setSelectedNorma((prev) => (prev === norma ? "" : norma))}
                          className={`px-2 py-1 rounded text-[11px] border ${
                            selectedNorma === norma
                              ? "bg-[#041627] text-white border-[#041627]"
                              : "bg-white text-slate-700 border-slate-300"
                          }`}
                        >
                          {norma}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : null}
                <div>
                  <p className="text-[10px] uppercase tracking-[0.16em] text-slate-500 font-bold mb-2">
                    Chunks usados ({chunksUsados.length})
                  </p>
                  <div className="space-y-2 max-h-64 overflow-auto pr-1">
                    {chunksUsados
                      .filter((c) => !selectedNorma || c.norma === selectedNorma)
                      .map((chunk, idx) => (
                        <article key={`${chunk.fuente}-${idx}`} className="rounded-lg border border-black/10 bg-white p-3">
                          <p className="text-xs font-bold text-[#041627]">{chunk.norma}</p>
                          <p className="text-[11px] text-slate-500 mt-1">{chunk.fuente}</p>
                          <p className="text-xs text-slate-700 mt-2 line-clamp-4">{chunk.excerpt}</p>
                        </article>
                      ))}
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-500">Genera el briefing para ver normativa activada y chunks de soporte.</p>
            )}
          </article>

          <article data-tour="hallazgo-block" className="sovereign-card space-y-3">
            <h4 className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">Estructurador de Hallazgo</h4>
            <textarea
              value={condicionHallazgo}
              onChange={(e) => setCondicionHallazgo(e.target.value)}
              placeholder="Describe la condicion detectada (hecho observado)"
              className="ghost-input min-h-24 w-full"
            />
            <button
              type="button"
              onClick={handleEstructurarHallazgo}
              disabled={hallazgoLoading || !condicionHallazgo.trim()}
              className="px-3 py-2 rounded-lg bg-[#041627] text-white text-xs font-bold tracking-[0.08em] uppercase disabled:opacity-60"
            >
              {hallazgoLoading ? "Estructurando..." : "Estructurar Hallazgo"}
            </button>
            {hallazgoError ? <p className="text-sm text-red-700">{hallazgoError}</p> : null}
            {hallazgoGenerado ? (
              <pre className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700 font-body bg-[#f7f8fa] p-4 rounded-xl border border-black/5">
                {hallazgoGenerado}
              </pre>
            ) : null}
          </article>

          {role !== "socio" && <article data-tour="tiempo-block" className="sovereign-card space-y-3">
            <h4 className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">Medicion de Tiempo (Real)</h4>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min="0"
                value={manualMinutes}
                onChange={(e) => setManualMinutes(e.target.value)}
                placeholder="Minutos manuales"
                className="w-36 rounded-lg border border-[#041627]/15 bg-[#f1f4f6] px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-[#89d3d4] focus:outline-none"
              />
              <button
                type="button"
                onClick={() => {
                  const mins = parseInt(manualMinutes, 10);
                  if (!isNaN(mins) && mins >= 0) {
                    void handleGuardarTiempo(mins);
                    setTiempoManual(String(mins));
                    setManualMinutes("");
                  }
                }}
                className="rounded-full bg-[#041627] px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-white hover:opacity-90"
              >
                Registrar
              </button>
            </div>
            <input
              type="number"
              step="0.1"
              value={tiempoAI}
              onChange={(e) => setTiempoAI(e.target.value)}
              placeholder="Con AI (min)"
              className="ghost-input"
            />
            <button
              type="button"
              onClick={() => void handleGuardarTiempo()}
              className="px-3 py-2 rounded-lg border border-slate-300 text-xs font-bold tracking-[0.08em] uppercase"
            >
              Guardar Medicion
            </button>
            {logTiempoMsg ? <p className="text-xs text-slate-700">{logTiempoMsg}</p> : null}
          </article>}
        </section>
      </div>
    </div>
  );
}
