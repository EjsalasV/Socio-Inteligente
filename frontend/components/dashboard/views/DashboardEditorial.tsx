"use client";

import Link from "next/link";

import { formatMoney } from "../../../lib/formatters";
import type { DashboardData } from "../../../types/dashboard";

type Props = {
  data: DashboardData;
  clienteId: string;
  roleLabel: string;
};

function phaseLabel(data: DashboardData): string {
  const phase = (data.workflow_phase || data.fase_actual || "").toLowerCase();
  if (phase.includes("inform") || phase.includes("cierre")) return "Informe";
  if (phase.includes("ejec") || phase.includes("visita")) return "Ejecucion";
  if (phase.includes("plan")) return "Planificacion";
  return "En curso";
}

function riskLabel(raw: string | null | undefined): string {
  const value = String(raw || "medio").toLowerCase();
  if (value === "alto" || value === "critico") return "Alto";
  if (value === "bajo") return "Bajo";
  return "Medio";
}

function buildChecklist(data: DashboardData): Array<{ title: string; note: string; done: boolean }> {
  const topAreas = (data.top_areas ?? []).filter((area) => area.con_saldo).slice(0, 3);
  const gates = (data.workflow_gates ?? []).slice(0, 3);

  if (gates.length) {
    return gates.map((gate) => ({
      title: gate.title || gate.code,
      note: gate.detail || gate.code,
      done: gate.status === "ok",
    }));
  }

  return topAreas.map((area, index) => ({
    title: `${index + 1}. ${area.codigo} - ${area.nombre}`,
    note: `Saldo ${formatMoney(area.saldo_total, "USD", 0)} · Prioridad ${area.prioridad.toUpperCase()}`,
    done: false,
  }));
}

function buildTimeline(data: DashboardData, nextStep: string): Array<{ title: string; detail: string; time: string; tone: "teal" | "sand" | "ink" }> {
  const phase = phaseLabel(data);
  return [
    { title: "Sesion iniciada", detail: "Acceso al encargo y contexto cargado.", time: "Hoy, 09:14", tone: "teal" },
    { title: "Cliente seleccionado", detail: data.nombre_cliente || "Cliente activo", time: "Hoy, 09:15", tone: "sand" },
    { title: `Ruta en ${phase.toLowerCase()}`, detail: `Fase actual del trabajo: ${phase}`, time: "Hoy, 09:16", tone: "ink" },
    { title: "Siguiente paso", detail: nextStep, time: "Pendiente", tone: "sand" },
  ];
}

export default function DashboardEditorial({ data, clienteId, roleLabel }: Props) {
  const progreso = Math.max(0, Math.min(100, data.progreso_auditoria ?? 0));
  const mat = data.materialidad_ejecucion > 0 ? data.materialidad_ejecucion : data.materialidad_global;
  const checklist = buildChecklist(data);
  const topAreas = [...(data.top_areas ?? [])].filter((area) => area.con_saldo).sort((a, b) => b.score_riesgo - a.score_riesgo);
  const topArea = topAreas[0];
  const phase = phaseLabel(data);
  const risk = riskLabel(data.riesgo_global);

  const nextStep = topArea
    ? `Completar trabajo en ${topArea.codigo} - ${topArea.nombre}`
    : "Completar Perfil del Cliente";

  const timeline = buildTimeline(data, nextStep);

  return (
    <div className="space-y-6 pb-8 sovereign-page-transition">
      <section className="sovereign-card overflow-hidden border-[#041627]/10 bg-[#faf6ee]">
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1.2fr)_280px] lg:items-center">
          <div className="space-y-5">
            <div className="flex flex-wrap items-center gap-2 text-[10px] uppercase tracking-[0.22em] text-slate-500">
              <span>Ruta</span>
              <span className="text-slate-400">•</span>
              <span>{data.nombre_cliente || "Cliente"}</span>
              <span className="text-slate-400">•</span>
              <span>Dashboard</span>
            </div>

            <div className="space-y-3">
              <h2 data-tour="dashboard-title" className="font-headline text-4xl md:text-5xl leading-[0.95] text-[#0b2030]">
                {data.nombre_cliente || "Cliente"} / Dashboard
              </h2>
              <p className="max-w-2xl text-sm md:text-base leading-relaxed text-slate-600">
                Una vista editorial, limpia y premium para revisar el encargo de un vistazo:
                estado, prioridades y el siguiente paso sin saturar la pantalla.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-2 rounded-full border border-[#041627]/10 bg-white px-3 py-2 text-[11px] uppercase tracking-[0.16em] text-slate-600">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                En linea
              </span>
              <span className="inline-flex items-center rounded-full border border-[#041627]/10 bg-white px-3 py-2 text-[11px] uppercase tracking-[0.16em] text-slate-600">
                1 en equipo
              </span>
              <span className="inline-flex items-center rounded-full border border-[#041627]/10 bg-white px-3 py-2 text-[11px] uppercase tracking-[0.16em] text-slate-600">
                Nivel {roleLabel}
              </span>
              <span className="inline-flex items-center rounded-full border border-[#041627]/10 bg-white px-3 py-2 text-[11px] uppercase tracking-[0.16em] text-slate-600">
                Fase {phase}
              </span>
            </div>
          </div>

          <div className="flex justify-start lg:justify-end">
            <div className="relative flex h-56 w-56 items-center justify-center rounded-full border border-[#041627]/10 bg-[radial-gradient(circle_at_center,rgba(4,22,39,0.03),rgba(255,255,255,0.85)_62%)]">
              <div className="absolute inset-5 rounded-full border border-[#041627]/10" />
              <div className="absolute inset-10 rounded-full border border-dashed border-[#8b7960]/25" />
              <div className="flex h-24 w-24 items-center justify-center rounded-full bg-[#0b2030] text-[#a5eff0] shadow-[0_16px_30px_rgba(11,32,48,0.18)]">
                <span className="material-symbols-outlined text-[38px]" aria-hidden="true">
                  verified
                </span>
              </div>
              <div className="absolute left-4 top-5 rounded-full border border-[#8b7960]/20 bg-[#f7efe0] px-3 py-1 text-[10px] uppercase tracking-[0.18em] text-[#8b7960]">
                Auditoria inteligente
              </div>
              <div className="absolute bottom-5 right-4 rounded-full border border-[#041627]/10 bg-white px-3 py-1 text-[10px] uppercase tracking-[0.18em] text-slate-500">
                Socio AI
              </div>
            </div>
          </div>
        </div>
      </section>

      <section
        data-tour="dashboard-kpis"
        className="grid gap-6 lg:grid-cols-[minmax(0,1.55fr)_minmax(300px,0.9fr)]"
      >
        <article className="sovereign-card">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="text-[10px] uppercase tracking-[0.18em] text-[#8b7960]">Resumen del encargo</p>
              <h3 className="mt-1 font-headline text-3xl text-[#0b2030]">Progreso onboarding</h3>
              <p className="mt-2 max-w-xl text-sm leading-relaxed text-slate-600">
                Mantiene una sola accion principal, con jerarquia clara y mucho aire para que se lea rapido.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link
                href={`/perfil/${clienteId}`}
                className="inline-flex items-center justify-center rounded-editorial bg-[#0b2030] px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-[#102d42]"
              >
                Ver perfil
              </Link>
              <Link
                href={`/configuracion/${clienteId}`}
                className="inline-flex items-center justify-center rounded-editorial border border-[#041627]/10 bg-white px-4 py-3 text-sm font-semibold text-[#0b2030] transition-colors hover:bg-[#f6f2e9]"
              >
                Abrir ajustes
              </Link>
            </div>
          </div>

          <div className="mt-6 grid gap-5 md:grid-cols-[minmax(0,1fr)_240px] md:items-end">
            <div>
              <div className="flex items-end gap-3">
                <span className="font-headline text-5xl text-[#0b2030]">{Math.round(progreso)}%</span>
                <span className="pb-1 text-sm text-slate-500">completado</span>
              </div>
              <div className="mt-4 h-3 overflow-hidden rounded-full bg-[#efe7d7]">
                <div className="h-full rounded-full bg-[#0b2030]" style={{ width: `${progreso}%` }} />
              </div>
              <p className="mt-4 text-sm text-slate-600">
                Siguiente accion: <span className="font-semibold text-[#0b2030]">{nextStep}</span>
              </p>
            </div>

            <div className="rounded-editorial border border-[#041627]/10 bg-white/80 p-4">
              <div className="flex items-center justify-between text-xs uppercase tracking-[0.16em] text-slate-500">
                <span>Estado</span>
                <span>Hoy</span>
              </div>
              <div className="mt-4 space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Riesgo global</span>
                  <span className="font-semibold text-[#0b2030]">{risk}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Materialidad</span>
                  <span className="font-semibold text-[#0b2030]">
                    {mat > 0 ? formatMoney(mat, "USD", 0) : "N/D"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">TB</span>
                  <span className="font-semibold text-[#0b2030]">{data.tb_stage || "Sin definir"}</span>
                </div>
              </div>
            </div>
          </div>
        </article>

        <article className="sovereign-card" data-tour="dashboard-risk-ranking">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[10px] uppercase tracking-[0.18em] text-[#8b7960]">Llamado rapido</p>
              <h3 className="mt-1 font-headline text-2xl text-[#0b2030]">Guia del sistema</h3>
            </div>
            <span className="rounded-full border border-[#041627]/10 bg-[#f7efe0] px-3 py-1 text-[10px] uppercase tracking-[0.16em] text-[#8b7960]">
              0/6
            </span>
          </div>

          <div className="mt-5 space-y-3">
            {checklist.map((item, index) => (
              <div
                key={`${item.title}-${index}`}
                className="flex items-start gap-3 rounded-editorial border border-[#041627]/8 bg-[#fbfaf6] px-3 py-3"
              >
                <span
                  className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
                    item.done ? "bg-emerald-100 text-emerald-800" : "bg-[#efe7d7] text-[#8b7960]"
                  }`}
                >
                  {String(index + 1).padStart(2, "0")}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-[#0b2030]">{item.title}</p>
                  <p className="mt-1 text-xs leading-relaxed text-slate-500">{item.note}</p>
                </div>
                <span className="material-symbols-outlined mt-0.5 text-[18px] text-slate-400" aria-hidden="true">
                  chevron_right
                </span>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="grid gap-6 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
        <article className="sovereign-card">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-[10px] uppercase tracking-[0.18em] text-[#8b7960]">Llamado rapido</p>
              <h3 className="mt-1 font-headline text-2xl text-[#0b2030]">Linea de tiempo</h3>
            </div>
            <Link
              href={`/dashboard/${clienteId}`}
              className="text-sm font-semibold text-[#0b2030] transition-colors hover:text-[#163550]"
            >
              Ver todo
            </Link>
          </div>

          <div className="mt-5 space-y-4">
            {timeline.map((item, index) => (
              <div key={`${item.title}-${index}`} className="flex gap-4">
                <div className="flex flex-col items-center">
                  <span
                    className={`mt-1 h-3.5 w-3.5 rounded-full ${
                      item.tone === "teal" ? "bg-[#0f7c80]" : item.tone === "sand" ? "bg-[#c7a56a]" : "bg-[#0b2030]"
                    }`}
                  />
                  {index < timeline.length - 1 ? <span className="mt-2 h-full w-px grow bg-[#e8dfd0]" /> : null}
                </div>
                <div className="pb-1">
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                    <h4 className="text-sm font-semibold text-[#0b2030]">{item.title}</h4>
                    <span className="text-[11px] uppercase tracking-[0.14em] text-slate-400">{item.time}</span>
                  </div>
                  <p className="mt-1 text-sm leading-relaxed text-slate-600">{item.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="sovereign-card">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-[10px] uppercase tracking-[0.18em] text-[#8b7960]">Foco</p>
              <h3 className="mt-1 font-headline text-2xl text-[#0b2030]">Area prioritaria</h3>
            </div>
            <span className="rounded-full border border-[#041627]/10 bg-white px-3 py-1 text-[10px] uppercase tracking-[0.16em] text-slate-500">
              {risk}
            </span>
          </div>

          {topArea ? (
            <div className="mt-5 rounded-editorial border border-[#041627]/10 bg-[#fbfaf6] p-4">
              <p className="text-[10px] uppercase tracking-[0.18em] text-[#8b7960]">Mayor exposicion</p>
              <p className="mt-2 font-headline text-2xl text-[#0b2030]">
                {topArea.codigo} / {topArea.nombre}
              </p>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                {formatMoney(topArea.saldo_total, "USD", 0)} · Prioridad {topArea.prioridad.toUpperCase()}
              </p>
              <div className="mt-4 h-2 overflow-hidden rounded-full bg-[#efe7d7]">
                <div className="h-full rounded-full bg-[#0f7c80]" style={{ width: `${Math.max(18, Math.min(100, topArea.score_riesgo))}%` }} />
              </div>
            </div>
          ) : (
            <div className="mt-5 rounded-editorial border border-dashed border-[#041627]/10 bg-[#fbfaf6] p-4 text-sm text-slate-500">
              Aun no hay areas con saldo suficiente para destacar.
            </div>
          )}

          <div className="mt-5 space-y-3">
            {topAreas.slice(1, 4).map((area) => (
              <div key={`${area.codigo}-${area.nombre}`} className="flex items-center justify-between rounded-editorial border border-[#041627]/8 bg-white px-3 py-3">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-[#0b2030]">{area.codigo}</p>
                  <p className="truncate text-xs text-slate-500">{area.nombre}</p>
                </div>
                <span className="text-xs font-semibold text-[#8b7960]">
                  {formatMoney(area.saldo_total, "USD", 0)}
                </span>
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}
