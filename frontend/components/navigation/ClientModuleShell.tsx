"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { hasSessionState } from "../../lib/auth-session";
import { getClienteTbStatus } from "../../lib/api/clientes";
import { useAuditContext } from "../../lib/hooks/useAuditContext";
import ClienteRealtimeProvider from "../providers/ClienteRealtimeProvider";
import Header from "./Header";
import OnboardingGuideBanner from "./OnboardingGuideBanner";
import Sidebar from "./Sidebar";

export default function ClientModuleShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { clienteId, moduleKey } = useAuditContext();
  const [ready, setReady] = useState<boolean>(false);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);

  useEffect(() => {
    if (!hasSessionState()) {
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
    const exemptModules = new Set(["perfil", "trial-balance"]);
    if (exemptModules.has(moduleKey)) return;

    let cancelled = false;
    const run = async () => {
      try {
        const status = await getClienteTbStatus(clienteId);
        if (cancelled) return;
        if (!status.has_tb) {
          router.replace(`/trial-balance/${clienteId}?required_tb=1`);
        }
      } catch {
        // Si el chequeo liviano falla, no bloqueamos navegacion del modulo.
      }
    };

    void run();
    return () => {
      cancelled = true;
    };
  }, [clienteId, isAuthenticated, moduleKey, ready, router]);

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
