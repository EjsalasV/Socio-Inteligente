"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { getClientes, type ClienteOption } from "../../lib/api/clientes";
import { useAuditContext } from "../../lib/hooks/useAuditContext";
import { useLearningRole, type LearningRole } from "../../lib/hooks/useLearningRole";
import { useWorkflow } from "../../lib/hooks/useWorkflow";
import { useUserPreferences } from "../providers/UserPreferencesProvider";
import { useTour } from "../tour/TourProvider";
import ClientSwitcher from "./ClientSwitcher";

function resolveClienteName(clienteId: string, clientes: ClienteOption[]): string {
  const found = clientes.find((c) => c.cliente_id === clienteId);
  return found?.nombre ?? (clienteId || "Cliente");
}

export default function Header() {
  const router = useRouter();
  const { clienteId, moduleLabel, moduleKey } = useAuditContext();
  const [clientes, setClientes] = useState<ClienteOption[]>([]);
  const { data: workflow } = useWorkflow(clienteId);
  const { activeModule, startTour, resetTours } = useTour();
  const { role, setRole } = useLearningRole();
  const { session } = useUserPreferences();

  useEffect(() => {
    let active = true;
    async function load(): Promise<void> {
      try {
        const response = await getClientes();
        if (!active) return;
        setClientes(response);
      } catch {
        if (!active) return;
        setClientes([]);
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, []);

  const clienteName = useMemo(() => resolveClienteName(clienteId, clientes), [clienteId, clientes]);
  const phase = workflow?.current_phase ?? "planificacion";
  const phaseIndex = phase === "informe" ? 3 : phase === "ejecucion" ? 2 : 1;
  const canManageUsers = useMemo(() => {
    const profileRole = String(session?.role || "").toLowerCase();
    return profileRole === "admin" || profileRole === "socio";
  }, [session?.role]);
  const moduleHint = useMemo(() => {
    const hints: Record<string, string> = {
      perfil: "Completa marco, materialidad y responsable para habilitar un flujo consistente.",
      dashboard: "Revisa KPIs y ranking para decidir donde iniciar trabajo de campo.",
      "trial-balance": "Confirma variaciones relevantes y marca cuentas para pruebas.",
      "risk-engine": "Prioriza areas altas y agrega procedimientos recomendados a papeles.",
      areas: "Genera briefing, ejecuta pruebas y documenta hallazgos con evidencia.",
      "papeles-trabajo": "Cierra tareas requeridas y valida gates antes de informe.",
      reportes: "Emite borrador/final cuando PLAN y EXEC esten en estado OK.",
      "socio-chat": "Haz preguntas tecnicas y exporta criterio a hallazgos o papeles.",
      "client-memory": "Consolida documentos e historial para mantener contexto del cliente.",
      "estados-financieros": "Analiza variaciones contra materialidad y alertas de integridad.",
    };
    const base = hints[moduleKey] ?? "Avanza por fases para mantener trazabilidad del encargo.";
    if (role === "junior") return `${base} Si algo no cuadra, pide soporte y registra evidencia minima.`;
    if (role === "socio") return `${base} Prioriza juicio de emision, riesgo material y comunicacion con gobierno corporativo.`;
    if (role === "senior") return `${base} Prioriza decisiones de riesgo, materialidad y cierre ejecutivo.`;
    return `${base} Documenta criterio y evidencia por area.`;
  }, [moduleKey, role]);

  function handleLogout(): void {
    localStorage.removeItem("socio_token");
    window.dispatchEvent(new Event("socio-auth-changed"));
    router.push("/");
  }

  return (
    <header className="sticky top-0 z-20 bg-white/92 backdrop-blur-sm px-4 md:px-8 py-4 border-b border-[#041627]/10">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="font-body text-xs uppercase tracking-[0.16em] text-slate-500">Ruta</p>
          <h1 className="font-headline text-3xl text-navy-900 leading-tight">
            {clienteName} <span className="text-slate-400">/</span> {moduleLabel}
          </h1>
          <div className="mt-2 flex items-center gap-2 text-[10px] uppercase tracking-[0.13em] text-slate-500">
            <span className={phaseIndex >= 1 ? "text-emerald-700 font-semibold" : ""}>Planificación</span>
            <span>•</span>
            <span className={phaseIndex >= 2 ? "text-emerald-700 font-semibold" : ""}>Ejecución</span>
            <span>•</span>
            <span className={phaseIndex >= 3 ? "text-emerald-700 font-semibold" : ""}>Informe</span>
          </div>
          <p className="mt-2 text-xs text-slate-600 max-w-2xl">{moduleHint}</p>
        </div>

        <div className="flex items-center gap-3 md:gap-4">
          <div data-tour="header-client-switcher">
            <ClientSwitcher clienteId={clienteId} />
          </div>
          <label className="sovereign-card !p-1.5 !px-2 flex items-center gap-2">
            <span className="text-[10px] uppercase tracking-[0.12em] text-slate-500 font-semibold">Nivel</span>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as LearningRole)}
              className="bg-transparent text-[11px] text-slate-700 outline-none"
            >
              <option value="junior">Junior</option>
              <option value="semi">Semi Senior</option>
              <option value="senior">Senior</option>
              <option value="socio">Socio</option>
            </select>
          </label>
          <button
            type="button"
            onClick={() => startTour()}
            disabled={!activeModule}
            data-tour="btn-ver-tutorial"
            className="sovereign-card !p-2 !px-3 text-[11px] font-body uppercase tracking-[0.14em] text-slate-500 hover:text-[#041627] disabled:opacity-55 disabled:cursor-not-allowed"
          >
            Ver tutorial
          </button>
          <button
            type="button"
            onClick={resetTours}
            className="sovereign-card !p-2 !px-3 text-[11px] font-body uppercase tracking-[0.14em] text-slate-500 hover:text-[#041627]"
          >
            Reiniciar tutoriales
          </button>
          {canManageUsers ? (
            <button
              type="button"
              onClick={() => router.push("/admin")}
              className="sovereign-card !p-2 !px-3 text-[11px] font-body uppercase tracking-[0.14em] text-slate-500 hover:text-[#041627]"
            >
              Admin
            </button>
          ) : null}
          <div className="sovereign-card !p-2 !px-3 text-[11px] font-body uppercase tracking-[0.14em] text-slate-500">
            Ctrl + K
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="sovereign-card !p-2 !px-3 text-[11px] font-body uppercase tracking-[0.14em] text-slate-500 hover:text-[#041627]"
          >
            Cerrar sesion
          </button>
        </div>
      </div>
    </header>
  );
}
