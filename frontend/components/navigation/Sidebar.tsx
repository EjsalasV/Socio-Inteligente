"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { useAuditContext } from "../../lib/hooks/useAuditContext";

type NavItem = {
  id: string;
  key: "dashboard" | "risk-engine" | "areas" | "reportes";
  label: string;
  icon: string;
  href: string;
};

function itemClass(active: boolean): string {
  if (active) {
    return "bg-white text-navy-900 font-semibold shadow-sm";
  }
  return "text-slate-600 hover:bg-white/75";
}

export default function Sidebar() {
  const { clienteId, moduleKey, pathname } = useAuditContext();
  const [openMobile, setOpenMobile] = useState<boolean>(false);

  const baseCliente = clienteId || "cliente_demo";

  const items = useMemo<NavItem[]>(
    () => [
      { id: "dashboard", key: "dashboard", label: "Dashboard", icon: "dashboard", href: `/dashboard/${baseCliente}` },
      { id: "risk-engine", key: "risk-engine", label: "Risk Engine", icon: "security", href: `/risk-engine/${baseCliente}` },
      { id: "areas-130", key: "areas", label: "130 - Cuentas por Cobrar", icon: "payments", href: `/areas/${baseCliente}/130` },
      {
        id: "areas-140",
        key: "areas",
        label: "140 - Efectivo",
        icon: "account_balance_wallet",
        href: `/areas/${baseCliente}/140`,
      },
      { id: "reportes", key: "reportes", label: "Reportes", icon: "description", href: `/dashboard/${baseCliente}#reportes` },
    ],
    [baseCliente],
  );

  return (
    <>
      <button
        type="button"
        className="lg:hidden fixed left-4 top-4 z-50 sovereign-card !p-2"
        onClick={() => setOpenMobile((v) => !v)}
        aria-label="Abrir navegación"
      >
        <span className="material-symbols-outlined">menu</span>
      </button>

      <aside
        className={`fixed inset-y-0 left-0 z-40 w-72 bg-[#f1f4f6] transition-transform duration-200 ${openMobile ? "translate-x-0" : "-translate-x-full"} lg:translate-x-0`}
      >
        <div className="h-full p-5 flex flex-col">
          <div className="mb-8 pt-2 px-2">
            <h2 className="font-headline text-3xl text-navy-900">Socio AI</h2>
            <p className="font-body text-[11px] tracking-[0.16em] uppercase text-slate-500 mt-1">Sovereign Intelligence</p>
          </div>

          <nav className="space-y-2">
            {items.map((item) => {
              const active = item.key === "areas" ? pathname.startsWith(item.href) : moduleKey === item.key;
              return (
                <Link
                  key={item.id}
                  href={item.href}
                  prefetch
                  className={`flex items-center gap-3 rounded-editorial px-4 py-3 transition-colors ${itemClass(active)}`}
                  onClick={() => setOpenMobile(false)}
                >
                  <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
                  <span className="font-body text-sm">{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </aside>

      {openMobile ? (
        <button
          type="button"
          className="lg:hidden fixed inset-0 z-30 bg-navy-900/20"
          aria-label="Cerrar navegación"
          onClick={() => setOpenMobile(false)}
        />
      ) : null}
    </>
  );
}
