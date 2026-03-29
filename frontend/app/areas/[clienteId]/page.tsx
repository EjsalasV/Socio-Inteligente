"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";

import { useDashboard } from "../../../lib/hooks/useDashboard";

function normalizeAreaCode(raw: string): string {
  const digits = raw.replace(/[^0-9]/g, "");
  if (!digits) return "130";
  if (digits.startsWith("35")) return "35";
  if (digits.startsWith("14")) return "140";
  if (digits.startsWith("13")) return "130";
  if (digits.startsWith("12")) return "120";
  if (digits.startsWith("11")) return "110";
  if (digits.startsWith("20")) return "200";
  if (digits.startsWith("21")) return "210";
  if (digits.startsWith("3")) return "300";
  return digits.slice(0, 3);
}

export default function AreasRootPage() {
  const router = useRouter();
  const params = useParams<{ clienteId?: string | string[] }>();
  const clienteId = Array.isArray(params?.clienteId) ? params.clienteId[0] : params?.clienteId ?? "";
  const { data } = useDashboard(clienteId);

  useEffect(() => {
    if (!clienteId) return;
    const topArea = (data?.top_areas ?? []).find((a) => a.con_saldo) ?? data?.top_areas?.[0];
    const target = topArea ? normalizeAreaCode(topArea.codigo) : "130";
    router.replace(`/areas/${clienteId}/${target}`);
  }, [clienteId, data, router]);

  return <div className="pt-8 text-sm text-slate-500">Cargando area priorizada...</div>;
}
