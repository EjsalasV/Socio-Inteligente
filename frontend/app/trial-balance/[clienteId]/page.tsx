"use client";

import { useEffect, useMemo, useState } from "react";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import { formatMoney, moneyClass } from "../../../lib/formatters";
import { useAreaDetail } from "../../../lib/hooks/useAreaDetail";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import { useDashboard } from "../../../lib/hooks/useDashboard";
import { getLsName, getLsOptions, getLsShortName, normalizeLsCode } from "../../../lib/lsCatalog";

const BASE_OPTIONS = getLsOptions(10).map((x) => normalizeLsCode(x.codigo));

function variationPct(actual: number, previous: number): number {
  if (previous === 0) return actual === 0 ? 0 : 100;
  return ((actual - previous) / Math.abs(previous)) * 100;
}

export default function TrialBalancePage() {
  const { clienteId } = useAuditContext();
  const { data: dashboard, isLoading, error } = useDashboard(clienteId);

  const areaChoices = useMemo(() => {
    const dynamic = (dashboard?.top_areas ?? []).map((x) => normalizeLsCode(x.codigo)).filter(Boolean);
    return Array.from(new Set([...BASE_OPTIONS, ...dynamic]));
  }, [dashboard]);

  const [selectedArea, setSelectedArea] = useState<string>(areaChoices[0] ?? "140");
  useEffect(() => {
    if (areaChoices.length === 0) return;
    if (!areaChoices.includes(selectedArea)) setSelectedArea(areaChoices[0]);
  }, [areaChoices, selectedArea]);

  const { data: areaData, error: areaError } = useAreaDetail(clienteId, selectedArea || "130");
  const cuentas = useMemo(() => areaData?.cuentas ?? [], [areaData?.cuentas]);

  const criticalCount = useMemo(
    () => cuentas.filter((c) => Math.abs(variationPct(c.saldo_actual, c.saldo_anterior)) > 10).length,
    [cuentas],
  );
  const aiFlags = useMemo(
    () => (areaData?.aseveraciones ?? []).filter((a) => a.riesgo_tipico.toLowerCase().includes("alto")).length,
    [areaData],
  );
  const balanceStatus = (dashboard?.balance_status || "cuadrado").toLowerCase();
  const balanceDelta = Math.abs(dashboard?.balance_delta ?? 0);
  const resultadoPeriodo = dashboard?.resultado_periodo ?? 0;
  const balanceOk = balanceStatus === "cuadrado";
  const isResultadoPeriodo = balanceStatus === "resultado_periodo";
  const tbStage = (dashboard?.tb_stage || "sin_saldos").toLowerCase();
  const tbStageLabel =
    tbStage === "final"
      ? "Corte Final"
      : tbStage === "preliminar"
        ? "Corte Preliminar"
        : tbStage === "inicial"
          ? "Corte Inicial"
          : "Sin saldos";

  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorMessage message={error} />;
  if (!dashboard) return <ErrorMessage message="No hay datos disponibles para Trial Balance." />;

  return (
    <div className="pt-4 pb-8 space-y-8 max-w-screen-2xl">
      <header className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4">
        <div>
          <h1 className="font-headline text-4xl text-[#041627]">Balance de Comprobacion - Revision Analitica</h1>
          <p className="font-body text-sm text-slate-500 mt-2">
            Ejercicio {dashboard.periodo || "Actual"} · Cliente {dashboard.nombre_cliente}
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
            {areaChoices.map((area) => (
              <option key={area} value={area}>
                {getLsShortName(area)} · {area}
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 mt-2">{getLsName(selectedArea)}</p>
        </div>
      </header>

      <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <article className="sovereign-card border-l-4 border-[#041627]">
          <p className="text-[10px] font-body font-bold uppercase tracking-[0.14em] text-slate-500">Balance A/L</p>
          <h3 className="font-headline text-2xl text-[#041627] mt-3">
            {balanceOk ? "Cuadrado" : isResultadoPeriodo ? "Cuadrado (con resultado del periodo)" : "Descuadrado"}
          </h3>
          <p
            className={`text-xs mt-2 ${
              balanceOk || isResultadoPeriodo ? "text-slate-500" : "text-[#ba1a1a] font-semibold"
            }`}
          >
            {balanceOk
              ? "Activo = Pasivo + Patrimonio"
              : isResultadoPeriodo
                ? `Resultado del periodo: ${formatMoney(resultadoPeriodo)}`
                : `Diferencia real: ${formatMoney(balanceDelta)}`}
          </p>
        </article>

        <article className="sovereign-card">
          <p className="text-[10px] font-body font-bold uppercase tracking-[0.14em] text-slate-500">Materialidad</p>
          <h3 className="font-headline text-3xl text-[#041627] mt-3">{formatMoney(dashboard.materialidad_global)}</h3>
          <p className="text-xs text-slate-500 mt-2">
            {dashboard.materialidad_origen === "perfil"
              ? "Tomada del perfil"
              : dashboard.materialidad_origen === "motor"
                ? "Estimacion automatica"
                : "Pendiente de definicion"}
          </p>
        </article>

        <article className="sovereign-card">
          <p className="text-[10px] font-body font-bold uppercase tracking-[0.14em] text-slate-500">Variaciones &gt; 10%</p>
          <h3 className="font-headline text-3xl text-[#ba1a1a] mt-3">{criticalCount}</h3>
        </article>

        <article className="rounded-editorial p-6 bg-[#002f30] text-white shadow-editorial">
          <p className="text-[10px] font-body font-bold uppercase tracking-[0.14em] text-[#a5eff0]">Alertas IA</p>
          <h3 className="font-headline text-4xl mt-3">{aiFlags.toString().padStart(2, "0")}</h3>
          <p className="text-xs text-[#89d3d4] mt-2">Riesgos altos en aseveraciones del area</p>
        </article>
      </section>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
        <section className="xl:col-span-8 sovereign-card !p-0 overflow-hidden">
          <div className="p-6 border-b border-black/5 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
            <div>
              <h2 className="font-headline text-2xl text-[#041627]">
                Trial Balance · {areaData?.encabezado.area_code || selectedArea} - {areaData?.encabezado.nombre || getLsName(selectedArea)}
              </h2>
              <p className="text-xs uppercase tracking-[0.14em] text-slate-500 mt-1">
                {areaData?.encabezado.actual_year || "Actual"} vs {areaData?.encabezado.anterior_year || "Anterior"}
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-sm">
              <thead className="bg-[#f1f4f6]/70">
                <tr>
                  <th className="px-6 py-4 text-left text-[10px] uppercase tracking-[0.16em] text-slate-500">Codigo</th>
                  <th className="px-6 py-4 text-left text-[10px] uppercase tracking-[0.16em] text-slate-500">Cuenta</th>
                  <th className="px-6 py-4 text-right text-[10px] uppercase tracking-[0.16em] text-slate-500">Actual</th>
                  <th className="px-6 py-4 text-right text-[10px] uppercase tracking-[0.16em] text-slate-500">Anterior</th>
                  <th className="px-6 py-4 text-right text-[10px] uppercase tracking-[0.16em] text-slate-500">Variacion</th>
                  <th className="px-6 py-4 text-center text-[10px] uppercase tracking-[0.16em] text-slate-500">%</th>
                  <th className="px-6 py-4 text-center text-[10px] uppercase tracking-[0.16em] text-slate-500">Estado</th>
                </tr>
              </thead>
              <tbody>
                {cuentas.map((row) => {
                  const varMonto = row.saldo_actual - row.saldo_anterior;
                  const varPct = variationPct(row.saldo_actual, row.saldo_anterior);
                  const flagged = Math.abs(varPct) > 10;
                  return (
                    <tr key={row.codigo} className={`border-b border-black/5 hover:bg-[#f7fafc] ${flagged ? "bg-[#ffdad6]/30" : "bg-white"}`}>
                      <td className={`px-6 py-4 font-body ${flagged ? "text-[#ba1a1a] font-semibold" : "text-slate-600"}`}>{row.codigo}</td>
                      <td className={`px-6 py-4 ${row.nivel <= 1 ? "font-headline text-lg font-semibold text-[#041627]" : "font-body text-sm text-slate-700 pl-10"}`}>
                        {row.nombre}
                      </td>
                      <td className={`px-6 py-4 text-right font-body ${moneyClass(row.saldo_actual)}`}>{formatMoney(row.saldo_actual)}</td>
                      <td className={`px-6 py-4 text-right font-body ${moneyClass(row.saldo_anterior)}`}>{formatMoney(row.saldo_anterior)}</td>
                      <td className={`px-6 py-4 text-right font-body ${moneyClass(varMonto)}`}>{formatMoney(varMonto)}</td>
                      <td className={`px-6 py-4 text-center font-semibold ${flagged ? "text-[#ba1a1a]" : "text-slate-600"}`}>{varPct.toFixed(1)}%</td>
                      <td className="px-6 py-4 text-center">
                        <span className={`material-symbols-outlined text-base ${flagged ? "text-[#ba1a1a]" : "text-emerald-700"}`}>
                          {flagged ? "warning" : "verified"}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {areaError ? <div className="p-4 text-sm text-amber-700 bg-amber-50 border-t border-amber-200">{areaError}</div> : null}
        </section>

        <aside className="xl:col-span-4">
          <div className="rounded-editorial bg-[#041627] text-white p-6 shadow-editorial sticky top-24">
            <div className="flex items-center gap-3 mb-6">
              <span className="material-symbols-outlined text-[#89d3d4]" style={{ fontVariationSettings: "'FILL' 1" }}>
                smart_toy
              </span>
              <h3 className="font-headline text-2xl text-[#a5eff0]">Socio AI - Guia de Aseveraciones</h3>
            </div>
            <p className="text-[11px] text-[#89d3d4] mb-4">Base deterministica del motor (catalogo tecnico), no respuesta generativa.</p>

            <div className="space-y-4">
              {(areaData?.aseveraciones ?? []).slice(0, 3).map((a, idx) => (
                <article key={`${a.nombre}-${idx}`} className="bg-white/5 p-4 rounded-xl border-l-2 border-[#89d3d4]">
                  <p className="text-[10px] uppercase tracking-[0.14em] text-[#a5eff0] font-bold">{a.nombre}</p>
                  <p className="text-xs text-slate-200 mt-2 leading-relaxed">{a.descripcion}</p>
                </article>
              ))}
              {(areaData?.aseveraciones ?? []).length === 0 ? (
                <p className="text-sm text-slate-300">Sin hallazgos automaticos para esta area.</p>
              ) : null}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
