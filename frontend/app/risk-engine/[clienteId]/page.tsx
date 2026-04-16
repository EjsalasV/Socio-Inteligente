"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useState } from "react";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import ContextualHelp from "../../../components/help/ContextualHelp";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import { useLearningRole } from "../../../lib/hooks/useLearningRole";
import { useRiskEngine } from "../../../lib/hooks/useRiskEngine";

const CriticalRisks = dynamic(() => import("../../../components/risk/CriticalRisks"), {
  loading: () => <DashboardSkeleton />,
  ssr: false,
});
const RiskMatrix = dynamic(() => import("../../../components/risk/RiskMatrix"), {
  loading: () => <DashboardSkeleton />,
  ssr: false,
});
const RiskStrategyPanel = dynamic(() => import("../../../components/risk/RiskStrategyPanel"), {
  loading: () => <DashboardSkeleton />,
  ssr: false,
});
const RiskProcedureSuggestions = dynamic(() => import("../../../components/risk/RiskProcedureSuggestions"), {
  loading: () => <DashboardSkeleton />,
  ssr: false,
});

export default function RiskEnginePage() {
  const { clienteId } = useAuditContext();
  const { data, isLoading, error } = useRiskEngine(clienteId);
  const { role } = useLearningRole();
  const [showSocioSuggestions, setShowSocioSuggestions] = useState<boolean>(false);
  const [roleViewVisible, setRoleViewVisible] = useState<boolean>(false);

  useEffect(() => {
    setRoleViewVisible(false);
    const t = window.setTimeout(() => setRoleViewVisible(true), 30);
    return () => window.clearTimeout(t);
  }, [role]);

  const strategy = data?.strategy ?? {
    approach: "mixto",
    control_pct: 50,
    substantive_pct: 50,
    rationale: "",
    control_tests: [],
    substantive_tests: [],
  };

  const criticalAreas = data?.areas_criticas ?? [];
  const totalHallazgosAbiertos = criticalAreas.reduce((acc, area) => acc + (area.hallazgos_abiertos || 0), 0);
  const topArea = criticalAreas[0];

  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorMessage message={error} />;
  if (!data) return <ErrorMessage message="No hay datos del motor de riesgos para este cliente." />;

  return (
    <div className="pt-4 pb-8 space-y-8 max-w-screen-2xl">
      <header className="mb-4">
        <span className="text-[#001919] font-label text-xs tracking-[0.2em] uppercase font-bold mb-2 block">
          Risk Intelligence Dashboard
        </span>
        <h1 data-tour="risk-title" className="font-headline text-4xl font-bold text-[#041627] tracking-tight">
          Motor de Riesgos - Mapa de Calor de Auditoría
        </h1>
        <div className="mt-3">
          <Link
            href="/procedimientos"
            className="inline-flex items-center gap-2 rounded-lg border border-[#041627]/20 bg-white px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-[#041627] hover:bg-slate-50"
          >
            <span className="material-symbols-outlined text-base">fact_check</span>
            Ver catalogo de procedimientos
          </Link>
        </div>
      </header>

      <ContextualHelp
        title="Ayuda del modulo Risk Engine"
        items={[
          {
            label: "Matriz de calor",
            byRole: {
              junior:
                "Empieza por los cuadrantes altos: esas areas tienen mayor probabilidad de error material.",
              semi:
                "Cruza impacto y frecuencia para ubicar las areas de mayor exposicion.",
              senior:
                "Usa la matriz para validar alcance y reasignar recursos a riesgos altos.",
              socio:
                "Usa la matriz para confirmar foco de auditoria, riesgo de emision y necesidad de escalamiento.",
            },
          },
          {
            label: "Areas criticas",
            byRole: {
              junior:
                "Toma la primera area del ranking y pasa a Workspace Areas para ejecutar pruebas.",
              semi:
                "Lista priorizada para decidir donde ejecutar pruebas primero.",
              senior:
                "Valida consistencia del ranking contra conocimiento del negocio y riesgos emergentes.",
              socio:
                "Confirma que las areas criticas soporten la estrategia global y la opinion esperada.",
            },
          },
          {
            label: "Sugerencias de procedimientos",
            byRole: {
              junior:
                "Usa el boton + para convertir sugerencias en tareas concretas en Papeles de Trabajo.",
              semi:
                "Puedes agregar pruebas propuestas directamente a Papeles de Trabajo.",
              senior:
                "Revisa pertinencia y cobertura antes de aprobar la carga masiva de procedimientos.",
              socio:
                "Define solo pruebas de mayor retorno de aseguramiento y evita sobre-auditar areas no materiales.",
            },
          },
        ]}
      />

      {role === "junior" && (
        <section className="bg-[#a5eff0]/10 border border-[#a5eff0]/30 rounded-xl p-6 space-y-4">
          <div className="flex items-start gap-4">
            <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#041627] text-[#a5eff0] text-xs font-bold mt-0.5">NIA</span>
            <div>
              <p className="text-xs uppercase tracking-[0.15em] text-[#041627]/60 font-bold mb-1">Cómo usar el Risk Engine — Vista Junior</p>
              <p className="text-sm text-[#041627] leading-relaxed">
                El Risk Engine te dice <strong>dónde trabajar primero</strong>. Las áreas con mayor score tienen mayor probabilidad de contener errores materiales. Empieza por el ranking de prioridad.
              </p>
            </div>
          </div>
        </section>
      )}

      {role === "socio" && criticalAreas.length > 0 && (
        <section className="rounded-xl p-6 bg-[#001919] border border-[#a5eff0]/20 shadow-md text-white">
          <p className="text-[10px] uppercase tracking-[0.2em] text-[#a5eff0] font-bold mb-3">Resumen Ejecutivo — Vista Socio</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="bg-white/10 rounded-lg p-4 min-h-[108px]">
              <p className="text-[10px] uppercase tracking-[0.12em] text-slate-300">Enfoque aprobado</p>
              <p className="font-headline text-xl mt-1 font-semibold text-white">{strategy.approach}</p>
              <p className="text-xs text-slate-300 mt-1">{strategy.control_pct}% control · {strategy.substantive_pct}% sustantiva</p>
            </div>
            {criticalAreas.slice(0, 2).map((area) => (
              <div
                key={area.area_id}
                className={`rounded-lg p-4 min-h-[108px] ${
                  area.nivel === "ALTO" || area.nivel === "CRITICO"
                    ? "bg-rose-900/40 border border-rose-700/40"
                    : "bg-amber-900/30 border border-amber-700/30"
                }`}
              >
                <p className="text-[10px] uppercase tracking-[0.12em] text-slate-300">Área crítica</p>
                <p className="font-semibold text-sm text-white mt-1 break-words">{area.area_nombre}</p>
                <p className="text-xs text-slate-300 mt-1">Score: {area.score.toFixed(1)} · {area.nivel}</p>
                {area.hallazgos_abiertos > 0 && <p className="text-xs text-amber-300 mt-1">{area.hallazgos_abiertos} hallazgo(s) abierto(s)</p>}
              </div>
            ))}
          </div>
          {strategy.rationale ? (
            <p className="text-xs text-slate-200 border-t border-white/10 pt-3">{strategy.rationale}</p>
          ) : null}
        </section>
      )}

      <div
        className={`transition-all duration-300 ease-out ${
          roleViewVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-1"
        }`}
      >
        {role === "junior" ? (
          <section className="space-y-5">
            <div className="sovereign-card">
              <h2 className="font-headline text-3xl text-[#041627]">Áreas que debes auditar primero</h2>
              <p className="text-sm text-slate-600 mt-2">
                Empieza por el ranking de mayor riesgo y ejecuta pruebas con evidencia desde el primer ciclo.
              </p>
            </div>

            <div className="space-y-4">
              {criticalAreas.length === 0 ? (
                <div className="sovereign-card text-sm text-slate-600">No hay áreas críticas disponibles para priorizar.</div>
              ) : (
                criticalAreas.map((area, idx) => {
                  const isHigh = area.nivel === "ALTO" || area.nivel === "CRITICO";
                  const isMedium = area.nivel === "MEDIO";
                  const numberTone = isHigh
                    ? "bg-rose-100 text-rose-800"
                    : isMedium
                      ? "bg-amber-100 text-amber-800"
                      : "bg-emerald-100 text-emerald-800";
                  const nivelTone = isHigh
                    ? "bg-rose-100 text-rose-800 border-rose-200"
                    : isMedium
                      ? "bg-amber-100 text-amber-800 border-amber-200"
                      : "bg-emerald-100 text-emerald-800 border-emerald-200";

                  const actionSentence = isHigh
                    ? "Ir al Workspace → generar briefing → ejecutar pruebas sustantivas prioritarias."
                    : isMedium
                      ? "Ir al Workspace → generar briefing → ejecutar pruebas sustantivas y controles clave."
                      : "Ir al Workspace → generar briefing → ejecutar pruebas analíticas y cierre documental.";

                  return (
                    <Link
                      key={`${area.area_id}-${area.area_nombre}`}
                      href={`/areas/${clienteId}/${area.area_id}`}
                      className="block sovereign-card hover:shadow-editorial transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#89d3d4]"
                    >
                      <div className="flex items-start gap-4">
                        <span className={`inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-bold ${numberTone}`}>
                          {idx + 1}
                        </span>
                        <div className="flex-1 space-y-3">
                          <div className="flex flex-wrap items-center gap-2">
                            <h3 className="font-headline text-2xl text-[#041627]">{area.area_nombre}</h3>
                            <span className={`inline-flex rounded-full border px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.1em] ${nivelTone}`}>
                              {area.nivel}
                            </span>
                          </div>
                          <p className="text-sm text-slate-700">{actionSentence}</p>
                          <div className="flex flex-wrap items-center justify-between gap-3">
                            <p className="text-xs uppercase tracking-[0.12em] text-slate-500 font-semibold">Referencia: NIA 315</p>
                            <span className="inline-flex rounded-lg bg-[#041627] px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-white">
                              Abrir Workspace
                            </span>
                          </div>
                        </div>
                      </div>
                    </Link>
                  );
                })
              )}
            </div>

            <article className="rounded-xl border border-[#041627]/15 bg-[#f1f4f6] p-5">
              <p className="text-sm text-[#041627]">
                El motor recomienda {strategy.substantive_pct}% pruebas directas de saldos y {strategy.control_pct}% pruebas de controles.
              </p>
            </article>
          </section>
        ) : null}

        {role === "semi" ? (
          <section className="space-y-6">
            <p className="text-sm text-slate-600">
              Enfoca la ejecución en áreas con mayor score y usa la estrategia recomendada para balancear controles y pruebas sustantivas.
            </p>
            <div className="grid grid-cols-12 gap-6 lg:gap-8">
              <div data-tour="risk-critical" className="col-span-12 xl:col-span-7">
                <CriticalRisks areas={criticalAreas} />
              </div>
              <RiskStrategyPanel areas={criticalAreas} strategy={strategy} />
            </div>
          </section>
        ) : null}

        {role === "senior" ? (
          <div className="grid grid-cols-12 gap-6 lg:gap-8">
            <div data-tour="risk-matrix" className="col-span-12 xl:col-span-7">
              <RiskMatrix data={data} />
            </div>
            <RiskStrategyPanel areas={criticalAreas} strategy={strategy} />
            <div data-tour="risk-critical" className="col-span-12 xl:col-span-5">
              <CriticalRisks areas={criticalAreas} />
            </div>
            <div data-tour="risk-suggestions" className="col-span-12 xl:col-span-7">
              <RiskProcedureSuggestions
                clienteId={clienteId}
                areas={criticalAreas}
                controlTests={strategy.control_tests ?? []}
                substantiveTests={strategy.substantive_tests ?? []}
              />
            </div>
          </div>
        ) : null}

        {role === "socio" ? (
          <section className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <article className="sovereign-card min-h-[110px]">
                <p className="text-[10px] uppercase tracking-[0.12em] text-slate-500 font-bold">Área principal</p>
                <p className="font-headline text-xl text-[#041627] mt-2 break-words">{topArea?.area_nombre ?? "No determinada"}</p>
                <p className="text-xs text-slate-600 mt-1">Nivel: {topArea?.nivel ?? "N/D"}</p>
              </article>
              <article className="sovereign-card min-h-[110px]">
                <p className="text-[10px] uppercase tracking-[0.12em] text-slate-500 font-bold">Estrategia</p>
                <p className="font-headline text-xl text-[#041627] mt-2">{strategy.approach || "mixto"}</p>
                <p className="text-xs text-slate-600 mt-1">{strategy.control_pct}% control · {strategy.substantive_pct}% sustantiva</p>
              </article>
              <article className="sovereign-card min-h-[110px]">
                <p className="text-[10px] uppercase tracking-[0.12em] text-slate-500 font-bold">Hallazgos abiertos</p>
                <p className="font-headline text-3xl text-[#041627] mt-2">{totalHallazgosAbiertos}</p>
              </article>
            </div>

            <article className="rounded-xl bg-[#041627] border border-[#89d3d4]/25 p-6 text-white">
              <p className="text-[10px] uppercase tracking-[0.16em] text-[#89d3d4] font-bold mb-2">Rationale de estrategia</p>
              <p className="text-sm leading-relaxed">{strategy.rationale || "Sin racional técnico disponible."}</p>
            </article>

            <div className="sovereign-card">
              <button
                type="button"
                onClick={() => setShowSocioSuggestions((prev) => !prev)}
                className="inline-flex items-center gap-2 rounded-lg border border-[#041627]/20 px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-[#041627]"
              >
                <span className="material-symbols-outlined text-base">{showSocioSuggestions ? "expand_less" : "expand_more"}</span>
                {showSocioSuggestions ? "Ocultar sugerencias" : "Ver sugerencias de procedimientos"}
              </button>
              {showSocioSuggestions ? (
                <div className="mt-4">
                  <RiskProcedureSuggestions
                    clienteId={clienteId}
                    areas={criticalAreas}
                    controlTests={strategy.control_tests ?? []}
                    substantiveTests={strategy.substantive_tests ?? []}
                  />
                </div>
              ) : null}
            </div>
          </section>
        ) : null}
      </div>

      <footer className="mt-8 border-t border-slate-200 pt-8 flex flex-col gap-4 md:flex-row md:justify-between md:items-center text-[10px] font-bold text-slate-400 tracking-widest uppercase">
        <div>Socio AI Risk Engine v2.4.0</div>
        <div className="flex flex-wrap gap-5 md:gap-8">
          <a className="hover:text-[#041627] transition-colors" href={`/metodologia/${clienteId}`}>Documentation</a>
          <a className="hover:text-[#041627] transition-colors" href={`/socio-chat/${clienteId}`}>Methodology</a>
          <a className="hover:text-[#041627] transition-colors" href={`/reportes/${clienteId}`}>Audit Standards</a>
        </div>
      </footer>
    </div>
  );
}
