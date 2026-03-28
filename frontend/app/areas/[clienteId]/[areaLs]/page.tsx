"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import LeadSchedule from "../../../../components/areas/LeadSchedule";
import DashboardSkeleton from "../../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../../components/dashboard/ErrorMessage";
import { patchAreaCheck } from "../../../../lib/api/areas";
import { useAreaDetail } from "../../../../lib/hooks/useAreaDetail";
import { getLsName, getLsOptions, getLsShortName, normalizeLsCode } from "../../../../lib/lsCatalog";
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

function isHighRisk(status: string, aseveraciones: { riesgo_tipico: string }[]): boolean {
  if (status.toLowerCase().includes("alto")) return true;
  return aseveraciones.some((a) => a.riesgo_tipico.toLowerCase().includes("alto"));
}

export default function AreaWorkspacePage() {
  const router = useRouter();
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
  const areaNavOptions = useMemo(
    () => Array.from(new Set(getLsOptions(10).map((x) => normalizeLsCode(x.codigo)))),
    [],
  );

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

  const highRisk = isHighRisk(data.encabezado.estatus, data.aseveraciones);
  const checkedCount = cuentas.filter((c) => c.checked).length;
  const pendingCount = Math.max(cuentas.length - checkedCount, 0);
  const blockingCount = data.aseveraciones.filter((a) => a.riesgo_tipico.toLowerCase().includes("alto")).length;

  return (
    <div className="space-y-8 pt-4 pb-8">
      <section className="flex flex-col xl:flex-row justify-between items-start gap-6">
        <div className="space-y-4">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`px-3 py-1 rounded text-[10px] font-bold tracking-[0.14em] uppercase ${highRisk ? "bg-[#ba1a1a] text-white" : "bg-emerald-100 text-emerald-700"}`}>
              {highRisk ? "Riesgo Alto" : "Riesgo Controlado"}
            </span>
            <span className={`px-3 py-1 rounded text-[10px] font-bold tracking-[0.14em] uppercase ${badgeTone(data.encabezado.estatus)}`}>
              {data.encabezado.estatus}
            </span>
          </div>
          <div>
            <p className="font-body text-xs uppercase tracking-[0.16em] text-slate-500">Workspace de Área</p>
            <h2 className="font-headline text-5xl text-[#041627] mt-1 tracking-tight">
              {data.encabezado.area_code} - {data.encabezado.nombre}
            </h2>
            <p className="text-slate-500 mt-3 font-body text-sm">
              Ejercicio {data.encabezado.actual_year} · Responsable <b>{data.encabezado.responsable}</b>
            </p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-black/10 shadow-editorial flex gap-8">
          <div>
            <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">Checks</p>
            <p className="font-headline text-4xl text-[#041627] mt-2">{checkedCount}</p>
          </div>
          <div className="w-px bg-slate-200" />
          <div>
            <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">Pendientes</p>
            <p className="font-headline text-4xl text-[#ba1a1a] mt-2">{pendingCount}</p>
          </div>
        </div>
      </section>

      <section className={`rounded-[2rem] p-1 shadow-editorial ${highRisk ? "bg-gradient-to-br from-[#ba1a1a] to-[#93000a]" : "bg-gradient-to-br from-[#041627] to-[#1a2b3c]"}`}>
        <div className={`rounded-[1.9rem] p-8 border ${highRisk ? "bg-[#ba1a1a] border-white/10" : "bg-[#1a2b3c] border-white/10"} text-white`}>
          <div className="flex flex-col xl:flex-row xl:items-center xl:justify-between gap-6">
            <div className="flex items-start gap-5">
              <div className="bg-white/10 p-4 rounded-2xl border border-white/20">
                <span className="material-symbols-outlined text-5xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                  {highRisk ? "dangerous" : "verified_user"}
                </span>
              </div>
              <div>
                <h3 className="font-headline text-4xl leading-tight">
                  {highRisk ? "Estado: No lista para cierre" : "Estado: Lista para cierre técnico"}
                </h3>
                <p className="font-headline italic text-lg text-slate-200 mt-3 max-w-3xl leading-relaxed">
                  {highRisk
                    ? "El área requiere procedimientos adicionales antes de emitir criterio final. Se observan alertas abiertas en aseveraciones clave."
                    : "El área mantiene consistencia en saldos y procedimientos, con pendientes menores de documentación."}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 min-w-[220px]">
              <div className="bg-black/20 px-4 py-3 rounded-xl border border-white/10 flex items-center justify-between">
                <span className="text-xs uppercase tracking-[0.12em] text-slate-200 font-bold">Hallazgos</span>
                <span className="text-xl font-bold">{blockingCount}</span>
              </div>
              <div className="bg-black/20 px-4 py-3 rounded-xl border border-white/10 flex items-center justify-between">
                <span className="text-xs uppercase tracking-[0.12em] text-slate-200 font-bold">Pendientes</span>
                <span className="text-xl font-bold">{pendingCount}</span>
              </div>
            </div>
          </div>

          <div className="mt-7 pt-6 border-t border-white/10">
            <h4 className="text-xs font-bold tracking-[0.2em] uppercase mb-4 flex items-center">
              <span className="material-symbols-outlined text-sm mr-2">list_alt</span>
              Acciones requeridas para cierre
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {(data.aseveraciones.length > 0
                ? data.aseveraciones.slice(0, 3).map((a) => a.procedimiento_clave || `Completar prueba de ${a.nombre}`)
                : ["Completar revisión de soportes", "Actualizar papeles de trabajo", "Documentar conclusión del área"]
              ).map((task) => (
                <div key={task} className="bg-white/5 border border-white/10 rounded-xl p-4 flex items-center gap-3">
                  <span className="material-symbols-outlined text-white/60">check_circle</span>
                  <span className="text-sm text-white">{task}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
        <section className="xl:col-span-8 space-y-8">
          <LeadSchedule
            cuentas={cuentas}
            currentYear={data.encabezado.actual_year}
            previousYear={data.encabezado.anterior_year}
            title={`${data.encabezado.area_code} - ${data.encabezado.nombre}`}
            onToggleCheck={handleToggleCheck}
          />
        </section>

        <section className="xl:col-span-4 space-y-6">
          <article className="sovereign-card">
            <h3 className="font-headline text-2xl text-[#041627] mb-4">Aseveraciones vinculadas</h3>
            <div className="space-y-3">
              {data.aseveraciones.map((a, idx) => (
                <article key={`${a.nombre}-${idx}`} className="bg-[#f1f4f6] rounded-editorial p-4">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-headline text-xl text-[#041627]">{a.nombre}</p>
                    <span className={`text-[10px] px-2 py-1 rounded uppercase tracking-[0.1em] font-bold ${badgeTone(a.riesgo_tipico)}`}>{a.riesgo_tipico}</span>
                  </div>
                  <p className="font-body text-sm text-slate-600 mt-2 leading-relaxed">{a.descripcion}</p>
                </article>
              ))}
            </div>
          </article>

          <article className="sovereign-card">
            <h4 className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold mb-4">Navegación rápida</h4>
            <select
              value={areaCode}
              onChange={(e) => router.push(`/areas/${clienteId}/${e.target.value}`)}
              className="ghost-input w-full"
            >
              {areaNavOptions.map((code) => (
                <option key={code} value={code}>
                  {getLsShortName(code)} · {code}
                </option>
              ))}
            </select>
            <p className="text-[11px] text-slate-500 mt-3">
              {getLsName(areaCode)}
            </p>
          </article>
        </section>
      </div>
    </div>
  );
}
