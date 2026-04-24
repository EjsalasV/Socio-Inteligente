"use client";

import Link from "next/link";
import { useCallback, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { logoutSession } from "../../lib/auth-session";
import { useAuditContext } from "../../lib/hooks/useAuditContext";
import { useUserPreferences } from "../providers/UserPreferencesProvider";
import { useTour } from "../tour/TourProvider";

type NavItem = {
  id: string;
  key:
    | "dashboard"
    | "risk-engine"
    | "trial-balance"
    | "mayor"
    | "estados-financieros"
    | "areas"
    | "papeles-trabajo"
    | "perfil"
    | "reportes"
    | "clientes"
    | "admin"
    | "socio-chat"
    | "client-memory"
    | "biblioteca"
    | "procedimientos";
  label: string;
  icon: string;
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
  const { stopTour } = useTour();
  const { clienteId, moduleKey, pathname } = useAuditContext();
  const { session } = useUserPreferences();
  const [openMobile, setOpenMobile] = useState<boolean>(false);
  const canManageUsers = useMemo(() => {
    const role = String(session?.role || "").toLowerCase();
    return role === "admin" || role === "socio";
  }, [session?.role]);

  const baseCliente = clienteId || "";
  const withCliente = useCallback((route: string): string => {
    // Only use clienteId if available, otherwise keep the route without cliente parameter
    // This prevents unexpected redirects when context is temporarily lost
    return baseCliente ? `/${route}/${baseCliente}` : `/${route}`;
  }, [baseCliente]);

  const items = useMemo<NavItem[]>(
    () => [
      { id: "perfil", key: "perfil", label: "Perfil Cliente", icon: "business_center", href: withCliente("perfil") },
      { id: "clientes", key: "clientes", label: "Clientes", icon: "groups", href: "/clientes" },
      ...(canManageUsers
        ? [{ id: "admin", key: "admin", label: "Admin", icon: "admin_panel_settings", href: "/admin" } as NavItem]
        : []),
      { id: "dashboard", key: "dashboard", label: "Dashboard", icon: "dashboard", href: withCliente("dashboard") },
      { id: "risk-engine", key: "risk-engine", label: "Risk Engine", icon: "security", href: withCliente("risk-engine") },
      { id: "trial-balance", key: "trial-balance", label: "Trial Balance", icon: "account_balance_wallet", href: withCliente("trial-balance") },
      { id: "mayor", key: "mayor", label: "Mayor Contable", icon: "table_view", href: withCliente("mayor") },
      {
        id: "estados-financieros",
        key: "estados-financieros",
        label: "Índices Financieros",
        icon: "monitoring",
        href: withCliente("estados-financieros"),
      },
      { id: "areas", key: "areas", label: "Workspace Áreas", icon: "receipt_long", href: withCliente("areas") },
      {
        id: "papeles-trabajo",
        key: "papeles-trabajo",
        label: "Papeles de Trabajo",
        icon: "task_alt",
        href: withCliente("papeles-trabajo"),
      },
      { id: "socio-chat", key: "socio-chat", label: "Socio Chat", icon: "forum", href: withCliente("socio-chat") },
      { id: "client-memory", key: "client-memory", label: "Client Memory", icon: "folder_shared", href: withCliente("client-memory") },
      { id: "biblioteca", key: "biblioteca", label: "Biblioteca", icon: "menu_book", href: "/biblioteca" },
      { id: "procedimientos", key: "procedimientos", label: "Procedimientos", icon: "fact_check", href: "/procedimientos" },
      { id: "reportes", key: "reportes", label: "Reportes", icon: "description", href: withCliente("reportes") },
    ],
    [canManageUsers, withCliente],
  );

  return (
    <>
      <button
        type="button"
        className="lg:hidden fixed left-4 top-4 z-50 sovereign-card !p-2 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded min-h-[44px] min-w-[44px] flex items-center justify-center"
        onClick={() => setOpenMobile((v) => !v)}
        aria-label="Abrir navegacion"
        aria-expanded={openMobile}
        aria-controls="sidebar-nav"
      >
        <span className="material-symbols-outlined" aria-hidden="true">menu</span>
      </button>

      <aside
        id="sidebar-nav"
        className={`fixed inset-y-0 left-0 z-40 w-72 bg-[#edf3fa] border-r border-[#041627]/8 transition-transform duration-200 ${openMobile ? "translate-x-0" : "-translate-x-full"} lg:translate-x-0`}
        role="navigation"
        aria-label="Navegación principal"
      >
        <div className="h-full p-5 flex flex-col min-h-0">
          <div className="mb-8 pt-2 px-2">
            <h2 className="font-headline text-3xl text-navy-900">Socio AI</h2>
            <p className="font-body text-[11px] tracking-[0.16em] uppercase text-slate-500 mt-1">Sovereign Intelligence</p>
          </div>

          <nav className="space-y-2 flex-1 overflow-y-auto pr-1 min-h-0" role="menubar">
            {items.map((item) => {
              const active =
                item.key === "biblioteca" || item.key === "procedimientos"
                  ? pathname.startsWith(`/${item.key}`)
                  : !baseCliente || item.key === "clientes"
                  ? pathname.startsWith("/clientes") || pathname.startsWith("/onboarding/")
                  : item.key === "areas"
                  ? pathname.startsWith(`/areas/${baseCliente}`)
                  : item.key === "reportes"
                    ? pathname.startsWith(`/reportes/${baseCliente}`)
                    : item.key === "admin"
                      ? pathname.startsWith("/admin")
                    : item.key === "socio-chat"
                      ? pathname.startsWith(`/socio-chat/${baseCliente}`)
                      : item.key === "client-memory"
                        ? pathname.startsWith(`/client-memory/${baseCliente}`)
                        : item.key === "papeles-trabajo"
                          ? pathname.startsWith(`/papeles-trabajo/${baseCliente}`)
                        : moduleKey === item.key;

              return (
                <Link
                  key={item.id}
                  href={item.href}
                  prefetch
                  data-tour={
                    item.key === "clientes"
                      ? "sidebar-clientes"
                      : item.key === "perfil"
                        ? "sidebar-perfil"
                        : item.key === "dashboard"
                          ? "sidebar-dashboard"
                          : item.key === "risk-engine"
                            ? "sidebar-risk-engine"
                            : item.key === "trial-balance"
                              ? "sidebar-trial-balance"
                              : item.key === "mayor"
                                ? "sidebar-mayor"
                              : item.key === "estados-financieros"
                                ? "sidebar-estados-financieros"
                                : item.key === "areas"
                                  ? "sidebar-areas"
                                  : item.key === "admin"
                                    ? "sidebar-admin"
                                  : item.key === "papeles-trabajo"
                                    ? "sidebar-papeles-trabajo"
                                    : item.key === "reportes"
                                      ? "sidebar-reportes"
                                      : item.key === "socio-chat"
                                        ? "sidebar-socio-chat"
                                        : item.key === "client-memory"
                                          ? "sidebar-client-memory"
                                          : item.key === "biblioteca"
                                          ? "sidebar-biblioteca"
                                          : item.key === "procedimientos"
                                            ? "sidebar-procedimientos"
                                          : undefined
                  }
                  className={`flex items-center gap-3 rounded-editorial px-4 py-3 transition-colors min-h-[44px] focus:outline-none focus:ring-2 focus:ring-blue-500 ${itemClass(active)}`}
                  onClick={() => {
                    stopTour();
                    setOpenMobile(false);
                  }}
                  role="menuitem"
                  aria-current={active ? "page" : undefined}
                >
                  <span className="material-symbols-outlined text-[20px]" aria-hidden="true">{item.icon}</span>
                  <span className="font-body text-sm">{item.label}</span>
                </Link>
              );
            })}
          </nav>

          <div className="pt-5 border-t border-black/5 mt-4">
            <button
              type="button"
              onClick={() => {
                void logoutSession().finally(() => router.push("/"));
              }}
              className="w-full flex items-center gap-3 rounded-editorial px-4 py-3 text-slate-600 hover:bg-white/75 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]"
              aria-label="Cerrar sesión y volver al login"
            >
              <span className="material-symbols-outlined text-[20px]" aria-hidden="true">logout</span>
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
