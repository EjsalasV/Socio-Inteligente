"use client";

import { formatMoney } from "../../../lib/formatters";
import type { DashboardData } from "../../../types/dashboard";

type Props = { data: DashboardData };

const NIA_TIPS: Record<string, string> = {
  "Planificación": "NIA 300 — Debes documentar tu plan de auditoría antes de ejecutar cualquier prueba.",
  "Ejecución": "NIA 500 — Obtén evidencia suficiente y apropiada para cada afirmación en riesgo.",
  "Informe": "NIA 700 — Revisa que todas las afirmaciones críticas estén cubiertas antes de emitir.",
};

function stepAction(etapa: string, topAreaNombre: string): { accion: string; nia: string; detalle: string }[] {
  if (etapa === "Planificación") {
    return [
      { accion: "Completa el memorando de planeación", nia: "NIA 300", detalle: "Documenta la estrategia de auditoría y los riesgos identificados." },
      { accion: "Define la materialidad de planeación", nia: "NIA 320", detalle: "Establece el umbral a partir del cual un error sería significativo." },
      { accion: "Documenta la matriz de riesgos", nia: "NIA 315", detalle: "Identifica y evalúa los riesgos de incorrección material por área." },
    ];
  }
  if (etapa === "Informe") {
    return [
      { accion: "Verifica cobertura de afirmaciones críticas", nia: "NIA 330", detalle: "Confirma que cada afirmación tiene evidencia suficiente y apropiada." },
      { accion: "Documenta hallazgos y comunicaciones", nia: "NIA 265", detalle: "Reporta deficiencias de control identificadas durante la auditoría." },
      { accion: "Prepara carta de representación", nia: "NIA 580", detalle: "Solicita a la gerencia confirmar por escrito las representaciones clave." },
    ];
  }
  // Ejecución por defecto
  return [
    { accion: `Ejecuta pruebas sustantivas en ${topAreaNombre}`, nia: "NIA 500", detalle: "Esta es el área de mayor riesgo — empieza aquí." },
    { accion: "Realiza procedimientos analíticos", nia: "NIA 520", detalle: "Compara saldos actuales con períodos anteriores y detecta variaciones." },
    { accion: "Documenta tu evidencia en papeles de trabajo", nia: "NIA 230", detalle: "Toda prueba realizada debe quedar documentada con referencia y conclusión." },
  ];
}

export default function DashboardJunior({ data }: Props) {
  const progreso = Math.max(0, Math.min(100, data.progreso_auditoria ?? 0));
  const orderedAreas = [...(data.top_areas ?? [])].filter((a) => a.con_saldo).sort((a, b) => b.score_riesgo - a.score_riesgo);
  const topArea = orderedAreas[0];
  const topNombre = topArea ? `${topArea.codigo} — ${topArea.nombre}` : "No determinada";

  const fase = (data.workflow_phase || data.fase_actual || "").toLowerCase();
  const etapa =
    fase.includes("inform") || fase.includes("cierre") ? "Informe"
    : fase.includes("ejec") || fase.includes("visita") ? "Ejecución"
    : fase.includes("plan") ? "Planificación"
    : "Ejecución";

  const acciones = stepAction(etapa, topNombre);
  const niaTip = NIA_TIPS[etapa] ?? NIA_TIPS["Ejecución"];
  const mat = data.materialidad_ejecucion > 0 ? data.materialidad_ejecucion : data.materialidad_global;

  const riskColor = (p: string) =>
    p.toLowerCase() === "alta" ? "bg-rose-100 text-rose-800 border-rose-200"
    : p.toLowerCase() === "media" ? "bg-amber-100 text-amber-800 border-amber-200"
    : "bg-emerald-100 text-emerald-800 border-emerald-200";

  return (
    <div className="space-y-8 pb-8">

      {/* Header Junior */}
      <section className="rounded-xl p-7 shadow-md text-white bg-gradient-to-br from-[#041627] to-[#0f3460] border border-[#041627]/20">
        <div className="flex items-center gap-3 mb-1">
          <span className="text-xs uppercase tracking-[0.2em] text-[#a5eff0] font-semibold">Vista Junior</span>
          <span className="px-2 py-0.5 rounded-full bg-[#a5eff0]/20 text-[#a5eff0] text-[10px] font-bold uppercase tracking-wider">Guiado</span>
        </div>
        <h2 className="font-headline text-4xl text-white mt-1">¿Qué hago hoy?</h2>
        <p className="text-slate-300 mt-2 text-sm">
          Cliente: <span className="font-semibold text-white">{data.nombre_cliente}</span>
          {" · "}Estás en fase de <span className="font-semibold text-white">{etapa}</span>
        </p>
      </section>

      {/* Tip NIA de la fase actual */}
      <section className="flex items-start gap-4 bg-[#a5eff0]/10 border border-[#a5eff0]/30 rounded-xl p-5">
        <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#041627] text-[#a5eff0] text-xs font-bold mt-0.5">
          NIA
        </span>
        <div>
          <p className="text-xs uppercase tracking-[0.15em] text-[#041627]/60 font-bold mb-1">Qué dice la norma en esta fase</p>
          <p className="text-[#041627] text-sm leading-relaxed">{niaTip}</p>
        </div>
      </section>

      {/* Acciones del día — el corazón de la vista junior */}
      <section className="bg-white rounded-xl p-7 shadow-sm border border-slate-200/50">
        <h3 className="font-headline text-2xl text-[#041627] font-semibold mb-5">Tus próximos pasos</h3>
        <div className="space-y-4">
          {acciones.map((a, i) => (
            <div key={a.nia} className="flex gap-4 p-4 rounded-lg bg-slate-50 border border-slate-100">
              <span className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#041627] text-white text-xs font-bold mt-0.5">
                {i + 1}
              </span>
              <div className="flex-1">
                <div className="flex items-start justify-between gap-2">
                  <p className="font-semibold text-[#041627] text-sm">{a.accion}</p>
                  <span className="shrink-0 px-2 py-0.5 rounded-full bg-[#041627]/10 text-[#041627] text-[10px] font-bold uppercase tracking-wide">
                    {a.nia}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">{a.detalle}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Área prioritaria — dónde enfocar */}
        <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-200/50">
          <h4 className="font-headline text-xl text-[#041627] font-semibold mb-4">Empieza aquí</h4>
          {topArea ? (
            <div className={`p-4 rounded-lg border ${riskColor(topArea.prioridad)}`}>
              <p className="text-[10px] uppercase tracking-wide font-bold mb-1 opacity-70">Área de mayor riesgo</p>
              <p className="font-bold text-sm">{topArea.codigo} — {topArea.nombre}</p>
              <p className="text-xs mt-1 opacity-80">
                Saldo: {formatMoney(topArea.saldo_total, "USD", 0)} · Prioridad: {topArea.prioridad.toUpperCase()}
              </p>
              <p className="text-xs mt-2 opacity-70 leading-relaxed">
                Esta área tiene el mayor puntaje de riesgo en el encargo. Tus pruebas deben ser más extensas aquí.
              </p>
            </div>
          ) : (
            <p className="text-sm text-slate-400">Aún no hay áreas con saldo cargado.</p>
          )}

          {orderedAreas.length > 1 && (
            <div className="mt-4 space-y-2">
              <p className="text-[11px] uppercase tracking-[0.12em] text-slate-500 font-bold">Otras áreas a cubrir</p>
              {orderedAreas.slice(1, 4).map((area) => (
                <div key={`${area.codigo}-${area.nombre}`} className="flex items-center justify-between text-xs py-1.5 border-b border-slate-100 last:border-0">
                  <span className="text-slate-700">{area.codigo} — {area.nombre}</span>
                  <span className={`px-2 py-0.5 rounded-full font-semibold text-[10px] ${riskColor(area.prioridad)}`}>{area.prioridad}</span>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Panel derecho: progreso + materialidad explicada */}
        <div className="space-y-5">

          {/* Progreso visual */}
          <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-200/50">
            <h4 className="font-headline text-xl text-[#041627] font-semibold mb-3">Avance del encargo</h4>
            <div className="flex items-end gap-3 mb-3">
              <span className="font-headline text-4xl text-[#041627] font-semibold">{Math.round(progreso)}%</span>
              <span className="text-sm text-slate-500 pb-1">completado</span>
            </div>
            <div className="h-4 rounded-full bg-slate-100 overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-[#041627] to-[#1a5276] transition-all"
                style={{ width: `${progreso}%` }}
              />
            </div>
            <div className="flex justify-between text-[11px] text-slate-400 mt-2">
              {["Planificación", "Ejecución", "Informe"].map((s) => (
                <span key={s} className={s === etapa ? "font-bold text-[#041627]" : ""}>{s}</span>
              ))}
            </div>
          </section>

          {/* Materialidad explicada en lenguaje simple */}
          <section className="bg-white rounded-xl p-6 shadow-sm border border-slate-200/50">
            <h4 className="font-headline text-xl text-[#041627] font-semibold mb-1">¿Qué es la materialidad?</h4>
            <p className="text-xs text-slate-500 mb-3 leading-relaxed">
              Es el monto mínimo de error que cambiaría la decisión de un usuario de los estados financieros. Si encuentras errores menores a este umbral, no son significativos.
            </p>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Límite de ejecución</span>
                <span className="font-semibold text-[#041627]">{mat > 0 ? formatMoney(mat, "USD", 0) : "No definida"}</span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-slate-500">Trivial (ignora errores menores a)</span>
                <span className="font-semibold text-[#041627]">{data.umbral_trivial > 0 ? formatMoney(data.umbral_trivial, "USD", 0) : "N/D"}</span>
              </div>
            </div>
            <p className="text-[10px] text-slate-400 mt-3">NIA 320 — Materialidad en la planificación y ejecución de auditoría</p>
          </section>

        </div>
      </div>
    </div>
  );
}
