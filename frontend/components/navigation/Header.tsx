"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { getClientes, type ClienteOption } from "../../lib/api/clientes";
import { useAuditContext } from "../../lib/hooks/useAuditContext";
import { useWorkflow } from "../../lib/hooks/useWorkflow";
import ClientSwitcher from "./ClientSwitcher";

function resolveClienteName(clienteId: string, clientes: ClienteOption[]): string {
  const found = clientes.find((c) => c.cliente_id === clienteId);
  return found?.nombre ?? (clienteId || "Cliente");
}

export default function Header() {
  const router = useRouter();
  const { clienteId, moduleLabel } = useAuditContext();
  const [clientes, setClientes] = useState<ClienteOption[]>([]);
  const { data: workflow } = useWorkflow(clienteId);

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

  function handleLogout(): void {
    localStorage.removeItem("socio_token");
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
        </div>

        <div className="flex items-center gap-3 md:gap-4">
          <ClientSwitcher clienteId={clienteId} />
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
