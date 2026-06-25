"use client";

import dynamic from "next/dynamic";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import FlowGuide from "../../../components/flow/FlowGuide";
import { AlertsBanner } from "../../../components/dashboard/AlertsBanner";
import FeedbackCard from "../../../components/dashboard/FeedbackCard";
import { PeriodoComparador } from "../../../components/periodo-selector/PeriodoComparador";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import { useDashboard } from "../../../lib/hooks/useDashboard";
import { useLearningRole } from "../../../lib/hooks/useLearningRole";
import Link from "next/link";

const DashboardSocio = dynamic(() => import("../../../components/dashboard/views/DashboardSocio"), {
  loading: () => <DashboardSkeleton />,
});
const DashboardSenior = dynamic(() => import("../../../components/dashboard/views/DashboardSenior"), {
  loading: () => <DashboardSkeleton />,
});
const DashboardSemi = dynamic(() => import("../../../components/dashboard/views/DashboardSemi"), {
  loading: () => <DashboardSkeleton />,
});
const DashboardJunior = dynamic(() => import("../../../components/dashboard/views/DashboardJunior"), {
  loading: () => <DashboardSkeleton />,
});

export default function DashboardClientePage() {
  const { clienteId } = useAuditContext();
  const { data, isLoading, error } = useDashboard(clienteId);
  const { role } = useLearningRole();

  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorMessage message={error} />;
  if (!data) return <ErrorMessage message="No hay datos disponibles para este cliente." />;

  // Mostrar la guía de flujo cuando el setup aún no está completo
  const setupIncomplete = data.tb_stage === "sin_saldos" || data.materialidad_global === 0;
  const materialidadPorArea = (data.materialidad_por_area ?? []).slice(0, 6);

  const view =
    role === "socio" ? <DashboardSocio data={data} /> :
    role === "senior" ? <DashboardSenior data={data} /> :
    role === "junior" ? <DashboardJunior data={data} /> :
    <DashboardSemi data={data} />;

  if (setupIncomplete) {
    return (
      <div className="space-y-8 pb-8">
        <FlowGuide data={data} clienteId={clienteId} />
        {materialidadPorArea.length > 0 ? (
          <section className="sovereign-card">
            <p className="text-[10px] uppercase tracking-[0.16em] text-slate-500 font-bold mb-2">Materialidad por area</p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {materialidadPorArea.map((item) => (
                <article key={item.area_codigo} className="rounded-lg border border-[#041627]/12 bg-[#f1f4f6] p-3">
                  <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500 font-bold">{item.area_codigo}</p>
                  <p className="text-sm font-semibold text-[#041627] mt-1">{item.area_nombre}</p>
                  <p className="text-xs text-slate-600 mt-1">
                    {item.porcentaje_aplicado.toFixed(2)}% · ${item.materialidad_sugerida.toLocaleString("es-CO")}
                  </p>
                </article>
              ))}
            </div>
          </section>
        ) : null}
        {view}
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-8">
      <AlertsBanner />
      <FeedbackCard />
      <section className="sovereign-card flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-[10px] uppercase tracking-[0.16em] text-slate-500 font-bold">Ajustes del cliente</p>
          <h2 className="font-headline text-2xl text-[#041627] mt-1">Ajustar contexto del negocio</h2>
          <p className="text-sm text-slate-600 mt-2">
            Desde aquí puedes volver a los ajustes específicos del cliente sin salir del dashboard.
          </p>
        </div>
        <Link
          href={`/configuracion/${clienteId}`}
          className="inline-flex items-center justify-center px-4 py-2 rounded-xl text-white text-sm font-semibold"
          style={{ background: "linear-gradient(135deg, #041627 0%, #1a2b3c 100%)" }}
        >
          Abrir ajustes
        </Link>
      </section>
      {materialidadPorArea.length > 0 ? (
        <section className="sovereign-card">
          <p className="text-[10px] uppercase tracking-[0.16em] text-slate-500 font-bold mb-2">Materialidad por area</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {materialidadPorArea.map((item) => (
              <article key={item.area_codigo} className="rounded-lg border border-[#041627]/12 bg-[#f1f4f6] p-3">
                <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500 font-bold">{item.area_codigo}</p>
                <p className="text-sm font-semibold text-[#041627] mt-1">{item.area_nombre}</p>
                <p className="text-xs text-slate-600 mt-1">
                  {item.porcentaje_aplicado.toFixed(2)}% · ${item.materialidad_sugerida.toLocaleString("es-CO")}
                </p>
              </article>
            ))}
          </div>
        </section>
      ) : null}
      <PeriodoComparador />
      {view}
    </div>
  );
}
