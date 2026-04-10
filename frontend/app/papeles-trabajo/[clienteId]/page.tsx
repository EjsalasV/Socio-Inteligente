"use client";

import { useMemo, useState } from "react";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import ContextualHelp from "../../../components/help/ContextualHelp";
import { advanceWorkflow } from "../../../lib/api/workflow";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import { useWorkpapers } from "../../../lib/hooks/useWorkpapers";

type EvidenceDraftMap = Record<string, string>;

function gateColor(status: "ok" | "blocked"): string {
  return status === "ok" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-red-50 text-red-700 border-red-200";
}

function priorityColor(priority: string): string {
  const normalized = priority.toLowerCase();
  if (normalized === "alta") return "bg-red-50 text-red-700 border-red-200";
  if (normalized === "media") return "bg-amber-50 text-amber-700 border-amber-200";
  return "bg-slate-50 text-slate-600 border-slate-200";
}

export default function PapelesTrabajoPage() {
  const { clienteId } = useAuditContext();
  const { data, isLoading, isLoadingMore, hasMore, error, savingTaskId, updateTask, loadMore } = useWorkpapers(clienteId);
  const [evidenceDrafts, setEvidenceDrafts] = useState<EvidenceDraftMap>({});
  const [workflowMsg, setWorkflowMsg] = useState<string>("");
  const [areaFilter, setAreaFilter] = useState<string>("todas");
  const [taskQuery, setTaskQuery] = useState<string>("");

  const groupedTasks = useMemo(() => {
    if (!data) return [];
    const groups = new Map<string, { areaCode: string; areaName: string; tasks: typeof data.tasks }>();
    for (const task of data.tasks) {
      const key = `${task.area_code}-${task.area_name}`;
      const existing = groups.get(key);
      if (existing) {
        existing.tasks.push(task);
      } else {
        groups.set(key, {
          areaCode: task.area_code,
          areaName: task.area_name,
          tasks: [task],
        });
      }
    }
    return Array.from(groups.values()).sort((a, b) => a.areaCode.localeCompare(b.areaCode));
  }, [data]);

  const areaFilterOptions = useMemo(
    () => groupedTasks.map((group) => ({ value: group.areaCode, label: `${group.areaCode} · ${group.areaName}` })),
    [groupedTasks],
  );

  const filteredGroups = useMemo(() => {
    const query = taskQuery.trim().toLowerCase();
    return groupedTasks
      .filter((group) => areaFilter === "todas" || group.areaCode === areaFilter)
      .map((group) => {
        if (!query) return group;
        const tasks = group.tasks.filter((task) => {
          const haystack = `${task.title} ${task.nia_ref} ${task.evidence_note || ""}`.toLowerCase();
          return haystack.includes(query);
        });
        return { ...group, tasks };
      })
      .filter((group) => group.tasks.length > 0);
  }, [areaFilter, groupedTasks, taskQuery]);

  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorMessage message={error} />;
  if (!data) return <ErrorMessage message="No hay plan de papeles de trabajo para este cliente." />;

  return (
    <div className="pt-4 pb-10 space-y-8 max-w-[1500px]">
      <section className="rounded-editorial p-7 text-white border border-[#041627]/20 bg-gradient-to-br from-[#041627] to-[#1a2b3c]">
        <p className="text-xs uppercase tracking-[0.2em] text-[#a5eff0] font-body">Control de Calidad</p>
        <h1 data-tour="papeles-title" className="font-headline text-5xl text-white mt-2">Papeles de Trabajo y Quality Gates</h1>
        <p className="font-body text-slate-200 mt-3 leading-relaxed text-base">
          Cliente: <span className="font-semibold text-white">{data.cliente_id}</span> ·
          Avance requerido: <span className="font-semibold text-white"> {data.completion_pct.toFixed(1)}%</span>
        </p>
      </section>

      <ContextualHelp
        title="Ayuda del modulo Papeles de Trabajo"
        items={[
          {
            label: "Quality gates",
            byRole: {
              junior:
                "Si un gate esta bloqueado, sigue el detalle paso a paso hasta dejarlo en OK.",
              semi:
                "Si un gate esta bloqueado, revisa su detalle para saber que falta exactamente.",
              senior:
                "Usa gates como control de calidad para decidir avance de fase y cierre tecnico.",
              socio:
                "Usa gates para decidir readiness de emision y nivel de riesgo residual aceptable.",
            },
          },
          {
            label: "Tareas por area",
            byRole: {
              junior:
                "No marques una tarea sin evidencia escrita: que hiciste, que encontraste y conclusion.",
              semi:
                "Marca procedimientos completos y adjunta evidencia breve y concreta.",
              senior:
                "Verifica suficiencia de evidencia y consistencia entre tareas, hallazgos y conclusion.",
              socio:
                "Exige evidencia suficiente en areas materiales y evita documentacion irrelevante.",
            },
          },
          {
            label: "Cambio de fase",
            byRole: {
              junior:
                "Avanza de fase solo cuando no haya pendientes criticos en tu area.",
              semi:
                "Solo avanza cuando cobertura y papeles requeridos esten suficientemente completos.",
              senior:
                "Autoriza cambio de fase unicamente con cobertura y calidad documental adecuadas.",
              socio:
                "Aprueba avance solo si el riesgo residual esta controlado para sostener la opinion.",
            },
          },
        ]}
      />

      <section data-tour="papeles-gates" className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {data.gates.map((gate) => (
          <article key={gate.code} className={`sovereign-card border ${gateColor(gate.status)}`}>
            <div className="flex items-center justify-between">
              <p className="text-[10px] uppercase tracking-[0.14em] font-bold">{gate.code}</p>
              <span
                className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
                  gate.status === "ok" ? "bg-emerald-700 text-white" : "bg-red-700 text-white"
                }`}
                aria-hidden="true"
              >
                {gate.status === "ok" ? "✓" : "!"}
              </span>
            </div>
            <h3 className="font-headline text-2xl mt-2">{gate.title}</h3>
            <p className="text-sm mt-3">{gate.detail}</p>
          </article>
        ))}
      </section>

      <section data-tour="papeles-avance" className="sovereign-card">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <p className="text-[10px] uppercase tracking-[0.15em] text-slate-500 font-bold">Avance de Ejecucion</p>
            <h2 className="font-headline text-3xl text-[#041627] mt-1">{data.completion_pct.toFixed(1)}%</h2>
          </div>
          <div className="w-full md:w-[380px] h-3 bg-[#e5e9eb] rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-[#041627] to-[#1a2b3c] transition-all"
              style={{ width: `${Math.max(0, Math.min(100, data.completion_pct))}%` }}
            />
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={async () => {
                try {
                  const next = await advanceWorkflow(clienteId, "ejecucion");
                  setWorkflowMsg(`Fase actual: ${next.current_phase.toUpperCase()}.`);
                } catch (err) {
                  setWorkflowMsg(err instanceof Error ? err.message : "No se pudo avanzar a ejecucion.");
                }
              }}
              className="px-3 py-2 rounded-xl text-xs font-semibold border border-[#041627]/15 text-[#041627] hover:bg-[#f1f4f6]"
            >
              Pasar a Ejecucion
            </button>
            <button
              type="button"
              onClick={async () => {
                try {
                  const next = await advanceWorkflow(clienteId, "informe");
                  setWorkflowMsg(`Fase actual: ${next.current_phase.toUpperCase()}.`);
                } catch (err) {
                  setWorkflowMsg(err instanceof Error ? err.message : "No se pudo avanzar a informe.");
                }
              }}
              className="px-3 py-2 rounded-xl text-xs font-semibold bg-[#041627] text-white hover:opacity-90"
            >
              Pasar a Informe
            </button>
          </div>
        </div>
        {workflowMsg ? <p className="mt-3 text-xs text-slate-600">{workflowMsg}</p> : null}
      </section>

      <section className="sovereign-card">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <label className="flex flex-col gap-2">
            <span className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">Filtrar por área L/S</span>
            <select
              value={areaFilter}
              onChange={(event) => setAreaFilter(event.target.value)}
              className="ghost-input"
            >
              <option value="todas">Todas las áreas</option>
              {areaFilterOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-2 md:col-span-2">
            <span className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">Buscar tarea o NIA</span>
            <input
              value={taskQuery}
              onChange={(event) => setTaskQuery(event.target.value)}
              placeholder="Ej. circularización, NIA 505, provisión..."
              className="ghost-input"
            />
          </label>
        </div>
        <p className="mt-3 text-xs text-slate-500">
          Mostrando {data.tasks.length} de {data.tasks_total} tareas filtradas ({data.tasks_total_all} totales).
        </p>
      </section>

      <section data-tour="papeles-tareas" className="space-y-6">
        {filteredGroups.map((group) => (
          <article key={`${group.areaCode}-${group.areaName}`} className="sovereign-card">
            <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
              <h3 className="font-headline text-3xl text-[#041627]">
                {group.areaCode} · {group.areaName}
              </h3>
              <span className="text-xs uppercase tracking-[0.14em] text-slate-500 font-bold">
                {group.tasks.filter((t) => t.done).length}/{group.tasks.length} completados
              </span>
            </div>

            <div className="space-y-4">
              {group.tasks.map((task) => {
                const evidenceValue = evidenceDrafts[task.id] ?? task.evidence_note ?? "";
                return (
                  <div key={task.id} className="rounded-editorial border border-[#041627]/10 p-4 bg-white">
                    <div className="flex items-start justify-between gap-4 flex-wrap">
                      <label className="flex items-start gap-3 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={task.done}
                          onChange={(event) => {
                            void updateTask(task.id, event.target.checked, evidenceValue);
                          }}
                          disabled={savingTaskId === task.id}
                          className="mt-1 h-4 w-4 rounded border-slate-300 text-[#041627] focus:ring-[#041627]"
                        />
                        <span>
                          <span className="block text-sm font-semibold text-[#041627]">{task.title}</span>
                          <span className="block text-xs text-slate-500 mt-1">{task.nia_ref}</span>
                        </span>
                      </label>

                      <span className={`px-2.5 py-1 rounded-full text-[10px] uppercase tracking-[0.12em] font-bold border ${priorityColor(task.prioridad)}`}>
                        {task.prioridad}
                      </span>
                    </div>

                    <div className="mt-4">
                      <label htmlFor={`evidence-${task.id}`} className="text-[11px] uppercase tracking-[0.12em] text-slate-500 font-bold">
                        Evidencia
                      </label>
                      <textarea
                        id={`evidence-${task.id}`}
                        value={evidenceValue}
                        onChange={(event) => {
                          setEvidenceDrafts((prev) => ({ ...prev, [task.id]: event.target.value }));
                        }}
                        onBlur={() => {
                          if (evidenceValue !== (task.evidence_note ?? "")) {
                            void updateTask(task.id, task.done, evidenceValue);
                          }
                        }}
                        placeholder="Soporte del procedimiento, referencia WP, conclusion breve..."
                        className="mt-2 w-full min-h-[74px] rounded-editorial border border-[#041627]/10 bg-[#f8fbff] px-3 py-2 text-sm text-slate-700 outline-none focus:border-[#041627]/35"
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </article>
        ))}
        {filteredGroups.length === 0 ? (
          <article className="sovereign-card text-sm text-slate-600">
            No hay tareas que coincidan con los filtros actuales.
          </article>
        ) : null}
      </section>
      {hasMore ? (
        <section className="flex justify-center">
          <button
            type="button"
            onClick={() => {
              void loadMore();
            }}
            disabled={isLoadingMore}
            className="px-4 py-2 rounded-xl text-sm font-semibold border border-[#041627]/20 text-[#041627] hover:bg-[#f1f4f6] disabled:opacity-50"
          >
            {isLoadingMore ? "Cargando más..." : "Cargar más tareas"}
          </button>
        </section>
      ) : null}
    </div>
  );
}
