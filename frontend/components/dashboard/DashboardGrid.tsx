import SovereignCard from "../SovereignCard";
import { formatMoney } from "../../lib/formatters";
import type { DashboardData } from "../../types/dashboard";

type Props = {
  data: DashboardData;
};

export default function DashboardGrid({ data }: Props) {
  return (
    <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
      <SovereignCard title="Activo" value={formatMoney(data.activo, "USD", 0)} subtext="Total maestro" />
      <SovereignCard title="Pasivo" value={formatMoney(data.pasivo, "USD", 0)} subtext="Total maestro" />
      <SovereignCard title="Patrimonio" value={formatMoney(data.patrimonio, "USD", 0)} subtext="Total maestro" />
      <SovereignCard title="Ingresos" value={formatMoney(data.ingresos, "USD", 0)} subtext="Acumulado período" />
      <SovereignCard title="Gastos" value={formatMoney(data.gastos, "USD", 0)} subtext="Acumulado período" />
    </section>
  );
}
