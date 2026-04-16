"use client";

import { createContext, useContext, useMemo } from "react";
import { usePathname } from "next/navigation";

export type AuditModule =
  | "dashboard"
  | "risk-engine"
  | "trial-balance"
  | "estados-financieros"
  | "areas"
  | "papeles-trabajo"
  | "perfil"
  | "reportes"
  | "socio-chat"
  | "client-memory"
  | "biblioteca"
  | "procedimientos";

type AuditContextValue = {
  clienteId: string;
  moduleKey: AuditModule;
  moduleLabel: string;
  pathname: string;
};

const AuditContext = createContext<AuditContextValue | null>(null);

function parseFromPath(pathname: string): AuditContextValue {
  const chunks = pathname.split("/").filter(Boolean);
  const first = chunks[0] ?? "dashboard";
  const second = chunks[1] ?? "";

  let moduleKey: AuditModule = "dashboard";
  if (first === "risk-engine") moduleKey = "risk-engine";
  if (first === "areas") moduleKey = "areas";
  if (first === "perfil") moduleKey = "perfil";
  if (first === "trial-balance") moduleKey = "trial-balance";
  if (first === "estados-financieros") moduleKey = "estados-financieros";
  if (first === "reportes") moduleKey = "reportes";
  if (first === "papeles-trabajo") moduleKey = "papeles-trabajo";
  if (first === "socio-chat") moduleKey = "socio-chat";
  if (first === "client-memory") moduleKey = "client-memory";
  if (first === "biblioteca") moduleKey = "biblioteca";
  if (first === "procedimientos") moduleKey = "procedimientos";

  const labels: Record<AuditModule, string> = {
    dashboard: "Dashboard",
    "risk-engine": "Risk Engine",
    "trial-balance": "Trial Balance",
    "estados-financieros": "Estados Financieros",
    areas: "Áreas L/S",
    "papeles-trabajo": "Papeles de Trabajo",
    perfil: "Perfil Cliente",
    reportes: "Reportes",
    "socio-chat": "Socio Chat",
    "client-memory": "Client Memory",
    biblioteca: "Biblioteca",
    procedimientos: "Procedimientos",
  };

  return {
    clienteId: second,
    moduleKey,
    moduleLabel: labels[moduleKey],
    pathname,
  };
}

export function AuditContextProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const value = useMemo(() => parseFromPath(pathname), [pathname]);
  return <AuditContext.Provider value={value}>{children}</AuditContext.Provider>;
}

export function useAuditContext(): AuditContextValue {
  const ctx = useContext(AuditContext);
  if (ctx) return ctx;

  // Fallback defensivo para uso fuera del provider.
  if (typeof window !== "undefined") {
    return parseFromPath(window.location.pathname);
  }
  return {
    clienteId: "",
    moduleKey: "dashboard",
    moduleLabel: "Dashboard",
    pathname: "/",
  };
}
