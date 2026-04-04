"use client";

import { useEffect, useMemo, useState } from "react";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import { formatMoney, moneyClass } from "../../../lib/formatters";
import { useAreaDetail } from "../../../lib/hooks/useAreaDetail";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import { useDashboard } from "../../../lib/hooks/useDashboard";
import { getLsName, getLsOptions, getLsShortName, normalizeLsCode } from "../../../lib/lsCatalog";

function variationPct(actual: number, previous: number): number {
  if (previous === 0) return actual === 0 ? 0 : 100;
  return ((actual - previous) / Math.abs(previous)) * 100;
}

export default function EstadosFinancierosPage() {
  const { clienteId } = useAuditContext();
  const { data: dashboard, isLoading, error } = useDashboard(clienteId);

  const baseOptions = useMemo(() => getLsOptions(8).map((x) => normalizeLsCode(x.codigo)), []);
  const dynamicOptions = useMemo(
    () =>
      (dashboard?.top_areas ?? [])
        .filter((x) => x.con_saldo)
        .map((x) => normalizeLsCode(x.codigo))
        .filter(Boolean),
    [dashboard],
  );
  const options = useMemo(() => {
    if (dynamicOptions.length > 0) return Array.from(new Set(dynamicOptions));
    return Array.from(new Set(baseOptions));
  }, [baseOptions, dynamicOptions]);
  const [selectedArea, setSelectedArea] = useState<string>(options[0] ?? "140");

  useEffect(() => {
    if (options.length === 0) return;
    if (!options.includes(selectedArea)) setSelectedArea(options[0]);
  }, [options, selectedArea]);

  const { data: areaData } = useAreaDetail(clienteId, selectedArea);

  const cuentasComparativas = useMemo(() => {
    return [...(areaData?.cuentas ?? [])]
      .sort((a, b) => Math.abs(b.saldo_actual) - Math.abs(a.saldo_actual))
      .slice(0, 8);
  }, [areaData]);

  const me = dashboard?.materialidad_ejecucion ?? (dashboard?.materialidad_global ?? 0) * 0.75;
  const triviales = dashboard?.umbral_trivial ?? (dashboard?.materialidad_global ?? 0) * 0.05;
  const tbStage = (dashboard?.tb_stage || "sin_saldos").toLowerCase();
  const tbStageLabel =
    tbStage === "final"
      ? "Corte Final"
      : tbStage === "preliminar"
        ? "Corte Preliminar"
        : tbStage === "inicial"
          ? "Corte Inicial"
          : "Sin saldos";
  const materialidadOrigenLabel =
    dashboard?.materialidad_origen === "perfil"
      ? "Definida en perfil del cliente"
      : dashboard?.materialidad_origen === "motor"
        ? "Estimacion automatica del motor"
        : "Pendiente de definicion";
  const materialidadDetalle = dashboard?.materialidad_detalle;
  const materialidadFormula = materialidadDetalle?.base_usada
    ? `${materialidadDetalle.porcentaje_rango_min.toFixed(1)}% - ${materialidadDetalle.porcentaje_rango_max.toFixed(1)}% de ${materialidadDetalle.base_usada}`
    : "Sin formula tecnica disponible";

  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorMessage message={error} />;
  if (!dashboard) return <ErrorMessage message="No hay datos de estados financieros para este cliente." />;

  return (
    <div className="pt-4 pb-10 space-y-8 max-w-screen-2xl">
      <header className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          <h1 className="font-headline text-4xl text-[#041627]">Estados Financieros - Analisis Comparativo</h1>
          <p className="font-body text-sm text-slate-500 mt-2">
            Cliente {dashboard.nombre_cliente} · Periodo {dashboard.periodo || "Actual"}
          </p>
          <div className="mt-3">
            <span className="inline-flex items-center rounded-full border border-[#041627]/20 bg-[#f1f4f6] px-3 py-1 text-[11px] font-semibold text-[#041627]">
              TB: {tbStageLabel}
            </span>
          </div>
        </div>
        <div className="min-w-[320px]">
          <label className="block text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold mb-2">Area</label>
          <select
            value={selectedArea}
            onChange={(e) => setSelectedArea(e.target.value)}
            className="ghost-input w-full"
          >
            {options.map((area) => (
              <option key={area} value={area}>
                {getLsShortName(area)} · {area}
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 mt-2">{getLsName(selectedArea)}</p>
        </div>
      </header>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <article className="sovereign-card border-l-4 border-[#041627]">
          <p className="text-[10px] uppercase tracking-[0.16em] text-slate-500 font-bold">Materialidad de Planeacion</p>
          <h3 className="font-headline text-3xl text-[#041627] mt-3">{formatMoney(dashboard.materialidad_global)}</h3>
          <p className="text-xs text-slate-500 mt-2">{materialidadOrigenLabel}</p>
          <p className="text-xs text-slate-500 mt-1">{materialidadFormula}</p>
        </article>

        <article className="sovereign-card border-l-4 border-[#89d3d4]">
          <p className="text-[10px] uppercase tracking-[0.16em] text-slate-500 font-bold">Materialidad de Ejecucion</p>
          <h3 className="font-headline text-3xl text-[#041627] mt-3">{formatMoney(me)}</h3>
          <p className="text-xs text-slate-500 mt-2">75% de MP</p>
        </article>

        <article className="rounded-editorial bg-[#1a2b3c] p-6 shadow-editorial text-white">
          <p className="text-[10px] uppercase tracking-[0.16em] text-[#89d3d4] font-bold">Umbral Trivial</p>
          <h3 className="font-headline text-3xl mt-3">{formatMoney(triviales)}</h3>
          <p className="text-xs text-slate-300 mt-2">5% de MP</p>
        </article>
      </section>

      <section className="bg-[#f1f4f6] rounded-editorial p-1">
        <div className="bg-white rounded-editorial overflow-hidden">
          <div className="px-8 py-6 border-b border-black/5 flex items-center justify-between gap-3">
            <h2 className="font-headline text-2xl text-[#041627]">
              Balance General y P&G · {areaData?.encabezado.nombre || getLsName(selectedArea)}
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-[#f1f4f6]">
                  <th className="px-8 py-4 text-left text-[11px] uppercase tracking-[0.14em] text-slate-500">Cuenta</th>
                  <th className="px-8 py-4 text-right text-[11px] uppercase tracking-[0.14em] text-slate-500">Ano actual</th>
                  <th className="px-8 py-4 text-right text-[11px] uppercase tracking-[0.14em] text-slate-500">Ano anterior</th>
                  <th className="px-8 py-4 text-right text-[11px] uppercase tracking-[0.14em] text-slate-500">Variacion $</th>
                  <th className="px-8 py-4 text-right text-[11px] uppercase tracking-[0.14em] text-slate-500">Variacion %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-black/5">
                {cuentasComparativas.map((row) => {
                  const varMonto = row.saldo_actual - row.saldo_anterior;
                  const varPct = variationPct(row.saldo_actual, row.saldo_anterior);
                  const critical = Math.abs(varMonto) > me || Math.abs(varPct) > 10;
                  return (
                    <tr key={row.codigo} className={`hover:bg-[#f7fafc] ${critical ? "bg-[#ffdad6]/30" : "bg-white"}`}>
                      <td className="px-8 py-5 text-sm font-semibold text-[#041627]">
                        {row.codigo} - {row.nombre}
                      </td>
                      <td className={`px-8 py-5 text-right text-sm ${moneyClass(row.saldo_actual)}`}>{formatMoney(row.saldo_actual)}</td>
                      <td className={`px-8 py-5 text-right text-sm ${moneyClass(row.saldo_anterior)}`}>{formatMoney(row.saldo_anterior)}</td>
                      <td className={`px-8 py-5 text-right text-sm ${moneyClass(varMonto)} ${critical ? "font-bold" : ""}`}>{formatMoney(varMonto)}</td>
                      <td className={`px-8 py-5 text-right text-sm ${critical ? "text-[#ba1a1a] font-bold" : "text-slate-600"}`}>
                        {varPct.toFixed(1)}%
                        {critical ? <span className="material-symbols-outlined text-sm align-middle ml-1">warning</span> : null}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        <article className="lg:col-span-3 sovereign-card">
          <div className="flex items-center gap-3 mb-6">
            <span className="material-symbols-outlined text-[#89d3d4] bg-[#002f30] p-2 rounded-lg">psychology</span>
            <h3 className="font-headline text-2xl text-[#041627]">Criterio del Socio IA</h3>
          </div>
          <div className="space-y-4">
            <div className="bg-[#f1f4f6] rounded-editorial p-5 border-l-4 border-[#89d3d4]">
              <p className="text-xs uppercase tracking-[0.12em] text-slate-500 font-bold mb-2">Analisis principal</p>
              <p className="text-sm text-slate-700 leading-relaxed">
                El riesgo global se mantiene en <b>{dashboard.riesgo_global}</b>. Se recomienda priorizar revision de variaciones
                superiores a ME y validar su soporte documental antes del cierre.
              </p>
            </div>
            <div className="bg-[#f1f4f6] rounded-editorial p-5">
              <p className="text-xs uppercase tracking-[0.12em] text-slate-500 font-bold mb-2">Coherencia financiera</p>
              <p className="text-sm text-slate-700 leading-relaxed">
                Activo: <b>{formatMoney(dashboard.activo)}</b> · Pasivo: <b>{formatMoney(dashboard.pasivo)}</b> · Patrimonio: <b>{formatMoney(dashboard.patrimonio)}</b>.
              </p>
            </div>
          </div>
        </article>

        <article className="lg:col-span-2 rounded-editorial bg-[#1a2b3c] text-white p-8 shadow-editorial">
          <h3 className="font-headline text-2xl">Alertas de Integridad</h3>
          <div className="space-y-4 mt-6">
            {(areaData?.aseveraciones ?? []).slice(0, 3).map((a, idx) => (
              <div key={`${a.nombre}-${idx}`} className="flex gap-3">
                <span className="material-symbols-outlined text-[#89d3d4] mt-0.5">report_problem</span>
                <div>
                  <p className="text-sm font-semibold">{a.nombre}</p>
                  <p className="text-xs text-slate-300 mt-1 leading-relaxed">{a.descripcion}</p>
                </div>
              </div>
            ))}
            {(areaData?.aseveraciones ?? []).length === 0 ? (
              <p className="text-sm text-slate-300">Sin alertas automaticas para esta area.</p>
            ) : null}
          </div>
        </article>
      </section>
    </div>
  );
}
