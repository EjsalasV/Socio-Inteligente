"use client";

import dynamic from "next/dynamic";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import FlowGuide from "../../../components/flow/FlowGuide";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import { useDashboard } from "../../../lib/hooks/useDashboard";
import { useLearningRole } from "../../../lib/hooks/useLearningRole";

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

  const view =
    role === "socio" ? <DashboardSocio data={data} /> :
    role === "senior" ? <DashboardSenior data={data} /> :
    role === "junior" ? <DashboardJunior data={data} /> :
    <DashboardSemi data={data} />;

  if (setupIncomplete) {
    return (
      <div className="space-y-8 pb-8">
        <FlowGuide data={data} clienteId={clienteId} />
        {view}
      </div>
    );
  }

  return view;
}
