"use client";

import Link from "next/link";
import { type ReactNode, useEffect, useMemo, useState } from "react";

import {
  getAreaProcedures,
  getProcedureAreas,
  type AreaProcedureDetail,
  type ProcedureItem,
  type ProcedureAreaSummary,
} from "../../lib/api/procedimientos";
import { useLearningRole } from "../../lib/hooks/useLearningRole";

function normalizeText(value: string): string {
  return (value || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim();
}

function normalizeNiaRefToCode(niaRef: string): string {
  const normalized = niaRef.toUpperCase().replace(/\s+/g, "");
  const match = normalized.match(/NIA(\d{3})/);
  if (match) return `NIA-${match[1]}`;
  return niaRef.toUpperCase().replace(/\s+/g, "-");
}

function juniorWhy(proc: ProcedureItem): string {
  if (proc.tipo === "confirmacion_externa") {
    return "Confirma con terceros y reduce riesgo de sesgo en datos del cliente.";
  }
  if (proc.tipo === "analitico") {
    return "Detecta variaciones inusuales antes de profundizar en pruebas de detalle.";
  }
  if (proc.tipo === "recalculo") {
    return "Comprueba exactitud matematica en saldos y estimaciones.";
  }
  return "Aporta evidencia suficiente sobre la aseveracion con mayor exposicion del area.";
}

function procedureTone(proc: ProcedureItem): string {
  if (proc.obligatorio) return "bg-rose-50 text-rose-700 border-rose-200";
  return "bg-slate-100 text-slate-700 border-slate-200";
}

export default function ProcedimientosPage() {
  const { role, roleLabel } = useLearningRole();
  const [areas, setAreas] = useState<ProcedureAreaSummary[]>([]);
  const [areasLoading, setAreasLoading] = useState<boolean>(true);
  const [areasError, setAreasError] = useState<string>("");
  const [areaSearch, setAreaSearch] = useState<string>("");
  const [selectedAreaCode, setSelectedAreaCode] = useState<string>("");
  const [detail, setDetail] = useState<AreaProcedureDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);
  const [detailError, setDetailError] = useState<string>("");
  const [expandedProcedureId, setExpandedProcedureId] = useState<string>("");
  const [mobileListOpen, setMobileListOpen] = useState<boolean>(true);

  useEffect(() => {
    let active = true;
    const run = async () => {
      setAreasLoading(true);
      setAreasError("");
      try {
        const rows = await getProcedureAreas();
        if (!active) return;
        setAreas(rows);
        const defaultArea = rows.find((row) => row.procedures_count > 0) ?? rows[0];
        setSelectedAreaCode(defaultArea?.area_codigo ?? "");
      } catch (error: unknown) {
        if (!active) return;
        setAreasError(error instanceof Error ? error.message : "No se pudo cargar el catalogo de areas.");
      } finally {
        if (active) setAreasLoading(false);
      }
    };
    void run();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedAreaCode) return;
    let active = true;
    const run = async () => {
      setDetailLoading(true);
      setDetailError("");
      try {
        const payload = await getAreaProcedures(selectedAreaCode);
        if (!active) return;
        setDetail(payload);
        setExpandedProcedureId("");
      } catch (error: unknown) {
        if (!active) return;
        setDetailError(error instanceof Error ? error.message : "No se pudieron cargar los procedimientos del area.");
        setDetail(null);
      } finally {
        if (active) setDetailLoading(false);
      }
    };
    void run();
    return () => {
      active = false;
    };
  }, [selectedAreaCode]);

  const filteredAreas = useMemo(() => {
    const query = normalizeText(areaSearch);
    if (!query) return areas;
    return areas.filter((row) => {
      const hayCodigo = normalizeText(row.area_codigo).includes(query);
      const hayNombre = normalizeText(row.area_nombre).includes(query);
      return hayCodigo || hayNombre;
    });
  }, [areaSearch, areas]);

  const visibleProcedures = useMemo(() => {
    if (!detail) return [];
    if (role === "junior") return detail.procedimientos.filter((proc) => proc.obligatorio);
    if (role === "semi") {
      return [...detail.procedimientos].sort((a, b) => Number(b.obligatorio) - Number(a.obligatorio));
    }
    return detail.procedimientos;
  }, [detail, role]);

  const socioSummary = useMemo(() => {
    if (!detail) return { criticalRisks: 0, keyProcedures: [] as ProcedureItem[] };
    const criticalAfirmaciones = new Set(
      detail.riesgos_tipicos
        .filter((risk) => {
          const level = normalizeText(risk.nivel);
          return level.includes("alto") || level.includes("critico");
        })
        .map((risk) => normalizeText(risk.afirmacion)),
    );
    const keyProcedures = detail.procedimientos.filter(
      (proc) => proc.obligatorio || criticalAfirmaciones.has(normalizeText(proc.afirmacion)),
    );
    return {
      criticalRisks: criticalAfirmaciones.size,
      keyProcedures: keyProcedures.slice(0, 8),
    };
  }, [detail]);

  return (
    <div className="pt-4 pb-8 max-w-screen-2xl space-y-6">
      <header className="sovereign-card">
        <p className="text-xs uppercase tracking-[0.16em] text-slate-500 font-semibold">Biblioteca Dinamica</p>
        <h1 className="font-headline text-4xl text-[#041627] mt-2">Procedimientos por Area</h1>
        <p className="text-sm text-slate-600 mt-2">
          Catalogo operativo conectado a YAML para ejecucion de auditoria por riesgo, aseveracion y referencia NIA.
        </p>
        <p className="mt-3 text-[11px] uppercase tracking-[0.12em] text-slate-500 font-semibold">Vista activa: {roleLabel}</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-[340px_minmax(0,1fr)] gap-6">
        <aside className="sovereign-card md:max-h-[calc(100vh-180px)] md:overflow-auto">
          <label className="text-[11px] uppercase tracking-[0.12em] text-slate-500 font-bold block">
            Buscar area
            <div className="mt-2 relative">
              <span className="material-symbols-outlined pointer-events-none absolute left-3 top-2.5 text-base text-slate-400">search</span>
              <input
                type="text"
                value={areaSearch}
                onChange={(e) => setAreaSearch(e.target.value)}
                placeholder="Codigo o nombre del area"
                className="w-full rounded-lg border border-[#041627]/15 bg-[#f1f4f6] pl-10 pr-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-[#89d3d4] focus:outline-none"
              />
            </div>
          </label>

          <button
            type="button"
            onClick={() => setMobileListOpen((prev) => !prev)}
            className="md:hidden mt-3 inline-flex items-center gap-2 rounded-lg border border-[#041627]/20 px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-[#041627]"
          >
            <span className="material-symbols-outlined text-base">{mobileListOpen ? "expand_less" : "expand_more"}</span>
            {mobileListOpen ? "Ocultar areas" : "Mostrar areas"}
          </button>

          <div className={`mt-4 space-y-2 ${mobileListOpen ? "block" : "hidden"} md:block`}>
            {areasLoading ? <p className="text-sm text-slate-500">Cargando areas...</p> : null}
            {areasError ? <p className="text-sm text-rose-700">{areasError}</p> : null}
            {!areasLoading && !areasError && filteredAreas.length === 0 ? (
              <p className="text-sm text-slate-500">No hay areas para el filtro actual.</p>
            ) : null}
            {filteredAreas.map((area) => (
              <button
                key={area.area_codigo}
                type="button"
                onClick={() => {
                  setSelectedAreaCode(area.area_codigo);
                  setMobileListOpen(false);
                }}
                className={`w-full rounded-lg border px-3 py-2 text-left transition-colors ${
                  selectedAreaCode === area.area_codigo
                    ? "border-[#89d3d4] bg-[#a5eff0]/10"
                    : "border-black/10 bg-white hover:bg-slate-50"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.1em] text-slate-500 font-bold">{area.area_codigo}</p>
                    <p className="text-xs text-slate-700 line-clamp-2">{area.area_nombre}</p>
                  </div>
                  <span className="rounded-full bg-[#041627]/10 px-2 py-0.5 text-[10px] font-bold text-[#041627]">
                    {area.procedures_count}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </aside>

        <section className="space-y-4">
          {detailLoading ? <article className="sovereign-card text-sm text-slate-500">Cargando procedimientos...</article> : null}
          {detailError ? <article className="sovereign-card text-sm text-rose-700">{detailError}</article> : null}

          {detail && !detailLoading ? (
            <>
              <article className="sovereign-card">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-[#041627] px-3 py-1 text-[11px] font-bold uppercase tracking-[0.12em] text-white">
                    {detail.area_codigo}
                  </span>
                  <span className="rounded-full border border-[#041627]/15 bg-[#f1f4f6] px-3 py-1 text-[11px] font-semibold text-[#041627]">
                    {detail.procedimientos.length} procedimientos
                  </span>
                </div>
                <h2 className="font-headline text-3xl text-[#041627] mt-3">{detail.area_nombre}</h2>
                {role === "junior" ? (
                  <p className="text-sm text-slate-600 mt-2">Mostrando solo obligatorios para ejecutar sin desviarte del criterio base.</p>
                ) : role === "semi" ? (
                  <p className="text-sm text-slate-600 mt-2">Vista mixta: obligatorios primero y opcionales destacados.</p>
                ) : role === "socio" ? (
                  <p className="text-sm text-slate-600 mt-2">Vista ejecutiva priorizando cobertura frente a riesgos criticos.</p>
                ) : (
                  <p className="text-sm text-slate-600 mt-2">Vista completa con metadata tecnica para planificacion y supervision.</p>
                )}
              </article>

              {role === "socio" ? (
                <article className="sovereign-card space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div className="rounded-lg border border-[#041627]/15 bg-[#f1f4f6] p-4">
                      <p className="text-[10px] uppercase tracking-[0.12em] text-slate-500 font-bold">Riesgos criticos</p>
                      <p className="font-headline text-3xl text-[#041627] mt-2">{socioSummary.criticalRisks}</p>
                    </div>
                    <div className="rounded-lg border border-[#041627]/15 bg-[#f1f4f6] p-4">
                      <p className="text-[10px] uppercase tracking-[0.12em] text-slate-500 font-bold">Procedimientos clave</p>
                      <p className="font-headline text-3xl text-[#041627] mt-2">{socioSummary.keyProcedures.length}</p>
                    </div>
                    <div className="rounded-lg border border-[#041627]/15 bg-[#f1f4f6] p-4">
                      <p className="text-[10px] uppercase tracking-[0.12em] text-slate-500 font-bold">Alertas tributarias</p>
                      <p className="font-headline text-3xl text-[#041627] mt-2">{detail.alertas_tributarias.length}</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {socioSummary.keyProcedures.map((proc) => (
                      <div key={proc.id} className="rounded-lg border border-black/10 bg-white p-3">
                        <div className="flex items-center justify-between gap-2">
                          <p className="font-semibold text-[#041627] text-sm">{proc.id} · {proc.descripcion}</p>
                          <span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase ${procedureTone(proc)}`}>
                            {proc.obligatorio ? "Obligatorio" : "Opcional"}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 mt-1">{proc.afirmacion} · {proc.tipo} · {proc.nia_ref}</p>
                      </div>
                    ))}
                  </div>
                </article>
              ) : (
                <article className="sovereign-card overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="min-w-full text-sm">
                      <thead className="bg-[#f1f4f6] text-left">
                        <tr>
                          <th className="px-3 py-2 text-[11px] uppercase tracking-[0.1em] text-slate-500">ID</th>
                          <th className="px-3 py-2 text-[11px] uppercase tracking-[0.1em] text-slate-500">Descripcion</th>
                          <th className="px-3 py-2 text-[11px] uppercase tracking-[0.1em] text-slate-500">Tipo</th>
                          <th className="px-3 py-2 text-[11px] uppercase tracking-[0.1em] text-slate-500">Afirmacion</th>
                          <th className="px-3 py-2 text-[11px] uppercase tracking-[0.1em] text-slate-500">Estado</th>
                          <th className="px-3 py-2 text-[11px] uppercase tracking-[0.1em] text-slate-500">NIA</th>
                        </tr>
                      </thead>
                      <tbody>
                        {visibleProcedures.flatMap((proc) => {
                          const expanded = expandedProcedureId === proc.id;
                          const rows: ReactNode[] = [
                            <tr
                              key={`${proc.id}-row`}
                              className="border-t border-black/10 cursor-pointer hover:bg-slate-50"
                              onClick={() => setExpandedProcedureId((prev) => (prev === proc.id ? "" : proc.id))}
                            >
                              <td className="px-3 py-2 font-semibold text-[#041627]">{proc.id}</td>
                              <td className="px-3 py-2 text-slate-700">{proc.descripcion}</td>
                              <td className="px-3 py-2 text-slate-600">{proc.tipo}</td>
                              <td className="px-3 py-2 text-slate-600">{proc.afirmacion}</td>
                              <td className="px-3 py-2">
                                <span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase ${procedureTone(proc)}`}>
                                  {proc.obligatorio ? "Obligatorio" : "Opcional"}
                                </span>
                              </td>
                              <td className="px-3 py-2">
                                <Link
                                  href={`/biblioteca?norma=${encodeURIComponent(normalizeNiaRefToCode(proc.nia_ref))}`}
                                  className="text-[#002f30] underline underline-offset-2 hover:text-[#041627]"
                                  onClick={(event) => event.stopPropagation()}
                                >
                                  {proc.nia_ref}
                                </Link>
                              </td>
                            </tr>,
                          ];

                          if (expanded) {
                            rows.push(
                              <tr key={`${proc.id}-expanded`} className="border-t border-black/5 bg-[#f9fbfc]">
                                <td colSpan={6} className="px-3 py-3">
                                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    <div className="rounded-lg border border-[#041627]/10 bg-white p-3">
                                      <p className="text-[11px] uppercase tracking-[0.1em] text-slate-500 font-bold mb-1">Detalle operativo</p>
                                      <p className="text-sm text-slate-700">
                                        Ejecuta este procedimiento con evidencia suficiente para la aseveracion de <strong>{proc.afirmacion}</strong>.
                                      </p>
                                    </div>
                                    <div className="rounded-lg border border-[#89d3d4]/40 bg-[#a5eff0]/10 p-3">
                                      <p className="text-[11px] uppercase tracking-[0.1em] text-[#002f30] font-bold mb-1">Por que</p>
                                      <p className="text-sm text-[#041627]">{juniorWhy(proc)}</p>
                                    </div>
                                  </div>
                                </td>
                              </tr>,
                            );
                          }

                          return rows;
                        })}
                      </tbody>
                    </table>
                  </div>
                </article>
              )}

              <article className="sovereign-card">
                <p className="text-[11px] uppercase tracking-[0.1em] text-slate-500 font-bold mb-2">Alertas tributarias relevantes</p>
                {detail.alertas_tributarias.length === 0 ? (
                  <p className="text-sm text-slate-600">No hay alertas tributarias registradas para esta area.</p>
                ) : (
                  <div className="space-y-2">
                    {detail.alertas_tributarias.map((alert) => (
                      <div key={alert.id} className="rounded-lg border border-black/10 bg-white p-3">
                        <p className="font-semibold text-[#041627] text-sm">{alert.id} · {alert.descripcion}</p>
                        <p className="text-xs text-slate-500 mt-1">{alert.norma} · nivel {alert.nivel}</p>
                        <p className="text-xs text-slate-600 mt-1">{alert.accion}</p>
                      </div>
                    ))}
                  </div>
                )}
              </article>
            </>
          ) : null}
        </section>
      </div>
    </div>
  );
}
