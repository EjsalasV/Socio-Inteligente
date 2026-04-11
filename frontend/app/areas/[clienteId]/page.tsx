"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";

import { useDashboard } from "../../../lib/hooks/useDashboard";
import { getLsOptions, normalizeLsCode } from "../../../lib/lsCatalog";

function normalizeAreaCode(raw: string): string {
  const clean = raw.trim();
  if (!clean) return "130";

  const options = getLsOptions();
  const exact = options.find((x) => x.codigo === clean);
  if (exact) return exact.codigo;

  const normalized = normalizeLsCode(clean);
  const byFamily = options.find((x) => normalizeLsCode(x.codigo) === normalized);
  if (byFamily) return byFamily.codigo;

  const digits = clean.replace(/[^0-9]/g, "");
  if (!digits) return "130";
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
