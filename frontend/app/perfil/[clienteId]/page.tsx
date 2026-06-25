"use client";

import { ChangeEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import ContextualHelp from "../../../components/help/ContextualHelp";
import QuestionHelp from "../../../components/ui/QuestionHelp";
import { getPerfil, savePerfil } from "../../../lib/api/perfil";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import type { PerfilFormData, PerfilPayload } from "../../../types/perfil";

function asRecord(value: unknown): Record<string, unknown> {
  return typeof value === "object" && value !== null ? (value as Record<string, unknown>) : {};
}

function asString(value: unknown, fallback = ""): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function toNumberInput(value: unknown): string {
  const parsed = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(parsed) || parsed === 0) return "";
  return String(parsed);
}

function parseInputNumber(value: string): number {
  const normalized = String(value || "").trim().replace(",", ".");
  if (!normalized) return 0;
  const parsed = Number(normalized);
  return Number.isFinite(parsed) ? parsed : 0;
}

function deepClone<T>(value: T): T {
  if (typeof structuredClone === "function") return structuredClone(value);
  return JSON.parse(JSON.stringify(value)) as T;
}

function setNested(target: PerfilPayload, path: string[], value: unknown): void {
  let cursor: Record<string, unknown> = target;
  for (let i = 0; i < path.length - 1; i += 1) {
    const key = path[i];
    const current = cursor[key];
    if (typeof current !== "object" || current === null) cursor[key] = {};
    cursor = cursor[key] as Record<string, unknown>;
  }
  cursor[path[path.length - 1]] = value;
}

function toFormData(perfil: PerfilPayload): PerfilFormData {
  const encargo = asRecord(perfil.encargo);
  const materialidad = asRecord(perfil.materialidad);
  const preliminar = asRecord(materialidad.preliminar);
  const final = asRecord(materialidad.final);
  const riesgoGlobal = asRecord(perfil.riesgo_global);

  return {
    firma_auditoria: asString(encargo.firma_auditora, "Socio AI"),
    auditor_encargado: asString(encargo.encargado_asignado, asString(encargo.socio_asignado, "")),
    fiscal_year: String(encargo.anio_activo ?? "2025"),
    riesgo_global: asString(riesgoGlobal.nivel, "MEDIO").toUpperCase(),
    socio_responsable: asString(encargo.socio_asignado, ""),
    gerente_responsable: asString(encargo.gerente_asignado, ""),
    senior_responsable: asString(encargo.senior_asignado, ""),
    semi_responsable: asString(encargo.semi_asignado, ""),
    junior_responsable: asString(encargo.junior_asignado, ""),
    revisor_tecnico: asString(encargo.revisor_tecnico, ""),
    especialista_externo: asString(encargo.especialista_externo, ""),
    fecha_inicio_encargo: asString(encargo.fecha_inicio, ""),
    fecha_objetivo_entrega: asString(encargo.fecha_objetivo, ""),
    estado_encargo: asString(encargo.estado_encargo, asString(encargo.fase_actual, "planeacion")),
    nivel_supervision: asString(encargo.nivel_supervision, "medio"),
    complejidad_encargo: asString(encargo.complejidad_encargo, "media"),
    observaciones_operativas: asString(encargo.observaciones_operativas, ""),
    materialidad_preliminar: toNumberInput(preliminar.materialidad_global),
    materialidad_preliminar_proyectada: toNumberInput(preliminar.materialidad_desempeno),
    materialidad_preliminar_trivial: toNumberInput(preliminar.error_trivial),
    materialidad_final_planeacion: toNumberInput(final.materialidad_planeacion),
    materialidad_final_ejecucion: toNumberInput(final.materialidad_ejecucion),
    umbral_trivialidad_final: toNumberInput(final.umbral_trivialidad),
    materialidad_base_usada: asString(preliminar.base_usada, asString(final.base_usada, "Ingresos")),
    materialidad_area_referencia: asString(preliminar.area_referencia, asString(final.area_referencia, "")),
    materialidad_justificacion_nia: asString(
      preliminar.justificacion_nia,
      asString(final.justificacion_nia, "NIA 320: base y porcentaje definidos por juicio profesional del encargo."),
    ),
    comentario_materialidad: asString(preliminar.comentario_base, "Calculado segun la base de materialidad del encargo."),
  };
}

function toPerfilPayload(base: PerfilPayload, form: PerfilFormData): PerfilPayload {
  const next = deepClone(base);

  setNested(next, ["encargo", "firma_auditora"], form.firma_auditoria);
  setNested(next, ["encargo", "encargado_asignado"], form.auditor_encargado);
  setNested(next, ["encargo", "anio_activo"], Number(form.fiscal_year));
  setNested(next, ["encargo", "socio_asignado"], form.socio_responsable);
  setNested(next, ["encargo", "gerente_asignado"], form.gerente_responsable);
  setNested(next, ["encargo", "senior_asignado"], form.senior_responsable);
  setNested(next, ["encargo", "semi_asignado"], form.semi_responsable);
  setNested(next, ["encargo", "junior_asignado"], form.junior_responsable);
  setNested(next, ["encargo", "revisor_tecnico"], form.revisor_tecnico);
  setNested(next, ["encargo", "especialista_externo"], form.especialista_externo);
  setNested(next, ["encargo", "fecha_inicio"], form.fecha_inicio_encargo);
  setNested(next, ["encargo", "fecha_objetivo"], form.fecha_objetivo_entrega);
  setNested(next, ["encargo", "estado_encargo"], form.estado_encargo);
  setNested(next, ["encargo", "fase_actual"], form.estado_encargo);
  setNested(next, ["encargo", "nivel_supervision"], form.nivel_supervision);
  setNested(next, ["encargo", "complejidad_encargo"], form.complejidad_encargo);
  setNested(next, ["encargo", "observaciones_operativas"], form.observaciones_operativas);

  setNested(next, ["riesgo_global", "nivel"], form.riesgo_global);

  const matPreliminar = parseInputNumber(form.materialidad_preliminar);
  const matProyectada = parseInputNumber(form.materialidad_preliminar_proyectada);
  const matPreliminarTrivial = parseInputNumber(form.materialidad_preliminar_trivial);
  const matFinalPlaneacion = parseInputNumber(form.materialidad_final_planeacion);
  const matFinalEjecucion = parseInputNumber(form.materialidad_final_ejecucion);
  const matFinalTrivial = parseInputNumber(form.umbral_trivialidad_final);

  setNested(next, ["materialidad", "preliminar", "materialidad_global"], matPreliminar);
  setNested(next, ["materialidad", "preliminar", "materialidad_desempeno"], matProyectada);
  setNested(next, ["materialidad", "preliminar", "error_trivial"], matPreliminarTrivial);
  setNested(next, ["materialidad", "final", "materialidad_planeacion"], matFinalPlaneacion);
  setNested(next, ["materialidad", "final", "materialidad_ejecucion"], matFinalEjecucion);
  setNested(next, ["materialidad", "final", "umbral_trivialidad"], matFinalTrivial);
  setNested(next, ["materialidad", "preliminar", "base_usada"], form.materialidad_base_usada);
  setNested(next, ["materialidad", "preliminar", "area_referencia"], form.materialidad_area_referencia);
  setNested(next, ["materialidad", "preliminar", "justificacion_nia"], form.materialidad_justificacion_nia);
  setNested(next, ["materialidad", "final", "base_usada"], form.materialidad_base_usada);
  setNested(next, ["materialidad", "final", "area_referencia"], form.materialidad_area_referencia);
  setNested(next, ["materialidad", "final", "justificacion_nia"], form.materialidad_justificacion_nia);
  setNested(next, ["materialidad", "estado_materialidad"], matFinalPlaneacion > 0 && matFinalEjecucion > 0 && matFinalTrivial > 0 ? "final" : "preliminar");
  setNested(next, ["materialidad", "preliminar", "comentario_base"], form.comentario_materialidad);

  return next;
}

function autoCalc(globalValue: string, pct: number): string {
  const base = parseInputNumber(globalValue);
  if (!base) return "";
  return String(Math.round(base * pct * 100) / 100);
}

const ESTADOS_ENCARGO = ["planeacion", "campo", "revision", "cierre"];
const NIVELES_SUPERVISION = ["baja", "media", "alta"];
const COMPLEJIDADES = ["baja", "media", "alta"];

export default function PerfilClientePage() {
  const router = useRouter();
  const { clienteId } = useAuditContext();

  const [basePerfil, setBasePerfil] = useState<PerfilPayload>({});
  const [form, setForm] = useState<PerfilFormData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [success, setSuccess] = useState<string>("");

  useEffect(() => {
    let active = true;

    async function load(): Promise<void> {
      if (!clienteId) {
        setLoading(false);
        setError("No se detecto cliente en la ruta.");
        return;
      }

      setLoading(true);
      setError("");
      setSuccess("");

      try {
        const response = await getPerfil(clienteId);
        if (!active) return;
        setBasePerfil(response.perfil);
        setForm(toFormData(response.perfil));
      } catch (err) {
        if (!active) return;
        const message = err instanceof Error ? err.message : "No se pudo cargar el perfil del cliente.";
        setError(message);
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [clienteId]);

  function updateField<K extends keyof PerfilFormData>(key: K, value: PerfilFormData[K]): void {
    if (!form) return;
    setForm({ ...form, [key]: value });
  }

  function handlePreliminarGlobalChange(value: string): void {
    if (!form) return;
    setForm({
      ...form,
      materialidad_preliminar: value,
      materialidad_preliminar_proyectada: autoCalc(value, 0.75),
      materialidad_preliminar_trivial: autoCalc(value, 0.05),
    });
  }

  function handleFinalGlobalChange(value: string): void {
    if (!form) return;
    setForm({
      ...form,
      materialidad_final_planeacion: value,
      materialidad_final_ejecucion: autoCalc(value, 0.75),
      umbral_trivialidad_final: autoCalc(value, 0.05),
    });
  }

  async function handleSave(): Promise<void> {
    if (!clienteId || !form) return;
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const payload = toPerfilPayload(basePerfil, form);
      const saved = await savePerfil(clienteId, payload);
      setBasePerfil(saved.perfil);
      setForm(toFormData(saved.perfil));
      setSuccess("Perfil guardado correctamente.");
      router.push(`/dashboard/${clienteId}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "No se pudo guardar el perfil.";
      setError(message);
    } finally {
      setSaving(false);
    }
  }

  const riskBar = useMemo(() => {
    if (!form) return 50;
    const level = form.riesgo_global.toUpperCase();
    if (level === "ALTO") return 90;
    if (level === "MEDIO") return 65;
    return 35;
  }, [form]);

  if (loading) {
    return (
      <main className="px-4 md:px-12 py-8 space-y-6">
        <div className="sovereign-card h-20 animate-pulse bg-[#edf2f7]" />
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-8 space-y-6">
            <div className="sovereign-card h-64 animate-pulse bg-[#edf2f7]" />
            <div className="sovereign-card h-64 animate-pulse bg-[#edf2f7]" />
          </div>
          <div className="lg:col-span-4 space-y-6">
            <div className="sovereign-card h-72 animate-pulse bg-[#edf2f7]" />
            <div className="sovereign-card h-56 animate-pulse bg-[#edf2f7]" />
          </div>
        </div>
      </main>
    );
  }

  if (!form) {
    return (
      <main className="px-4 md:px-12 py-8">
        <div className="sovereign-card text-sm text-[#93000a] bg-[#ffdad6] border border-[#ba1a1a]/20">
          {error || "No se pudo inicializar la configuracion del perfil."}
        </div>
      </main>
    );
  }

  return (
    <main className="px-4 md:px-12 py-8 max-w-[1500px] space-y-8">
      <section className="rounded-editorial bg-white shadow-editorial px-6 md:px-8 py-5 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 data-tour="perfil-title" className="font-headline text-4xl md:text-5xl font-bold tracking-tight text-[#041627]">Perfil del encargo</h1>
          <p className="text-slate-600 mt-2 max-w-3xl leading-relaxed">            Define equipo, gobierno operativo y materialidad del encargo sin repetir los datos generales del cliente ni la configuracion del negocio.          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            data-tour="perfil-save"
            className="px-5 py-2.5 rounded-xl border border-[rgba(196,198,205,0.6)] text-sm font-semibold text-slate-600 hover:text-[#041627] hover:bg-[#f8fafc] transition disabled:opacity-60"
          >
            {saving ? "Guardando..." : "Guardar y continuar"}
          </button>
          <button
            type="button"
            onClick={() => router.push(`/dashboard/${clienteId}`)}
            className="px-6 py-2.5 rounded-xl text-white text-sm font-semibold shadow-sm transition active:scale-95"
            style={{ background: "linear-gradient(135deg, #041627 0%, #1a2b3c 100%)" }}
          >
            Ir al dashboard
          </button>
        </div>
      </section>

      {error ? <div className="sovereign-card text-sm text-[#93000a] bg-[#ffdad6] border border-[#ba1a1a]/20">{error}</div> : null}
      {success ? <div className="sovereign-card text-sm text-[#065f46] bg-[#ecfdf5] border border-[#047857]/20">{success}</div> : null}

      <ContextualHelp
        title="Ayuda del modulo Perfil"
        items={[
          { label: "Gobierno del encargo", description: "Define el equipo que lidera y revisa el trabajo, sin duplicar datos del cliente." },
          { label: "Control operativo", description: "Alinea fechas, complejidad y fase para que el flujo avance con trazabilidad." },
          { label: "Materialidad", description: "Mantiene la base NIA 320 y el juicio profesional ya calculado por el equipo." },
        ]}
      />

      <section className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-8 space-y-10">
          <article data-tour="perfil-marco" className="sovereign-card">
            <div className="flex items-center gap-2 mb-6">
              <span className="h-px w-8 bg-[#041627]/20" />
              <h2 className="font-headline text-2xl font-semibold text-[#041627]">Detalles del equipo</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <label className="flex flex-col gap-2"><span className="text-xs font-bold tracking-wider uppercase text-slate-500">Socio responsable</span><input className="ghost-input w-full py-3" value={form.socio_responsable} onChange={(e: ChangeEvent<HTMLInputElement>) => updateField("socio_responsable", e.target.value)} placeholder="Nombre del socio" /></label>
              <label className="flex flex-col gap-2"><span className="text-xs font-bold tracking-wider uppercase text-slate-500">Gerente responsable</span><input className="ghost-input w-full py-3" value={form.gerente_responsable} onChange={(e: ChangeEvent<HTMLInputElement>) => updateField("gerente_responsable", e.target.value)} placeholder="Nombre del gerente" /></label>
              <label className="flex flex-col gap-2"><span className="text-xs font-bold tracking-wider uppercase text-slate-500">Senior</span><input className="ghost-input w-full py-3" value={form.senior_responsable} onChange={(e: ChangeEvent<HTMLInputElement>) => updateField("senior_responsable", e.target.value)} placeholder="Senior asignado" /></label>
              <label className="flex flex-col gap-2"><span className="text-xs font-bold tracking-wider uppercase text-slate-500">Semi senior</span><input className="ghost-input w-full py-3" value={form.semi_responsable} onChange={(e: ChangeEvent<HTMLInputElement>) => updateField("semi_responsable", e.target.value)} placeholder="Semi senior asignado" /></label>
              <label className="flex flex-col gap-2"><span className="text-xs font-bold tracking-wider uppercase text-slate-500">Junior</span><input className="ghost-input w-full py-3" value={form.junior_responsable} onChange={(e: ChangeEvent<HTMLInputElement>) => updateField("junior_responsable", e.target.value)} placeholder="Junior asignado" /></label>
              <label className="flex flex-col gap-2"><span className="text-xs font-bold tracking-wider uppercase text-slate-500">Revisor tecnico</span><input className="ghost-input w-full py-3" value={form.revisor_tecnico} onChange={(e: ChangeEvent<HTMLInputElement>) => updateField("revisor_tecnico", e.target.value)} placeholder="Nombre del revisor" /></label>
              <label className="flex flex-col gap-2 md:col-span-2"><span className="text-xs font-bold tracking-wider uppercase text-slate-500">Especialista externo</span><input className="ghost-input w-full py-3" value={form.especialista_externo} onChange={(e: ChangeEvent<HTMLInputElement>) => updateField("especialista_externo", e.target.value)} placeholder="Ej. experto tributario, TI, valuacion" /></label>
            </div>
          </article>

          <article className="sovereign-card">
            <div className="flex items-center gap-2 mb-6">
              <span className="h-px w-8 bg-[#041627]/20" />
              <h2 className="font-headline text-2xl font-semibold text-[#041627]">Control operativo del encargo</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <label className="flex flex-col gap-2"><span className="text-xs font-bold tracking-wider uppercase text-slate-500">Fecha de inicio</span><input className="ghost-input w-full py-3" type="date" value={form.fecha_inicio_encargo} onChange={(e: ChangeEvent<HTMLInputElement>) => updateField("fecha_inicio_encargo", e.target.value)} /></label>
              <label className="flex flex-col gap-2"><span className="text-xs font-bold tracking-wider uppercase text-slate-500">Fecha objetivo de entrega</span><input className="ghost-input w-full py-3" type="date" value={form.fecha_objetivo_entrega} onChange={(e: ChangeEvent<HTMLInputElement>) => updateField("fecha_objetivo_entrega", e.target.value)} /></label>
              <label className="flex flex-col gap-2"><span className="text-xs font-bold tracking-wider uppercase text-slate-500">Estado del encargo</span><select className="ghost-input w-full py-3" value={form.estado_encargo} onChange={(e: ChangeEvent<HTMLSelectElement>) => updateField("estado_encargo", e.target.value)}>{ESTADOS_ENCARGO.map((estado) => (<option key={estado} value={estado}>{estado}</option>))}</select></label>
              <label className="flex flex-col gap-2"><span className="text-xs font-bold tracking-wider uppercase text-slate-500">Nivel de supervision</span><select className="ghost-input w-full py-3" value={form.nivel_supervision} onChange={(e: ChangeEvent<HTMLSelectElement>) => updateField("nivel_supervision", e.target.value)}>{NIVELES_SUPERVISION.map((nivel) => (<option key={nivel} value={nivel}>{nivel}</option>))}</select></label>
              <label className="flex flex-col gap-2"><span className="text-xs font-bold tracking-wider uppercase text-slate-500">Complejidad del encargo</span><select className="ghost-input w-full py-3" value={form.complejidad_encargo} onChange={(e: ChangeEvent<HTMLSelectElement>) => updateField("complejidad_encargo", e.target.value)}>{COMPLEJIDADES.map((nivel) => (<option key={nivel} value={nivel}>{nivel}</option>))}</select></label>
              <label className="flex flex-col gap-2 md:col-span-2"><span className="text-xs font-bold tracking-wider uppercase text-slate-500">Observaciones operativas</span><textarea rows={4} className="ghost-input w-full" value={form.observaciones_operativas} onChange={(e: ChangeEvent<HTMLTextAreaElement>) => updateField("observaciones_operativas", e.target.value)} placeholder="Notas sobre revision, dependencias, tiempos, riesgos o soporte requerido." /></label>
            </div>
          </article>

          <article className="sovereign-card">
            <div className="flex items-center gap-2 mb-6">
              <span className="h-px w-8 bg-[#041627]/20" />
              <h2 className="font-headline text-2xl font-semibold text-[#041627]">Materialidad</h2>
            </div>
            <div className="mb-8">
              <p className="text-xs font-bold tracking-widest uppercase text-slate-500 mb-4">Preliminar</p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="flex flex-col gap-1"><span className="text-xs font-bold tracking-wider uppercase text-slate-500">Global</span><div className="flex items-end gap-2"><input type="number" className="ghost-input w-full py-3 text-base font-semibold text-[#041627]" value={form.materialidad_preliminar} placeholder="0" onChange={(e: ChangeEvent<HTMLInputElement>) => handlePreliminarGlobalChange(e.target.value)} /><span className="text-sm font-medium text-slate-500 pb-1 shrink-0">USD</span></div></div>
                <div className="flex flex-col gap-1"><span className="text-xs font-bold tracking-wider uppercase text-slate-500">Desempeno <span className="normal-case font-normal text-slate-400">(75%)</span></span><div className="flex items-end gap-2"><input type="number" className="ghost-input w-full py-3 text-base font-semibold text-[#041627]" value={form.materialidad_preliminar_proyectada} placeholder="0" onChange={(e: ChangeEvent<HTMLInputElement>) => updateField("materialidad_preliminar_proyectada", e.target.value)} /><span className="text-sm font-medium text-slate-500 pb-1 shrink-0">USD</span></div><p className="text-[10px] text-slate-400">Auto-calculado Â· editable</p></div>
                <div className="flex flex-col gap-1"><span className="text-xs font-bold tracking-wider uppercase text-slate-500">Trivial <span className="normal-case font-normal text-slate-400">(5%)</span></span><div className="flex items-end gap-2"><input type="number" className="ghost-input w-full py-3 text-base font-semibold text-[#041627]" value={form.materialidad_preliminar_trivial} placeholder="0" onChange={(e: ChangeEvent<HTMLInputElement>) => updateField("materialidad_preliminar_trivial", e.target.value)} /><span className="text-sm font-medium text-slate-500 pb-1 shrink-0">USD</span></div><p className="text-[10px] text-slate-400">Auto-calculado Â· editable</p></div>
              </div>
            </div>

            <div className="border-t border-slate-100 mb-8" />

            <div className="mb-8">
              <p className="text-xs font-bold tracking-widest uppercase text-slate-500 mb-4">Base NIA y juicio profesional</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <label className="flex flex-col gap-2"><span className="text-xs font-bold tracking-wider uppercase text-slate-500 flex items-center gap-2">Base usada<QuestionHelp text="Indica la base financiera usada para calcular la materialidad segun NIA 320: ingresos, activo, patrimonio, EBIT, cuentas por cobrar, inventarios u otra." /></span><select className="ghost-input w-full py-3" value={form.materialidad_base_usada} onChange={(e: ChangeEvent<HTMLSelectElement>) => updateField("materialidad_base_usada", e.target.value)}><option value="Ingresos">Ingresos</option><option value="Activo">Activo</option><option value="Patrimonio">Patrimonio</option><option value="EBIT">EBIT</option><option value="CxC">Cuentas por cobrar</option><option value="Inventarios">Inventarios</option><option value="Otro">Otro</option></select></label>
                <label className="flex flex-col gap-2"><span className="text-xs font-bold tracking-wider uppercase text-slate-500 flex items-center gap-2">Area de referencia<QuestionHelp text="SeÃ±ala que area del balance o del mayor tomaste como referencia para esa base." /></span><input className="ghost-input w-full py-3" value={form.materialidad_area_referencia} onChange={(e: ChangeEvent<HTMLInputElement>) => updateField("materialidad_area_referencia", e.target.value)} placeholder="Ej. 140 - Efectivo / 130 - CxC" /></label>
                <label className="flex flex-col gap-2 md:col-span-2"><span className="text-xs font-bold tracking-wider uppercase text-slate-500 flex items-center gap-2">Justificacion NIA<QuestionHelp text="Resume por que elegiste esa base y ese porcentaje. Debe dejar claro el juicio profesional conforme a NIA 320." /></span><textarea rows={4} className="ghost-input w-full" value={form.materialidad_justificacion_nia} onChange={(e: ChangeEvent<HTMLTextAreaElement>) => updateField("materialidad_justificacion_nia", e.target.value)} placeholder="Explica brevemente la razon profesional de la materialidad." /></label>
              </div>
            </div>

            <div className="mb-8">
              <p className="text-xs font-bold tracking-widest uppercase text-slate-500 mb-4">Final</p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="flex flex-col gap-1"><span className="text-xs font-bold tracking-wider uppercase text-slate-500">Global</span><div className="flex items-end gap-2"><input type="number" className="ghost-input w-full py-3 text-base font-semibold text-[#041627]" value={form.materialidad_final_planeacion} placeholder="0" onChange={(e: ChangeEvent<HTMLInputElement>) => handleFinalGlobalChange(e.target.value)} /><span className="text-sm font-medium text-slate-500 pb-1 shrink-0">USD</span></div></div>
                <div className="flex flex-col gap-1"><span className="text-xs font-bold tracking-wider uppercase text-slate-500">Desempeno <span className="normal-case font-normal text-slate-400">(75%)</span></span><div className="flex items-end gap-2"><input type="number" className="ghost-input w-full py-3 text-base font-semibold text-[#041627]" value={form.materialidad_final_ejecucion} placeholder="0" onChange={(e: ChangeEvent<HTMLInputElement>) => updateField("materialidad_final_ejecucion", e.target.value)} /><span className="text-sm font-medium text-slate-500 pb-1 shrink-0">USD</span></div><p className="text-[10px] text-slate-400">Auto-calculado Â· editable</p></div>
                <div className="flex flex-col gap-1"><span className="text-xs font-bold tracking-wider uppercase text-slate-500">Trivial <span className="normal-case font-normal text-slate-400">(5%)</span></span><div className="flex items-end gap-2"><input type="number" className="ghost-input w-full py-3 text-base font-semibold text-[#041627]" value={form.umbral_trivialidad_final} placeholder="0" onChange={(e: ChangeEvent<HTMLInputElement>) => updateField("umbral_trivialidad_final", e.target.value)} /><span className="text-sm font-medium text-slate-500 pb-1 shrink-0">USD</span></div><p className="text-[10px] text-slate-400">Auto-calculado Â· editable</p></div>
              </div>
            </div>

            <div className="border-t border-slate-100 mb-6" />

            <div className="flex flex-col gap-2">
              <span className="text-xs font-bold tracking-wider uppercase text-slate-500">Comentario de base de materialidad</span>
              <textarea rows={3} className="ghost-input w-full" value={form.comentario_materialidad} onChange={(e: ChangeEvent<HTMLTextAreaElement>) => updateField("comentario_materialidad", e.target.value)} />
            </div>
          </article>
        </div>

        <aside className="lg:col-span-4 space-y-8">
          <article className="rounded-editorial p-8 shadow-editorial relative overflow-hidden text-white" style={{ background: "linear-gradient(135deg, #1a2b3c 0%, #041627 100%)" }}>
            <div className="relative z-10 space-y-4">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[#a5eff0]" style={{ fontVariationSettings: "'FILL' 1" }}>auto_awesome</span>
                <span className="text-xs font-bold tracking-widest uppercase text-[#a5eff0]">Resumen operativo</span>
              </div>
              <h3 className="font-headline text-2xl leading-snug">{form.firma_auditoria}</h3>
              <p className="text-sm text-slate-200">Auditor encargado: {form.auditor_encargado || "N/D"}</p>
              <div className="rounded-2xl bg-white/10 p-4 text-sm space-y-2">
                <p><span className="font-semibold">Estado:</span> {form.estado_encargo}</p>
                <p><span className="font-semibold">Supervision:</span> {form.nivel_supervision}</p>
                <p><span className="font-semibold">Complejidad:</span> {form.complejidad_encargo}</p>
                <p><span className="font-semibold">Periodo:</span> {form.fiscal_year}</p>
              </div>
              <button className="w-full py-3 rounded-xl border border-[#a5eff0]/30 text-[#a5eff0] text-xs font-bold uppercase tracking-widest hover:bg-[#a5eff0]/10 transition-colors">Equipo listo</button>
            </div>
            <div className="absolute -right-12 -bottom-12 w-48 h-48 bg-[#002f30]/40 rounded-full blur-3xl" />
          </article>

          <article className="sovereign-card">
            <h3 className="font-headline text-xl font-semibold text-[#041627] mb-8 italic">Parametros criticos</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">Riesgo global</span>
                <span className="text-xs font-bold text-[#002f30] px-2 py-1 bg-[#a5eff0] rounded-md uppercase">{form.riesgo_global}</span>
              </div>
              <div className="relative w-full h-1.5 bg-[#e5e9eb] rounded-full overflow-hidden">
                <div className="absolute top-0 left-0 h-full bg-[#002f30]" style={{ width: `${riskBar}%` }} />
              </div>
              <div className="flex justify-between text-[10px] text-slate-400 font-medium">
                <span>BAJO</span><span>MEDIO</span><span>ALTO</span>
              </div>
            </div>
          </article>

          <div className="flex items-start gap-4 p-6 bg-[#f1f4f6] rounded-editorial border-l-4 border-[#041627]">
            <span className="material-symbols-outlined text-[#041627]">info</span>
            <div>
              <p className="text-xs font-semibold text-[#041627] mb-1">Nota de cumplimiento</p>
              <p className="text-[11px] text-slate-600 leading-relaxed">Verifica que la configuracion de materialidad, el equipo y las fechas del encargo esten alineados al periodo activo.</p>
            </div>
          </div>
        </aside>
      </section>

      <footer className="pt-6 border-t border-slate-200 flex flex-col gap-4 md:flex-row md:justify-between md:items-center">
        <div className="flex items-center gap-4 text-xs text-slate-500">
          <span className="flex items-center gap-1"><span className="material-symbols-outlined text-sm">lock</span> ConexiÃ³n encriptada</span>
          <span className="w-1 h-1 bg-slate-300 rounded-full" />
          <span>Ultimo guardado: {success ? "Ahora" : "Pendiente"}</span>
        </div>
        <div className="flex gap-3">
          <button type="button" onClick={() => setForm(toFormData(basePerfil))} className="px-6 py-3 rounded-xl font-semibold text-[#041627] hover:bg-[#f1f4f6] transition-colors">Limpiar cambios</button>
          <button type="button" onClick={handleSave} disabled={saving} className="px-8 py-3 rounded-xl text-white font-bold shadow-sm disabled:opacity-60" style={{ background: "linear-gradient(135deg, #041627 0%, #1a2b3c 100%)" }}>{saving ? "Guardando..." : "Confirmar perfil de auditoria"}</button>
        </div>
      </footer>
    </main>
  );
}

