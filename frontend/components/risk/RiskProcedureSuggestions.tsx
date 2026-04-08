import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { createWorkpaperTask, deleteWorkpaperTask } from "../../lib/api/workpapers";
import type { RiskCriticalArea, RiskStrategyTest } from "../../types/risk";

type Procedure = {
  nia: string;
  title: string;
  description: string;
  vinculo: string;
};

type ProcedureCard = Procedure & {
  area_id?: string;
  prioridad?: string;
  scope: "control" | "substantive";
};

type ActionLog = {
  key: string;
  title: string;
  areaName: string;
  status: "created" | "existing";
  at: string;
  taskId?: string;
};

type Props = {
  clienteId: string;
  areas: RiskCriticalArea[];
  controlTests?: RiskStrategyTest[];
  substantiveTests?: RiskStrategyTest[];
};

function buildProcedures(areas: RiskCriticalArea[]): Procedure[] {
  const joined = areas.map((a) => a.area_nombre.toLowerCase()).join(" ");

  const list: Procedure[] = [];
  if (joined.includes("ingreso") || joined.includes("cobrar") || joined.includes("venta")) {
    list.push({
      nia: "NIA 505",
      title: "Confirmacion Externa de Saldos",
      description:
        "Solicitar confirmaciones directas de los principales saldos y validar diferencias con documentacion soporte.",
      vinculo: "Ingresos / Cuentas por Cobrar",
    });
  }

  if (joined.includes("invent") || joined.includes("existenc")) {
    list.push({
      nia: "NIA 315",
      title: "Prueba de Recorrido (Walkthrough)",
      description:
        "Documentar el flujo completo de compras e inventario para evaluar diseno e implementacion de controles clave.",
      vinculo: "Inventarios",
    });
  }

  if (joined.includes("efectivo") || joined.includes("banco") || joined.includes("tesorer")) {
    list.push({
      nia: "NIA 505",
      title: "Confirmaciones Bancarias y Conciliaciones",
      description:
        "Validar saldos de efectivo con confirmaciones externas y revisar partidas conciliatorias de cierre.",
      vinculo: "Efectivo",
    });
  }

  if (joined.includes("patrimonio") || joined.includes("inversion")) {
    list.push({
      nia: "NIA 540",
      title: "Revision de Estimaciones y Valuaciones",
      description:
        "Evaluar supuestos de valuacion, deterioro y revelaciones en patrimonio e inversiones no corrientes.",
      vinculo: "Patrimonio / Inversiones",
    });
  }

  list.push({
    nia: "NIA 520",
    title: "Procedimientos Analiticos Focalizados",
    description:
      "Contrastar tendencias por periodo y desviaciones no esperadas para identificar riesgo de incorreccion material.",
    vinculo: "Analisis transversal",
  });

  const deduped: Procedure[] = [];
  const seen = new Set<string>();
  for (const p of list) {
    const key = `${p.nia}-${p.title}`;
    if (seen.has(key)) continue;
    seen.add(key);
    deduped.push(p);
  }
  return deduped.slice(0, 3);
}

function inferTargetArea(areas: RiskCriticalArea[], procedure: Procedure): RiskCriticalArea | null {
  const link = procedure.vinculo.toLowerCase();
  if (link.includes("efectivo")) {
    return areas.find((a) => a.area_nombre.toLowerCase().includes("efectivo")) ?? null;
  }
  if (link.includes("cobrar") || link.includes("ingreso")) {
    return (
      areas.find(
        (a) =>
          a.area_nombre.toLowerCase().includes("cobrar") ||
          a.area_nombre.toLowerCase().includes("ingreso"),
      ) ?? null
    );
  }
  if (link.includes("invent")) {
    return areas.find((a) => a.area_nombre.toLowerCase().includes("invent")) ?? null;
  }
  if (link.includes("patrimonio") || link.includes("inversion")) {
    return (
      areas.find(
        (a) =>
          a.area_nombre.toLowerCase().includes("patrimonio") ||
          a.area_nombre.toLowerCase().includes("inversion"),
      ) ?? null
    );
  }
  return areas[0] ?? null;
}

function cardKey(procedure: ProcedureCard): string {
  return `${procedure.scope}|${procedure.nia}|${procedure.title}`;
}

function timeLabel(): string {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function RiskProcedureSuggestions({
  clienteId,
  areas,
  controlTests = [],
  substantiveTests = [],
}: Props) {
  const router = useRouter();
  const procedures = buildProcedures(areas);

  const aiControl: ProcedureCard[] = controlTests.slice(0, 3).map((x) => ({
    nia: x.nia_ref || "NIA",
    title: x.title,
    description: x.description,
    vinculo: x.area_nombre,
    area_id: x.area_id,
    prioridad: x.priority,
    scope: "control",
  }));
  const aiSubstantive: ProcedureCard[] = substantiveTests.slice(0, 3).map((x) => ({
    nia: x.nia_ref || "NIA",
    title: x.title,
    description: x.description,
    vinculo: x.area_nombre,
    area_id: x.area_id,
    prioridad: x.priority,
    scope: "substantive",
  }));
  const fallbackControl: ProcedureCard[] = procedures.slice(0, 3).map((p) => ({
    ...p,
    area_id: "",
    prioridad: "media",
    scope: "control",
  }));
  const fallbackSubstantive: ProcedureCard[] = procedures.slice(0, 3).map((p) => ({
    ...p,
    area_id: "",
    prioridad: "media",
    scope: "substantive",
  }));

  const controlList = aiControl.length ? aiControl : fallbackControl;
  const subList = aiSubstantive.length ? aiSubstantive : fallbackSubstantive;
  const allCards = useMemo(() => [...controlList, ...subList], [controlList, subList]);

  const [savingKey, setSavingKey] = useState<string>("");
  const [batchSaving, setBatchSaving] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<string>("");
  const [addedKeys, setAddedKeys] = useState<string[]>([]);
  const [selectedAreaByKey, setSelectedAreaByKey] = useState<Record<string, string>>({});
  const [autoGoToWorkpapers, setAutoGoToWorkpapers] = useState<boolean>(false);
  const [logs, setLogs] = useState<ActionLog[]>([]);

  useEffect(() => {
    if (!allCards.length) return;
    setSelectedAreaByKey((prev) => {
      const next = { ...prev };
      for (const procedure of allCards) {
        const key = cardKey(procedure);
        if (next[key]) continue;
        const inferred =
          (procedure.area_id ? areas.find((a) => a.area_id === procedure.area_id) ?? null : null) ??
          inferTargetArea(areas, procedure);
        if (inferred?.area_id) next[key] = inferred.area_id;
      }
      return next;
    });
  }, [allCards, areas]);

  async function addProcedure(procedure: ProcedureCard, silent = false): Promise<{
    status: "created" | "existing";
    taskId: string;
  }> {
    const key = cardKey(procedure);
    const chosenAreaId = selectedAreaByKey[key] || procedure.area_id || "";
    const targetArea =
      (chosenAreaId ? areas.find((a) => a.area_id === chosenAreaId) ?? null : null) ??
      inferTargetArea(areas, procedure);

    if (!targetArea) {
      throw new Error("No hay areas de riesgo para vincular este procedimiento.");
    }

    setSavingKey(key);
    if (!silent) setFeedback("");

    const result = await createWorkpaperTask(clienteId, {
      area_code: targetArea.area_id,
      area_name: targetArea.area_nombre,
      title: procedure.title,
      nia_ref: procedure.nia,
      prioridad: (procedure.prioridad || targetArea.nivel || "media").toLowerCase(),
      required: true,
      evidence_note: procedure.description,
    });

    setAddedKeys((prev) => (prev.includes(key) ? prev : [...prev, key]));
    const taskId = result.task?.id || "";
    setLogs((prev) => {
      const next: ActionLog[] = [
        {
          key,
          title: procedure.title,
          areaName: targetArea.area_nombre,
          status: result.created ? "created" : "existing",
          at: timeLabel(),
          taskId,
        },
        ...prev,
      ];
      return next.slice(0, 5);
    });

    if (!silent) {
      setFeedback(
        result.created
          ? `Procedimiento agregado en ${targetArea.area_nombre}.`
          : `Ya existia en ${targetArea.area_nombre}.`,
      );
      if (autoGoToWorkpapers) {
        router.push(`/papeles-trabajo/${clienteId}`);
      }
    }

    setSavingKey("");
    return { status: result.created ? "created" : "existing", taskId };
  }

  async function handleAddProcedure(procedure: ProcedureCard): Promise<void> {
    try {
      await addProcedure(procedure);
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : "No se pudo crear el procedimiento.");
      setSavingKey("");
    }
  }

  async function handleAddAll(scope: "control" | "substantive"): Promise<void> {
    const list = scope === "control" ? controlList : subList;
    const pending = list.filter((p) => !addedKeys.includes(cardKey(p)));
    if (!pending.length) {
      setFeedback(`No hay procedimientos ${scope === "control" ? "de control" : "sustantivos"} pendientes.`);
      return;
    }

    setBatchSaving(true);
    setFeedback("");

    let created = 0;
    let existing = 0;
    let failed = 0;

    for (const procedure of pending) {
      try {
        const result = await addProcedure(procedure, true);
        if (result.status === "created") created += 1;
        else existing += 1;
      } catch {
        failed += 1;
      }
    }

    setBatchSaving(false);
    setSavingKey("");
    setFeedback(
      `Carga masiva (${scope === "control" ? "control" : "sustantiva"}): ${created} creados, ${existing} existentes, ${failed} fallidos.`,
    );
  }

  const totalCount = allCards.length;
  const addedCount = allCards.filter((p) => addedKeys.includes(cardKey(p))).length;

  async function handleUndo(log: ActionLog): Promise<void> {
    if (log.status !== "created" || !log.taskId) {
      setFeedback("Solo se puede deshacer tareas creadas en esta sesion.");
      return;
    }
    try {
      await deleteWorkpaperTask(clienteId, log.taskId);
      setAddedKeys((prev) => prev.filter((k) => k !== log.key));
      setLogs((prev) => prev.filter((item) => !(item.key === log.key && item.at === log.at)));
      setFeedback(`Deshecho: ${log.title} removido de Papeles de Trabajo.`);
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : "No se pudo deshacer la accion.");
    }
  }

  return (
    <section className="col-span-12 lg:col-span-7 bg-[#f1f4f6] p-8 rounded-xl">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex items-center space-x-3">
          <span
            className="inline-flex items-center justify-center h-8 w-8 rounded-full bg-[#001919] text-[#a5eff0] text-xs font-bold"
            aria-hidden="true"
          >
            AI
          </span>
          <h2 className="font-headline text-2xl text-[#041627] font-semibold">Socio AI - Sugerencia de Procedimientos</h2>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="px-2 py-1 rounded-full border border-[#041627]/20 bg-white text-slate-600">
            Agregados {addedCount}/{totalCount}
          </span>
          <button
            type="button"
            onClick={() => router.push(`/papeles-trabajo/${clienteId}`)}
            className="px-3 py-1.5 rounded-lg border border-[#041627]/20 bg-white text-slate-700 hover:bg-slate-50"
          >
            Ver en Papeles
          </button>
        </div>
      </div>

      <div className="mb-6 flex items-center gap-2 text-xs text-slate-600">
        <input
          id="auto-go-workpapers"
          type="checkbox"
          checked={autoGoToWorkpapers}
          onChange={(e) => setAutoGoToWorkpapers(e.target.checked)}
          className="h-4 w-4 rounded border-slate-300"
        />
        <label htmlFor="auto-go-workpapers">Ir a Papeles automaticamente al agregar</label>
      </div>

      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="font-headline text-xl text-[#041627]">Pruebas sugeridas (Control)</h3>
          <button
            type="button"
            onClick={() => void handleAddAll("control")}
            disabled={batchSaving}
            className="px-3 py-1.5 rounded-lg border border-[#041627]/20 bg-white text-xs text-slate-700 disabled:opacity-60"
          >
            {batchSaving ? "Agregando..." : "Agregar todos (control)"}
          </button>
        </div>

        {controlList.map((procedure) => {
          const key = cardKey(procedure);
          const isAdded = addedKeys.includes(key);
          return (
            <div key={key} className="bg-white p-6 rounded-xl shadow-sm border border-slate-200/50">
              <div className="flex justify-between items-start mb-4 gap-3">
                <div className="bg-[#001919]/5 px-3 py-1 rounded-full border border-[#001919]/10">
                  <span className="text-[#001919] font-bold text-xs uppercase tracking-wider">{procedure.nia}</span>
                </div>
                <button
                  className="text-slate-400 hover:text-[#041627] transition-colors disabled:opacity-50"
                  type="button"
                  aria-label="Agregar procedimiento"
                  onClick={() => void handleAddProcedure(procedure)}
                  disabled={batchSaving || isAdded || savingKey === key}
                >
                  <span className="inline-flex h-6 px-2 items-center justify-center rounded-full border border-current text-xs">
                    {isAdded ? "Agregado" : savingKey === key ? "..." : "+"}
                  </span>
                </button>
              </div>
              <h5 className="font-bold text-slate-900 mb-2">{procedure.title}</h5>
              <p className="text-sm text-slate-600 mb-4">{procedure.description}</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 items-end">
                <div className="flex items-center space-x-2 text-[10px] font-bold text-[#001919] uppercase tracking-widest">
                  <span className="inline-flex h-4 w-4 items-center justify-center rounded-full bg-[#001919] text-white text-[10px]">?</span>
                  <span>Vinculado a: {procedure.vinculo}</span>
                </div>
                <label className="text-[10px] uppercase tracking-[0.1em] text-slate-500 font-bold">
                  Area destino
                  <select
                    value={selectedAreaByKey[key] || ""}
                    onChange={(e) =>
                      setSelectedAreaByKey((prev) => ({
                        ...prev,
                        [key]: e.target.value,
                      }))
                    }
                    className="mt-1 ghost-input w-full"
                  >
                    {areas.map((area) => (
                      <option key={area.area_id} value={area.area_id}>
                        {area.area_id} - {area.area_nombre}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-8 pt-6 border-t border-slate-200/60">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-headline text-xl text-[#041627]">Pruebas sugeridas (Sustantivas)</h3>
          <button
            type="button"
            onClick={() => void handleAddAll("substantive")}
            disabled={batchSaving}
            className="px-3 py-1.5 rounded-lg border border-[#041627]/20 bg-white text-xs text-slate-700 disabled:opacity-60"
          >
            {batchSaving ? "Agregando..." : "Agregar todos (sustantivas)"}
          </button>
        </div>

        <div className="space-y-6">
          {subList.map((procedure) => {
            const key = cardKey(procedure);
            const isAdded = addedKeys.includes(key);
            return (
              <div key={key} className="bg-white p-6 rounded-xl shadow-sm border border-slate-200/50">
                <div className="flex justify-between items-start mb-4 gap-3">
                  <div className="bg-[#041627]/5 px-3 py-1 rounded-full border border-[#041627]/10">
                    <span className="text-[#041627] font-bold text-xs uppercase tracking-wider">{procedure.nia}</span>
                  </div>
                  <button
                    className="text-slate-400 hover:text-[#041627] transition-colors disabled:opacity-50"
                    type="button"
                    aria-label="Agregar procedimiento sustantivo"
                    onClick={() => void handleAddProcedure(procedure)}
                    disabled={batchSaving || isAdded || savingKey === key}
                  >
                    <span className="inline-flex h-6 px-2 items-center justify-center rounded-full border border-current text-xs">
                      {isAdded ? "Agregado" : savingKey === key ? "..." : "+"}
                    </span>
                  </button>
                </div>
                <h5 className="font-bold text-slate-900 mb-2">{procedure.title}</h5>
                <p className="text-sm text-slate-600 mb-4">{procedure.description}</p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 items-end">
                  <div className="flex items-center space-x-2 text-[10px] font-bold text-[#001919] uppercase tracking-widest">
                    <span className="inline-flex h-4 w-4 items-center justify-center rounded-full bg-[#041627] text-white text-[10px]">?</span>
                    <span>Vinculado a: {procedure.vinculo}</span>
                  </div>
                  <label className="text-[10px] uppercase tracking-[0.1em] text-slate-500 font-bold">
                    Area destino
                    <select
                      value={selectedAreaByKey[key] || ""}
                      onChange={(e) =>
                        setSelectedAreaByKey((prev) => ({
                          ...prev,
                          [key]: e.target.value,
                        }))
                      }
                      className="mt-1 ghost-input w-full"
                    >
                      {areas.map((area) => (
                        <option key={area.area_id} value={area.area_id}>
                          {area.area_id} - {area.area_nombre}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {feedback ? (
        <div className="mt-4 flex items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700">
          <span>{feedback}</span>
          <button
            type="button"
            onClick={() => router.push(`/papeles-trabajo/${clienteId}`)}
            className="px-2 py-1 rounded border border-[#041627]/20 text-slate-700"
          >
            Ver en Papeles
          </button>
        </div>
      ) : null}

      {logs.length ? (
        <div className="mt-4 rounded-lg border border-slate-200 bg-white p-3">
          <p className="text-[10px] uppercase tracking-[0.12em] text-slate-500 font-bold mb-2">Ultimos agregados</p>
          <div className="space-y-1 text-xs text-slate-600">
            {logs.map((log) => (
              <div key={`${log.key}-${log.at}`} className="flex items-center justify-between gap-3">
                <p>
                  {log.at} - {log.title} - {log.areaName} ({log.status === "created" ? "creado" : "ya existia"})
                </p>
                {log.status === "created" && log.taskId ? (
                  <button
                    type="button"
                    onClick={() => void handleUndo(log)}
                    className="px-2 py-1 rounded border border-rose-300 text-rose-700 bg-rose-50"
                  >
                    Deshacer
                  </button>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
