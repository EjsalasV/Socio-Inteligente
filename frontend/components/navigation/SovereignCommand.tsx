"use client";

import { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import { getClientes, type ClienteOption } from "../../lib/api/clientes";
import { getRiskEngineData } from "../../lib/api/risk";

type CommandItem = {
  id: string;
  label: string;
  subtitle: string;
  kind: "command" | "cliente" | "area";
  action: () => void;
};

const BASE_AREAS = [
  "Activos Fijos",
  "Ingresos",
  "Inventarios",
  "Cuentas por Cobrar",
  "Patrimonio",
];

function parseClienteFromPath(pathname: string): string | null {
  const chunks = pathname.split("/").filter(Boolean);
  if (chunks.length < 2) return null;
  if (
    chunks[0] === "dashboard" ||
    chunks[0] === "risk-engine" ||
    chunks[0] === "trial-balance" ||
    chunks[0] === "estados-financieros" ||
    chunks[0] === "areas" ||
    chunks[0] === "perfil"
  ) {
    return chunks[1] ?? null;
  }
  return null;
}

export default function SovereignCommand() {
  const router = useRouter();
  const pathname = usePathname();

  const [open, setOpen] = useState<boolean>(false);
  const [query, setQuery] = useState<string>("");
  const [clientes, setClientes] = useState<ClienteOption[]>([]);
  const [areas, setAreas] = useState<string[]>(BASE_AREAS);

  const currentClienteId = parseClienteFromPath(pathname);

  useEffect(() => {
    let active = true;

    async function hydrate(): Promise<void> {
      try {
        const list = await getClientes();
        if (!active) return;
        setClientes(list);
      } catch {
        if (!active) return;
        setClientes([]);
      }

      if (!currentClienteId) return;
      try {
        const risk = await getRiskEngineData(currentClienteId);
        if (!active) return;
        const dynamicAreas = risk.areas_criticas.map((x) => x.area_nombre).filter(Boolean);
        setAreas(Array.from(new Set([...BASE_AREAS, ...dynamicAreas])));
      } catch {
        if (!active) return;
      }
    }

    void hydrate();
    return () => {
      active = false;
    };
  }, [currentClienteId]);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent): void {
      const isShortcut = (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k";
      if (!isShortcut) return;
      event.preventDefault();
      setOpen((prev) => !prev);
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const items = useMemo<CommandItem[]>(() => {
    const commands: CommandItem[] = [
      {
        id: "cmd-dashboard",
        label: "Ver Dashboard",
        subtitle: "Ir al panel ejecutivo",
        kind: "command",
        action: () => router.push(currentClienteId ? `/dashboard/${currentClienteId}` : "/"),
      },
      {
        id: "cmd-profile",
        label: "Configurar Perfil",
        subtitle: "Abrir ficha de configuración del cliente",
        kind: "command",
        action: () => router.push(currentClienteId ? `/perfil/${currentClienteId}` : "/"),
      },
      {
        id: "cmd-risk",
        label: "Ver Risk Engine",
        subtitle: "Abrir matriz de riesgo editorial",
        kind: "command",
        action: () => router.push(currentClienteId ? `/risk-engine/${currentClienteId}` : "/"),
      },
      {
        id: "cmd-trial-balance",
        label: "Ver Trial Balance",
        subtitle: "Abrir balance de comprobación",
        kind: "command",
        action: () => router.push(currentClienteId ? `/trial-balance/${currentClienteId}` : "/"),
      },
      {
        id: "cmd-estados-financieros",
        label: "Ver Índices Financieros",
        subtitle: "Liquidez, solvencia y rentabilidad",
        kind: "command",
        action: () => router.push(currentClienteId ? `/estados-financieros/${currentClienteId}` : "/"),
      },
    ];

    const clienteItems = clientes.map<CommandItem>((cliente) => ({
      id: `cliente-${cliente.cliente_id}`,
      label: cliente.nombre,
      subtitle: `Cliente · ${cliente.cliente_id}`,
      kind: "cliente",
      action: () => router.push(`/dashboard/${cliente.cliente_id}`),
    }));

    const areaItems = areas.map<CommandItem>((area, idx) => ({
      id: `area-${idx}-${area}`,
      label: area,
      subtitle: "Área de riesgo",
      kind: "area",
      action: () => {
        if (pathname.startsWith("/risk-engine/")) {
          const node = document.getElementById("riesgos-criticos");
          node?.scrollIntoView({ behavior: "smooth", block: "start" });
          setOpen(false);
          return;
        }
        router.push(currentClienteId ? `/risk-engine/${currentClienteId}` : "/");
      },
    }));

    return [...commands, ...clienteItems, ...areaItems];
  }, [areas, clientes, currentClienteId, pathname, router]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter((item) => item.label.toLowerCase().includes(q) || item.subtitle.toLowerCase().includes(q));
  }, [items, query]);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-5 right-5 z-40 sovereign-card !p-3 !rounded-full text-xs font-body font-bold tracking-[0.14em] uppercase text-slate-600"
      >
        Ctrl + K
      </button>

      {open ? (
        <div className="fixed inset-0 z-50 bg-navy-900/25 backdrop-blur-sm p-4 md:p-10" onClick={() => setOpen(false)}>
          <div
            className="max-w-2xl mx-auto bg-white rounded-editorial shadow-[0_24px_60px_rgba(4,22,39,0.22)] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-4 border-b border-slate-100">
              <input
                autoFocus
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Buscar cliente, área o comando..."
                className="ghost-input w-full"
              />
            </div>
            <div className="max-h-[420px] overflow-y-auto p-2">
              {filtered.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className="w-full text-left p-3 rounded-lg hover:bg-[#f1f4f6] transition-colors"
                  onClick={() => {
                    item.action();
                    setOpen(false);
                    setQuery("");
                  }}
                >
                  <div className="font-headline text-xl text-navy-900 leading-tight">{item.label}</div>
                  <div className="font-body text-xs uppercase tracking-[0.12em] text-slate-500 mt-1">{item.subtitle}</div>
                </button>
              ))}
              {filtered.length === 0 ? (
                <p className="p-4 text-sm text-slate-500 font-body">Sin coincidencias para tu búsqueda.</p>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
