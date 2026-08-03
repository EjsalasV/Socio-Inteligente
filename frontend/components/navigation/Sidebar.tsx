"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
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
    | "knowledge"
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
    | "procedimientos"
    | "learning-progress"
    | "entity-profile";
  label: string;
  icon: string;
  href: string;
  group: "flujo" | "aprendizaje" | "administracion" | "legacy";
};

// Modo MVP: la navegación muestra el flujo de análisis (clientes → perfil →
// TB/Mayor → dashboard → riesgos → chat) y el pilar de aprendizaje
// (biblioteca normativa y guía de procedimientos por área/rol).
// NEXT_PUBLIC_FULL_PLATFORM=1 restaura la plataforma completa (demos/desarrollo).
const FULL_PLATFORM = process.env.NEXT_PUBLIC_FULL_PLATFORM === "1";
const MVP_KEYS = new Set<NavItem["key"]>([
  "clientes",
  "entity-profile",
  "socio-chat",
  "admin",
  "trial-balance",
  "mayor",
  "biblioteca",
  "procedimientos",
  "learning-progress",
]);

function itemClass(active: boolean, immersive = false): string {
  if (immersive) {
    return active
      ? "bg-white/10 text-white font-semibold border-l-2 border-[#73d5cf]"
      : "text-slate-300 hover:bg-white/[0.06] hover:text-white";
  }
  if (active) {
    return "bg-white text-navy-900 font-semibold shadow-sm border border-[#041627]/10";
  }
  return "text-slate-600 hover:bg-white/80";
}

export default function Sidebar({ immersive = false }: { immersive?: boolean }) {
  const router = useRouter();
  const { stopTour } = useTour();
  const { clienteId, moduleKey, pathname } = useAuditContext();
  const { session } = useUserPreferences();
  const [openMobile, setOpenMobile] = useState<boolean>(false);
  const [collapsed, setCollapsed] = useState<boolean>(false);

  useEffect(() => {
    const saved = window.localStorage.getItem("socioai-sidebar-collapsed") === "1";
    setCollapsed(saved);
    window.dispatchEvent(new CustomEvent("socio-sidebar-change", { detail: { collapsed: saved } }));
  }, []);

  function toggleCollapsed(): void {
    const next = !collapsed;
    setCollapsed(next);
    window.localStorage.setItem("socioai-sidebar-collapsed", next ? "1" : "0");
    window.dispatchEvent(new CustomEvent("socio-sidebar-change", { detail: { collapsed: next } }));
  }
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
      { id: "socio-chat", key: "socio-chat", label: "Mentor", icon: "forum", href: baseCliente ? withCliente("socio-chat") : "/clientes", group: "flujo" },
      { id: "clientes", key: "clientes", label: "Clientes", icon: "groups", href: "/clientes", group: "flujo" },
      { id: "entity-profile", key: "entity-profile", label: "Contexto del cliente", icon: "domain", href: baseCliente ? withCliente("entity-profile") : "/clientes", group: "flujo" },
      { id: "trial-balance", key: "trial-balance", label: "Balance como fuente", icon: "insights", href: withCliente("trial-balance"), group: "flujo" },
      { id: "mayor", key: "mayor", label: "Mayor como fuente", icon: "table_view", href: withCliente("mayor"), group: "flujo" },
      { id: "learning-progress", key: "learning-progress", label: "Mi aprendizaje", icon: "school", href: "/learning-progress", group: "aprendizaje" },
      { id: "biblioteca", key: "biblioteca", label: "Biblioteca", icon: "menu_book", href: "/biblioteca", group: "aprendizaje" },
      { id: "procedimientos", key: "procedimientos", label: "Guía de procedimientos", icon: "fact_check", href: "/procedimientos", group: "aprendizaje" },
      ...(canManageUsers
        ? [{ id: "admin", key: "admin", label: "Administración", icon: "admin_panel_settings", href: "/admin", group: "administracion" } as NavItem]
        : []),
      { id: "perfil", key: "perfil", label: "Perfil técnico", icon: "business_center", href: withCliente("perfil"), group: "legacy" },
      { id: "dashboard", key: "dashboard", label: "Dashboard", icon: "dashboard", href: withCliente("dashboard"), group: "legacy" },
      { id: "risk-engine", key: "risk-engine", label: "Risk Engine", icon: "security", href: withCliente("risk-engine"), group: "legacy" },
      { id: "knowledge", key: "knowledge", label: "Knowledge Core", icon: "hub", href: withCliente("knowledge"), group: "legacy" },
      {
        id: "estados-financieros",
        key: "estados-financieros",
        label: "Índices Financieros",
        icon: "monitoring",
        href: withCliente("estados-financieros"), group: "legacy",
      },
      { id: "areas", key: "areas", label: "Workspace Áreas", icon: "receipt_long", href: withCliente("areas"), group: "legacy" },
      {
        id: "papeles-trabajo",
        key: "papeles-trabajo",
        label: "Papeles de Trabajo",
        icon: "task_alt",
        href: withCliente("papeles-trabajo"), group: "legacy",
      },
      { id: "client-memory", key: "client-memory", label: "Client Memory", icon: "folder_shared", href: withCliente("client-memory"), group: "legacy" },
      { id: "reportes", key: "reportes", label: "Reportes", icon: "description", href: withCliente("reportes"), group: "legacy" },
    ],
    [baseCliente, canManageUsers, withCliente],
  );

  const visibleItems = useMemo<NavItem[]>(
    () => (FULL_PLATFORM ? items : items.filter((item) => MVP_KEYS.has(item.key))),
    [items],
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
        className={`fixed inset-y-0 left-0 z-40 ${collapsed ? "w-20" : immersive ? "w-[286px]" : "w-72"} ${immersive ? "mentor-leather-sidebar border-r border-white/10" : "bg-[#edf3fa] border-r border-[#041627]/8"} transition-[width,transform] duration-200 ${openMobile ? "translate-x-0" : "-translate-x-full"} lg:translate-x-0`}
        role="navigation"
        aria-label="Navegación principal"
      >
        <div className={`h-full ${collapsed ? "p-3" : "p-5"} flex flex-col min-h-0`}>
          <div className={`mb-6 pt-2 ${collapsed ? "text-center" : "px-2"}`}>
            <h2 className={`font-headline ${immersive ? "text-white" : "text-navy-900"} ${collapsed ? "text-xl" : "text-3xl"}`}>{collapsed ? "SA" : <>Socio<span className={immersive ? "text-[#73d5cf]" : ""}>AI</span></>}</h2>
            {!collapsed ? <p className={`font-body text-[10px] tracking-[0.2em] uppercase mt-1 ${immersive ? "text-slate-400" : "text-slate-500"}`}>Tu mentor de auditoría</p> : null}
          </div>

          <button type="button" onClick={toggleCollapsed} className={`mb-4 min-h-[44px] items-center justify-center rounded-xl border ${immersive ? "hidden" : "hidden lg:flex border-[#041627]/10 bg-white text-slate-600 hover:text-[#041627]"}`} aria-label={collapsed ? "Expandir menú" : "Contraer menú"} title={collapsed ? "Expandir menú" : "Contraer menú"}>
            <span className="material-symbols-outlined text-[20px]">{collapsed ? "right_panel_open" : "left_panel_close"}</span>
          </button>

          <nav className="space-y-2 flex-1 overflow-y-auto pr-1 min-h-0" role="menubar">
            {visibleItems.map((item, index) => {
              const showGroup = index === 0 || visibleItems[index - 1]?.group !== item.group;
              const groupLabel = item.group === "flujo" ? "Flujo principal" : item.group === "aprendizaje" ? "Aprendizaje" : item.group === "administracion" ? "Administración" : "Plataforma completa";
              const active =
                item.key === "biblioteca" || item.key === "procedimientos" || item.key === "learning-progress"
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
                <div key={item.id}>
                {showGroup && !collapsed ? <p className={`mb-2 mt-5 px-3 text-[10px] font-semibold uppercase tracking-[0.16em] first:mt-0 ${immersive ? "text-slate-500" : "text-slate-400"}`}>{groupLabel}</p> : null}
                <Link
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
                              : item.key === "knowledge"
                                ? "sidebar-knowledge"
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
                  className={`flex items-center ${collapsed ? "justify-center px-2" : "gap-3 px-4"} ${immersive ? "rounded-r-xl rounded-l-none" : "rounded-editorial"} py-3 transition-colors min-h-[44px] focus:outline-none focus:ring-2 focus:ring-[#73d5cf] ${itemClass(active, immersive)}`}
                  onClick={() => {
                    stopTour();
                    setOpenMobile(false);
                  }}
                  role="menuitem"
                  aria-current={active ? "page" : undefined}
                  title={collapsed ? item.label : undefined}
                >
                  <span className="material-symbols-outlined text-[20px]" aria-hidden="true">{item.icon}</span>
                  {!collapsed ? <span className="font-body text-sm">{item.label}</span> : null}
                </Link>
                </div>
              );
            })}
          </nav>

          <div className={`pt-5 mt-4 ${immersive ? "border-t border-white/10" : "border-t border-black/5"}`}>
            <button
              type="button"
              onClick={() => {
                if (immersive) toggleCollapsed();
                else void logoutSession().finally(() => router.push("/"));
              }}
              className={`w-full flex items-center ${collapsed ? "justify-center px-2" : "gap-3 px-4"} rounded-editorial py-3 ${immersive ? "text-slate-400 hover:bg-white/[0.06] hover:text-white" : "text-slate-600 hover:bg-white/75"} transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[44px]`}
              aria-label={immersive ? (collapsed ? "Mostrar menú" : "Ocultar menú") : "Cerrar sesión y volver al login"}
            >
              <span className="material-symbols-outlined text-[20px]" aria-hidden="true">{immersive ? (collapsed ? "keyboard_double_arrow_right" : "keyboard_double_arrow_left") : "logout"}</span>
              {!collapsed ? <span className="font-body text-sm">{immersive ? "Ocultar menú" : "Volver al login"}</span> : null}
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
