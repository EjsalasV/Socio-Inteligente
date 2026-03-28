"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import LeadSchedule from "../../../../components/areas/LeadSchedule";
import DashboardSkeleton from "../../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../../components/dashboard/ErrorMessage";
import { patchAreaCheck } from "../../../../lib/api/areas";
import { useAreaDetail } from "../../../../lib/hooks/useAreaDetail";
import type { AreaCuenta } from "../../../../types/area";

type Params = {
  clienteId?: string | string[];
  areaLs?: string | string[];
};

function badgeTone(value: string): string {
  const v = value.toLowerCase();
  if (v.includes("alto")) return "bg-red-50 text-red-700";
  if (v.includes("medio")) return "bg-amber-50 text-amber-700";
  return "bg-emerald-50 text-emerald-700";
}

export default function AreaWorkspacePage() {
  const params = useParams<Params>();
  const clienteId = useMemo(() => {
    const raw = params?.clienteId;
    return Array.isArray(raw) ? raw[0] : raw ?? "";
  }, [params]);
  const areaCode = useMemo(() => {
    const raw = params?.areaLs;
    return Array.isArray(raw) ? raw[0] : raw ?? "";
  }, [params]);

  const { data, isLoading, error } = useAreaDetail(clienteId, areaCode);
  const [cuentas, setCuentas] = useState<AreaCuenta[]>([]);

  useEffect(() => {
    setCuentas(data?.cuentas ?? []);
  }, [data]);

  async function handleToggleCheck(codigo: string, checked: boolean): Promise<void> {
    setCuentas((prev) => prev.map((c) => (c.codigo === codigo ? { ...c, checked } : c)));
    try {
      await patchAreaCheck(clienteId, areaCode, codigo, checked);
    } catch {
      setCuentas((prev) => prev.map((c) => (c.codigo === codigo ? { ...c, checked: !checked } : c)));
    }
  }

  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorMessage message={error} />;
  if (!data) return <ErrorMessage message="No hay información para esta área." />;

  return (
    <div className="space-y-6">
      <section className="sovereign-card">
        <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="font-body text-xs uppercase tracking-[0.16em] text-slate-500">Workspace de Área</p>
            <h2 className="font-headline text-4xl text-navy-900 mt-1">
              {data.encabezado.area_code} - {data.encabezado.nombre}
            </h2>
          </div>
          <div className="text-right">
            <p className="font-body text-sm text-slate-600">Responsable: <b>{data.encabezado.responsable}</b></p>
            <span className={`inline-flex mt-2 px-2 py-1 rounded text-[10px] uppercase tracking-[0.12em] font-bold ${badgeTone(data.encabezado.estatus)}`}>
              {data.encabezado.estatus}
            </span>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <section className="sovereign-card xl:col-span-2">
          <LeadSchedule
            cuentas={cuentas}
            currentYear={data.encabezado.actual_year}
            previousYear={data.encabezado.anterior_year}
            title={`${data.encabezado.area_code} - ${data.encabezado.nombre}`}
            onToggleCheck={handleToggleCheck}
          />
        </section>

        <section className="sovereign-card space-y-3">
          <h3 className="font-headline text-2xl text-navy-900">Aseveraciones</h3>
          {data.aseveraciones.map((a, idx) => (
            <article key={`${a.nombre}-${idx}`} className="bg-[#f1f4f6] rounded-editorial p-3">
              <div className="flex items-center justify-between">
                <p className="font-headline text-lg text-navy-900">{a.nombre}</p>
                <span className={`text-[10px] px-2 py-1 rounded uppercase tracking-[0.1em] font-bold ${badgeTone(a.riesgo_tipico)}`}>{a.riesgo_tipico}</span>
              </div>
              <p className="font-body text-sm text-slate-600 mt-1 leading-relaxed">{a.descripcion}</p>
            </article>
          ))}

          <Link href={`/areas/${clienteId}/140`} prefetch className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.12em] text-slate-500 hover:text-navy-900">
            <span className="material-symbols-outlined text-base">arrow_back</span>
            Ir a área 140 - Efectivo
          </Link>
        </section>
      </div>
    </div>
  );
}
