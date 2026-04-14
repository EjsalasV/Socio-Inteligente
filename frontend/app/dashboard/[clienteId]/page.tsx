"use client";

import dynamic from "next/dynamic";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
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

  if (role === "socio") return <DashboardSocio data={data} />;
  if (role === "senior") return <DashboardSenior data={data} />;
  if (role === "junior") return <DashboardJunior data={data} />;
  return <DashboardSemi data={data} />;
}
