"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuditContext } from "../../lib/hooks/useAuditContext";

type NavItem = {
  id: string;
  key:
    | "dashboard"
    | "risk-engine"
    | "trial-balance"
    | "estados-financieros"
    | "areas"
    | "papeles-trabajo"
    | "perfil"
    | "reportes"
    | "clientes"
    | "socio-chat"
    | "client-memory";
  label: string;
  icon: string;
  iconLabel: string;
  href: string;
};

function itemClass(active: boolean): string {
  if (active) {
    return "bg-white text-navy-900 font-semibold shadow-sm border border-[#041627]/10";
  }
  return "text-slate-600 hover:bg-white/80";
}

export default function Sidebar() {
  const router = useRouter();
  const { clienteId, moduleKey, pathname } = useAuditContext();
  const [openMobile, setOpenMobile] = useState<boolean>(false);

  const baseCliente = clienteId || "cliente_demo";

  const items = useMemo<NavItem[]>(
    () => [
      { id: "perfil", key: "perfil", label: "Perfil Cliente", icon: "PF", iconLabel: "Perfil", href: `/perfil/${baseCliente}` },
      { id: "clientes", key: "clientes", label: "Clientes", icon: "CL", iconLabel: "Clientes", href: "/clientes" },
      { id: "dashboard", key: "dashboard", label: "Dashboard", icon: "DB", iconLabel: "Dashboard", href: `/dashboard/${baseCliente}` },
      { id: "risk-engine", key: "risk-engine", label: "Risk Engine", icon: "RK", iconLabel: "Risk", href: `/risk-engine/${baseCliente}` },
      { id: "trial-balance", key: "trial-balance", label: "Trial Balance", icon: "TB", iconLabel: "Trial Balance", href: `/trial-balance/${baseCliente}` },
      {
        id: "estados-financieros",
        key: "estados-financieros",
        label: "Estados Financieros",
        icon: "EF",
        iconLabel: "Estados Financieros",
        href: `/estados-financieros/${baseCliente}`,
      },
      { id: "areas", key: "areas", label: "Workspace Áreas", icon: "WA", iconLabel: "Workspace Areas", href: `/areas/${baseCliente}/130` },
      {
        id: "papeles-trabajo",
        key: "papeles-trabajo",
        label: "Papeles de Trabajo",
        icon: "PT",
        iconLabel: "Papeles de Trabajo",
        href: `/papeles-trabajo/${baseCliente}`,
      },
      { id: "socio-chat", key: "socio-chat", label: "Socio Chat", icon: "SC", iconLabel: "Socio Chat", href: `/socio-chat/${baseCliente}` },
      { id: "client-memory", key: "client-memory", label: "Client Memory", icon: "CM", iconLabel: "Client Memory", href: `/client-memory/${baseCliente}` },
      { id: "reportes", key: "reportes", label: "Reportes", icon: "RP", iconLabel: "Reportes", href: `/reportes/${baseCliente}` },
    ],
    [baseCliente],
  );

  return (
    <>
      <button
        type="button"
        className="lg:hidden fixed left-4 top-4 z-50 sovereign-card !p-2"
        onClick={() => setOpenMobile((v) => !v)}
        aria-label="Abrir navegacion"
      >
        <span className="inline-flex h-6 w-6 items-center justify-center rounded-full border border-[#041627]/20 text-xs font-bold">≡</span>
      </button>

      <aside
        className={`fixed inset-y-0 left-0 z-40 w-72 bg-[#edf3fa] border-r border-[#041627]/8 transition-transform duration-200 ${openMobile ? "translate-x-0" : "-translate-x-full"} lg:translate-x-0`}
      >
        <div className="h-full p-5 flex flex-col min-h-0">
          <div className="mb-8 pt-2 px-2">
            <h2 className="font-headline text-3xl text-navy-900">Socio AI</h2>
            <p className="font-body text-[11px] tracking-[0.16em] uppercase text-slate-500 mt-1">Sovereign Intelligence</p>
          </div>

          <nav className="space-y-2 flex-1 overflow-y-auto pr-1 min-h-0">
            {items.map((item) => {
              const active =
                item.key === "areas"
                  ? pathname.startsWith(`/areas/${baseCliente}`)
                  : item.key === "reportes"
                    ? pathname.startsWith(`/reportes/${baseCliente}`)
                    : item.key === "socio-chat"
                      ? pathname.startsWith(`/socio-chat/${baseCliente}`)
                      : item.key === "client-memory"
                        ? pathname.startsWith(`/client-memory/${baseCliente}`)
                        : item.key === "papeles-trabajo"
                          ? pathname.startsWith(`/papeles-trabajo/${baseCliente}`)
                    : item.key === "clientes"
                      ? pathname.startsWith("/clientes") || pathname.startsWith("/onboarding/")
                    : moduleKey === item.key;

              return (
                <Link
                  key={item.id}
                  href={item.href}
                  prefetch
                  className={`flex items-center gap-3 rounded-editorial px-4 py-3 transition-colors ${itemClass(active)}`}
                  onClick={() => setOpenMobile(false)}
                >
                  <span
                    className="inline-flex h-6 min-w-6 items-center justify-center rounded-md border border-[#041627]/20 bg-white/70 px-1 text-[10px] font-bold text-[#041627]"
                    aria-label={item.iconLabel}
                    title={item.iconLabel}
                  >
                    {item.icon}
                  </span>
                  <span className="font-body text-sm">{item.label}</span>
                </Link>
              );
            })}
          </nav>

          <div className="pt-5 border-t border-black/5 mt-4">
            <button
              type="button"
              onClick={() => {
                localStorage.removeItem("socio_token");
                router.push("/");
              }}
            className="w-full flex items-center gap-3 rounded-editorial px-4 py-3 text-slate-600 hover:bg-white/75 transition-colors"
          >
              <span className="inline-flex h-6 w-6 items-center justify-center rounded-full border border-[#041627]/20 text-xs">↩</span>
              <span className="font-body text-sm">Volver al login</span>
            </button>
          </div>
        </div>
      </aside>

      {openMobile ? (
        <button
          type="button"
          className="lg:hidden fixed inset-0 z-30 bg-navy-900/20"
          aria-label="Cerrar navegacion"
          onClick={() => setOpenMobile(false)}
        />
      ) : null}
    </>
  );
}
