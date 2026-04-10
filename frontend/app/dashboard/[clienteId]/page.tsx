"use client";

import dynamic from "next/dynamic";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import { useDashboard } from "../../../lib/hooks/useDashboard";

const DashboardContent = dynamic(() => import("../../../components/dashboard/DashboardContent"), {
  loading: () => <DashboardSkeleton />,
});

export default function DashboardClientePage() {
  const { clienteId } = useAuditContext();
  const { data, isLoading, error } = useDashboard(clienteId);

  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorMessage message={error} />;
  if (!data) return <ErrorMessage message="No hay datos disponibles para este cliente." />;

  return <DashboardContent data={data} />;
}
