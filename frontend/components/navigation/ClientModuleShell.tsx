"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { clearSessionState, hasSessionState } from "../../lib/auth-session";
import { buildApiUrl } from "../../lib/api-base";
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
    let disposed = false;

    const syncLocalState = () => {
      const active = hasSessionState();
      if (disposed) return active;
      setIsAuthenticated(active);
      setReady(true);
      if (!active) {
        router.replace("/");
      }
      return active;
    };

    const validateBackendSession = async () => {
      const active = syncLocalState();
      if (!active) return;
      try {
        const res = await fetch(buildApiUrl("/auth/me"), {
          method: "GET",
          credentials: "include",
          cache: "no-store",
        });
        if (!res.ok) {
          clearSessionState();
          if (!disposed) {
            setIsAuthenticated(false);
            router.replace("/");
          }
        }
      } catch {
        // Si no hay red, no forzamos logout; mantenemos estado local.
      }
    };

    const onAuthChanged = () => {
      syncLocalState();
    };

    syncLocalState();
    void validateBackendSession();
    window.addEventListener("socio-auth-changed", onAuthChanged);
    window.addEventListener("focus", onAuthChanged);

    return () => {
      disposed = true;
      window.removeEventListener("socio-auth-changed", onAuthChanged);
      window.removeEventListener("focus", onAuthChanged);
    };
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
