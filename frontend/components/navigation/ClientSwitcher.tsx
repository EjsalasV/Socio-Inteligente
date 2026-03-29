"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { getClientes, type ClienteOption } from "../../lib/api/clientes";
import { useAuditContext } from "../../lib/hooks/useAuditContext";

type Props = {
  clienteId?: string;
};

export default function ClientSwitcher({ clienteId: overrideClienteId }: Props) {
  const router = useRouter();
  const { clienteId, moduleKey } = useAuditContext();
  const currentCliente = overrideClienteId ?? clienteId;

  const [clientes, setClientes] = useState<ClienteOption[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let active = true;

    async function load(): Promise<void> {
      try {
        const list = await getClientes();
        if (!active) return;
        setClientes(list);
      } catch {
        if (!active) return;
        setClientes([]);
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, []);

  const safeValue = useMemo(() => {
    if (clientes.some((c) => c.cliente_id === currentCliente)) return currentCliente;
    return currentCliente;
  }, [currentCliente, clientes]);

  function buildRoute(nextId: string): string {
    if (moduleKey === "risk-engine") return `/risk-engine/${nextId}`;
    if (moduleKey === "trial-balance") return `/trial-balance/${nextId}`;
    if (moduleKey === "estados-financieros") return `/estados-financieros/${nextId}`;
    if (moduleKey === "areas") return `/areas/${nextId}/130`;
    if (moduleKey === "papeles-trabajo") return `/papeles-trabajo/${nextId}`;
    if (moduleKey === "perfil") return `/perfil/${nextId}`;
    if (moduleKey === "socio-chat") return `/socio-chat/${nextId}`;
    if (moduleKey === "client-memory") return `/client-memory/${nextId}`;
    if (moduleKey === "reportes") return `/reportes/${nextId}`;
    return `/dashboard/${nextId}`;
  }

  function handleChange(nextId: string): void {
    if (!nextId || nextId === currentCliente) return;
    router.push(buildRoute(nextId));
  }

  return (
    <div className="flex items-center gap-2">
      <label htmlFor="client-switcher" className="text-xs uppercase tracking-[0.12em] text-slate-500 font-body">
        Cliente
      </label>
      <select
        id="client-switcher"
        value={safeValue}
        onChange={(e) => handleChange(e.target.value)}
        className="ghost-input min-w-[220px] text-sm text-slate-700"
        disabled={loading}
      >
        {loading ? <option value={currentCliente || ""}>Cargando clientes...</option> : null}
        {!loading && clientes.length === 0 ? <option value={currentCliente || ""}>Sin clientes disponibles</option> : null}
        {!loading
          ? clientes.map((cliente) => (
              <option key={cliente.cliente_id} value={cliente.cliente_id}>
                {cliente.nombre}
              </option>
            ))
          : null}
      </select>
    </div>
  );
}
