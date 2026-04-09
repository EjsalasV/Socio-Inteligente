"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuditContext } from "../../lib/hooks/useAuditContext";
import { useDashboard } from "../../lib/hooks/useDashboard";
import ClienteRealtimeProvider from "../providers/ClienteRealtimeProvider";
import Header from "./Header";
import OnboardingGuideBanner from "./OnboardingGuideBanner";
import Sidebar from "./Sidebar";

export default function ClientModuleShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { clienteId, moduleKey } = useAuditContext();
  const { data: dashboard, isLoading: dashboardLoading } = useDashboard(clienteId);
  const [ready, setReady] = useState<boolean>(false);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("socio_token") : null;
    if (!token) {
      setIsAuthenticated(false);
      setReady(true);
      router.replace("/");
      return;
    }

    setIsAuthenticated(true);
    setReady(true);
  }, [router]);

  useEffect(() => {
    if (!ready || !isAuthenticated) return;
    if (!clienteId) return;
    if (dashboardLoading) return;
    const exemptModules = new Set(["perfil", "trial-balance"]);
    if (exemptModules.has(moduleKey)) return;
    if (!dashboard) return;
    if ((dashboard.tb_stage || "sin_saldos").toLowerCase() === "sin_saldos") {
      router.replace(`/trial-balance/${clienteId}?required_tb=1`);
    }
  }, [clienteId, dashboard, dashboardLoading, isAuthenticated, moduleKey, ready, router]);

  if (!ready || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-surface px-6 py-8">
        <div className="sovereign-card h-28 animate-pulse bg-[#edf2f7]" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface">
      <Sidebar />
      <ClienteRealtimeProvider>
        <div className="lg:ml-72">
          <Header />
          <OnboardingGuideBanner />
          <div className="px-4 md:px-8 pb-8">{children}</div>
        </div>
      </ClienteRealtimeProvider>
    </div>
  );
}
