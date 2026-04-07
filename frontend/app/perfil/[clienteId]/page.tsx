"use client";

import { ChangeEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { getPerfil, savePerfil } from "../../../lib/api/perfil";
import { SECTOR_OPTIONS } from "../../../lib/sectorCatalog";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import type { PerfilFormData, PerfilPayload } from "../../../types/perfil";

function asRecord(value: unknown): Record<string, unknown> {
  return typeof value === "object" && value !== null ? (value as Record<string, unknown>) : {};
}

function asString(value: unknown, fallback = ""): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function asNumber(value: unknown, fallback = 0): number {
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
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
    if (typeof current !== "object" || current === null) {
      cursor[key] = {};
    }
    cursor = cursor[key] as Record<string, unknown>;
  }
  cursor[path[path.length - 1]] = value;
}

function toFormData(perfil: PerfilPayload): PerfilFormData {
  const cliente = asRecord(perfil.cliente);
  const encargo = asRecord(perfil.encargo);
  const riesgoGlobal = asRecord(perfil.riesgo_global);
  const materialidad = asRecord(perfil.materialidad);
  const preliminar = asRecord(materialidad.preliminar);

  return {
    firma_auditoria: asString(encargo.firma_auditora, "Socio AI"),
    auditor_encargado: asString(encargo.encargado_asignado, asString(encargo.socio_asignado, "")),
    fiscal_year: String(encargo.anio_activo ?? "2025"),
    sector: asString(cliente.sector, "Holding"),
    nombre_legal: asString(cliente.nombre_legal, ""),
    pais_operacion: asString(cliente.pais, "Ecuador"),
    marco_contable: asString(encargo.marco_referencial, "NIIF para PYMES"),
    norma_auditoria: asString(encargo.norma_auditoria, "NIAs"),
    riesgo_global: asString(riesgoGlobal.nivel, "MEDIO").toUpperCase(),
    materialidad_preliminar: asNumber(preliminar.materialidad_global, 0),
    comentario_materialidad: asString(preliminar.comentario_base, "Calculado segun base de materialidad del encargo."),
  };
}

function toPerfilPayload(base: PerfilPayload, form: PerfilFormData): PerfilPayload {
  const next = deepClone(base);

  setNested(next, ["cliente", "nombre_legal"], form.nombre_legal);
  setNested(next, ["cliente", "sector"], form.sector);
  setNested(next, ["cliente", "pais"], form.pais_operacion);

  setNested(next, ["encargo", "firma_auditora"], form.firma_auditoria);
  setNested(next, ["encargo", "encargado_asignado"], form.auditor_encargado);
  setNested(next, ["encargo", "anio_activo"], Number(form.fiscal_year));
  setNested(next, ["encargo", "marco_referencial"], form.marco_contable);
  setNested(next, ["encargo", "norma_auditoria"], form.norma_auditoria);

  setNested(next, ["riesgo_global", "nivel"], form.riesgo_global);
  setNested(next, ["materialidad", "preliminar", "materialidad_global"], form.materialidad_preliminar);
  setNested(next, ["materialidad", "preliminar", "comentario_base"], form.comentario_materialidad);

  return next;
}

const MARCOS = ["NIIF para PYMES", "NIIF Plenas", "US GAAP", "Norma local"];
const NORMAS = ["NIAs", "Normas Locales", "PCAOB"];

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
      <section className="rounded-editorial bg-white/85 backdrop-blur-sm shadow-editorial px-6 md:px-8 py-5 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 data-tour="perfil-title" className="font-headline text-4xl md:text-5xl font-bold tracking-tight text-[#041627]">Configuracion del Perfil</h1>
          <p className="text-slate-600 mt-2 max-w-3xl leading-relaxed">
            Define los parametros del encargo para que Socio AI construya la estrategia inicial de auditoria sin perder trazabilidad.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            data-tour="perfil-save"
            className="px-5 py-2.5 rounded-xl border border-[rgba(196,198,205,0.6)] text-sm font-semibold text-slate-600 hover:text-[#041627] hover:bg-[#f8fafc] transition disabled:opacity-60"
          >
            {saving ? "Guardando..." : "Guardar progreso"}
          </button>
          <button
            type="button"
            onClick={() => router.push(`/dashboard/${clienteId}`)}
            className="px-6 py-2.5 rounded-xl text-white text-sm font-semibold shadow-sm transition active:scale-95"
            style={{ background: "linear-gradient(135deg, #041627 0%, #1a2b3c 100%)" }}
          >
            Iniciar auditoria
          </button>
        </div>
      </section>

      {error ? <div className="sovereign-card text-sm text-[#93000a] bg-[#ffdad6] border border-[#ba1a1a]/20">{error}</div> : null}
      {success ? <div className="sovereign-card text-sm text-[#065f46] bg-[#ecfdf5] border border-[#047857]/20">{success}</div> : null}

      <section className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-8 space-y-10">
          <article data-tour="perfil-marco" className="sovereign-card">
            <div className="flex items-center gap-2 mb-6">
              <span className="h-px w-8 bg-[#041627]/20" />
              <h2 className="font-headline text-2xl font-semibold text-[#041627]">Detalles de la firma y auditor</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <label className="flex flex-col gap-2">
                <span className="text-xs font-bold tracking-wider uppercase text-slate-500">Nombre de la firma</span>
                <input className="ghost-input w-full py-3" value={form.firma_auditoria} onChange={(e: ChangeEvent<HTMLInputElement>) => updateField("firma_auditoria", e.target.value)} />
              </label>
              <label className="flex flex-col gap-2">
                <span className="text-xs font-bold tracking-wider uppercase text-slate-500">Auditor encargado</span>
                <input className="ghost-input w-full py-3" value={form.auditor_encargado} onChange={(e: ChangeEvent<HTMLInputElement>) => updateField("auditor_encargado", e.target.value)} />
              </label>
              <label className="flex flex-col gap-2 md:col-span-2">
                <span className="text-xs font-bold tracking-wider uppercase text-slate-500">Ano fiscal de auditoria</span>
                <input className="ghost-input w-full py-3" value={form.fiscal_year} onChange={(e: ChangeEvent<HTMLInputElement>) => updateField("fiscal_year", e.target.value)} />
              </label>
            </div>
          </article>

          <article className="sovereign-card">
            <div className="flex items-center gap-2 mb-6">
              <span className="h-px w-8 bg-[#041627]/20" />
              <h2 className="font-headline text-2xl font-semibold text-[#041627]">Perfil del cliente</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <label className="flex flex-col gap-2">
                <span className="text-xs font-bold tracking-wider uppercase text-slate-500">Sector industrial</span>
                <select className="ghost-input w-full py-3" value={form.sector} onChange={(e: ChangeEvent<HTMLSelectElement>) => updateField("sector", e.target.value)}>
                  {SECTOR_OPTIONS.map((sector) => (
                    <option key={sector} value={sector}>{sector}</option>
                  ))}
                </select>
              </label>
              <label className="flex flex-col gap-2">
                <span className="text-xs font-bold tracking-wider uppercase text-slate-500">Nombre legal</span>
                <input className="ghost-input w-full py-3" value={form.nombre_legal} onChange={(e: ChangeEvent<HTMLInputElement>) => updateField("nombre_legal", e.target.value)} />
              </label>
              <label className="flex flex-col gap-2 md:col-span-2">
                <span className="text-xs font-bold tracking-wider uppercase text-slate-500">Pais de operacion principal</span>
                <input className="ghost-input w-full py-3" value={form.pais_operacion} onChange={(e: ChangeEvent<HTMLInputElement>) => updateField("pais_operacion", e.target.value)} />
              </label>
            </div>
          </article>

          <article className="sovereign-card">
            <div className="flex items-center gap-2 mb-6">
              <span className="h-px w-8 bg-[#041627]/20" />
              <h2 className="font-headline text-2xl font-semibold text-[#041627]">Marco regulatorio</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <p className="text-sm font-semibold text-[#041627]">Estandar de contabilidad</p>
                <select className="ghost-input w-full py-3" value={form.marco_contable} onChange={(e: ChangeEvent<HTMLSelectElement>) => updateField("marco_contable", e.target.value)}>
                  {MARCOS.map((marco) => (
                    <option key={marco} value={marco}>{marco}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-4">
                <p className="text-sm font-semibold text-[#041627]">Norma de auditoria</p>
                <select className="ghost-input w-full py-3" value={form.norma_auditoria} onChange={(e: ChangeEvent<HTMLSelectElement>) => updateField("norma_auditoria", e.target.value)}>
                  {NORMAS.map((norma) => (
                    <option key={norma} value={norma}>{norma}</option>
                  ))}
                </select>
              </div>
            </div>
          </article>
        </div>

        <aside className="lg:col-span-4 space-y-8">
          <article className="rounded-editorial p-8 shadow-editorial relative overflow-hidden text-white" style={{ background: "linear-gradient(135deg, #1a2b3c 0%, #041627 100%)" }}>
            <div className="relative z-10">
              <div className="flex items-center gap-2 mb-6">
                <span className="material-symbols-outlined text-[#a5eff0]" style={{ fontVariationSettings: "'FILL' 1" }}>auto_awesome</span>
                <span className="text-xs font-bold tracking-widest uppercase text-[#a5eff0]">Asistente Socio AI</span>
              </div>
              <h3 className="font-headline text-2xl mb-4 leading-snug">Estrategia sugerida para {form.sector}</h3>
              <p className="text-sm leading-relaxed text-slate-200 mb-6">
                Prioriza pruebas sustantivas en cuentas de alto impacto y valida consistencia de marco {form.marco_contable} con {form.norma_auditoria}.
              </p>
              <ul className="space-y-3 mb-8 text-xs text-slate-200">
                <li className="flex gap-3"><span className="material-symbols-outlined text-[#a5eff0] text-sm">check_circle</span> Cobertura de ingresos y corte.</li>
                <li className="flex gap-3"><span className="material-symbols-outlined text-[#a5eff0] text-sm">check_circle</span> Integridad de pasivos y revelaciones.</li>
              </ul>
              <button className="w-full py-3 rounded-xl border border-[#a5eff0]/30 text-[#a5eff0] text-xs font-bold uppercase tracking-widest hover:bg-[#a5eff0]/10 transition-colors">
                Adoptar estrategia IA
              </button>
            </div>
            <div className="absolute -right-12 -bottom-12 w-48 h-48 bg-[#002f30]/40 rounded-full blur-3xl" />
          </article>

          <article className="sovereign-card">
            <h3 className="font-headline text-xl font-semibold text-[#041627] mb-8 italic">Parametros criticos</h3>
            <div className="space-y-10">
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

              <div className="space-y-4">
                <label className="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">Materialidad preliminar</label>
                <div className="flex items-end gap-2">
                  <input
                    type="number"
                    className="ghost-input w-full py-3 text-lg font-semibold text-[#041627]"
                    value={form.materialidad_preliminar}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => updateField("materialidad_preliminar", Number(e.target.value || 0))}
                  />
                  <span className="text-sm font-medium text-slate-500 pb-1">USD</span>
                </div>
                <textarea
                  rows={3}
                  className="ghost-input w-full"
                  value={form.comentario_materialidad}
                  onChange={(e: ChangeEvent<HTMLTextAreaElement>) => updateField("comentario_materialidad", e.target.value)}
                />
              </div>
            </div>
          </article>

          <div className="flex items-start gap-4 p-6 bg-[#f1f4f6] rounded-editorial border-l-4 border-[#041627]">
            <span className="material-symbols-outlined text-[#041627]">info</span>
            <div>
              <p className="text-xs font-semibold text-[#041627] mb-1">Nota de cumplimiento</p>
              <p className="text-[11px] text-slate-600 leading-relaxed">
                Verifica que la configuracion de NIAs y marco contable este alineada con el periodo activo del encargo.
              </p>
            </div>
          </div>
        </aside>
      </section>

      <footer className="pt-6 border-t border-slate-200 flex flex-col gap-4 md:flex-row md:justify-between md:items-center">
        <div className="flex items-center gap-4 text-xs text-slate-500">
          <span className="flex items-center gap-1"><span className="material-symbols-outlined text-sm">lock</span> Conexion encriptada</span>
          <span className="w-1 h-1 bg-slate-300 rounded-full" />
          <span>Ultimo guardado: {success ? "Ahora" : "Pendiente"}</span>
        </div>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => setForm(toFormData(basePerfil))}
            className="px-6 py-3 rounded-xl font-semibold text-[#041627] hover:bg-[#f1f4f6] transition-colors"
          >
            Limpiar cambios
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="px-8 py-3 rounded-xl text-white font-bold shadow-sm disabled:opacity-60"
            style={{ background: "linear-gradient(135deg, #041627 0%, #1a2b3c 100%)" }}
          >
            {saving ? "Guardando..." : "Confirmar perfil de auditoria"}
          </button>
        </div>
      </footer>
    </main>
  );
}
