"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import Header from "./Header";
import Sidebar from "./Sidebar";

export default function ClientModuleShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
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
      <div className="lg:ml-72">
        <Header />
        <div className="px-4 md:px-8 pb-8">{children}</div>
      </div>
    </div>
  );
}
