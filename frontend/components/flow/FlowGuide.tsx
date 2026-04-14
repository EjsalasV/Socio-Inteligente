"use client";

import Link from "next/link";
import { useState } from "react";

import type { DashboardData } from "../../types/dashboard";

type StepStatus = "done" | "next" | "pending";

interface FlowStep {
  num: number;
  label: string;
  description: string;
  href: string;
  status: StepStatus;
  cta: string;
}

function buildSteps(data: DashboardData, clienteId: string): FlowStep[] {
  const tbLoaded = data.tb_stage !== "sin_saldos";
  const materialidadDefined = data.materialidad_global > 0;
  const perfilOk = !!data.nombre_cliente && materialidadDefined;
  const hasAreas = data.top_areas.some((a) => a.con_saldo);
  const workStarted = data.progreso_auditoria > 0;

  const raw: Omit<FlowStep, "status">[] = [
    {
      num: 1,
      label: "Configura el Perfil",
      description: "Nombre legal, sector, marco NIIF y materialidad estimada.",
      href: `/perfil/${clienteId}`,
      cta: perfilOk ? "Ver perfil" : "Completar",
    },
    {
      num: 2,
      label: "Carga el Trial Balance",
      description: "Sube el TB para estratificar áreas por riesgo automáticamente.",
      href: `/trial-balance/${clienteId}`,
      cta: tbLoaded ? "Ver TB" : "Cargar TB",
    },
    {
      num: 3,
      label: "Revisa el Risk Engine",
      description: "Valida el score de riesgo por área y ajusta la estrategia.",
      href: `/risk-engine/${clienteId}`,
      cta: "Ir a Risk Engine",
    },
    {
      num: 4,
      label: "Analiza los Índices Financieros",
      description: "Identifica señales de riesgo: liquidez, solvencia, rentabilidad.",
      href: `/estados-financieros/${clienteId}`,
      cta: "Ver índices",
    },
    {
      num: 5,
      label: "Gestiona Papeles de Trabajo",
      description: "Crea el programa de trabajo y asigna tareas al equipo.",
      href: `/papeles-trabajo/${clienteId}`,
      cta: workStarted ? "Ver avance" : "Iniciar",
    },
    {
      num: 6,
      label: "Ejecuta por Área",
      description: "Lead Schedule, briefing AI y hallazgos cuenta por cuenta.",
      href: `/areas/${clienteId}`,
      cta: "Ir a áreas",
    },
    {
      num: 7,
      label: "Consulta al Socio AI",
      description: "Pregunta criterio NIA/NIIF en cualquier momento del encargo.",
      href: `/socio-chat/${clienteId}`,
      cta: "Abrir chat",
    },
    {
      num: 8,
      label: "Emite el Informe",
      description: "Vincula evidencia y genera el PDF del informe final.",
      href: `/reportes/${clienteId}`,
      cta: "Ver reportes",
    },
  ];

  // Determinar qué pasos están "done" basándose en datos disponibles
  const dataDrivenDone: Record<number, boolean | null> = {
    1: perfilOk,
    2: tbLoaded,
    3: hasAreas ? null : false,   // no podemos confirmar que fue revisado
    4: null,
    5: workStarted,
    6: null,
    7: null,
    8: null,
  };

  // Encontrar el primer paso incompleto confirmado
  const firstIncomplete = raw.find((s) => dataDrivenDone[s.num] === false);

  return raw.map((s) => {
    const isDone = dataDrivenDone[s.num] === true;
    const isNext = s === firstIncomplete;
    const status: StepStatus = isDone ? "done" : isNext ? "next" : "pending";
    return { ...s, status };
  });
}

type Props = {
  data: DashboardData;
  clienteId: string;
};

export default function FlowGuide({ data, clienteId }: Props) {
  const [collapsed, setCollapsed] = useState(false);
  const steps = buildSteps(data, clienteId);
  const doneCount = steps.filter((s) => s.status === "done").length;
  const nextStep = steps.find((s) => s.status === "next");

  return (
    <section className="bg-white rounded-xl border border-slate-200/50 shadow-sm overflow-hidden">
      {/* Header */}
      <button
        type="button"
        onClick={() => setCollapsed((v) => !v)}
        className="w-full px-7 py-5 bg-gradient-to-r from-[#041627] to-[#163550] text-white flex items-center justify-between"
      >
        <div className="text-left">
          <p className="text-[10px] uppercase tracking-[0.2em] text-[#a5eff0] font-bold">Guía de flujo</p>
          <h3 className="font-headline text-xl mt-0.5">Cómo usar el sistema — paso a paso</h3>
        </div>
        <div className="flex items-center gap-4 shrink-0">
          <div className="text-right">
            <p className="text-xs text-slate-300">{doneCount} / {steps.length} completados</p>
            {nextStep && (
              <p className="text-xs text-[#a5eff0] font-semibold mt-0.5">
                Siguiente: {nextStep.label}
              </p>
            )}
          </div>
          <span className="material-symbols-outlined text-slate-300 text-xl">
            {collapsed ? "expand_more" : "expand_less"}
          </span>
        </div>
      </button>

      {/* Steps grid */}
      {!collapsed && (
        <div className="p-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {steps.map((step) => {
              const isDone = step.status === "done";
              const isNext = step.status === "next";
              return (
                <div
                  key={step.num}
                  className={`relative rounded-xl border p-4 flex flex-col ${
                    isDone
                      ? "bg-emerald-50 border-emerald-200"
                      : isNext
                      ? "bg-[#041627]/5 border-[#041627]/25 ring-1 ring-[#041627]/15"
                      : "bg-slate-50 border-slate-100"
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span
                      className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold shrink-0 ${
                        isDone
                          ? "bg-emerald-600 text-white"
                          : isNext
                          ? "bg-[#041627] text-white"
                          : "bg-slate-200 text-slate-500"
                      }`}
                    >
                      {isDone ? "✓" : step.num}
                    </span>
                    {isNext && (
                      <span className="text-[9px] uppercase tracking-[0.12em] font-bold text-[#041627]/70">
                        Siguiente
                      </span>
                    )}
                  </div>

                  <p
                    className={`font-semibold text-sm mb-1 ${
                      isDone ? "text-emerald-800" : "text-[#041627]"
                    }`}
                  >
                    {step.label}
                  </p>
                  <p className="text-[11px] text-slate-500 leading-relaxed flex-1 mb-3">
                    {step.description}
                  </p>

                  <Link
                    href={step.href}
                    className={`inline-block px-3 py-1.5 rounded-lg text-[11px] font-bold uppercase tracking-[0.08em] text-center ${
                      isDone
                        ? "bg-emerald-100 text-emerald-800 hover:bg-emerald-200"
                        : isNext
                        ? "bg-[#041627] text-white hover:bg-[#163550]"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                    }`}
                  >
                    {step.cta}
                  </Link>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </section>
  );
}
