"use client";

import { useEffect, useMemo, useState } from "react";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import ContextualHelp from "../../../components/help/ContextualHelp";
import { formatMoney, moneyClass } from "../../../lib/formatters";
import { useAreaDetail } from "../../../lib/hooks/useAreaDetail";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import { useDashboard } from "../../../lib/hooks/useDashboard";
import { useLearningRole } from "../../../lib/hooks/useLearningRole";
import { getLsName, getLsOptions, getLsShortName, normalizeLsCode } from "../../../lib/lsCatalog";

function variationPct(actual: number, previous: number): number {
  if (previous === 0) return actual === 0 ? 0 : 100;
  return ((actual - previous) / Math.abs(previous)) * 100;
}

function buildFinancialCriterion(data: {
  riesgoGlobal: string;
  mpGlobal: number | null;
  meGlobal: number | null;
  tbStage: string;
  topVarianceAccount: string | null;
  sector: string;
}): string {
  const alertas = data.topVarianceAccount
    ? `La cuenta con mayor variación es ${data.topVarianceAccount}, ` +
      `que requiere revisión analítica prioritaria conforme a NIA 520.`
    : "No se detectaron variaciones significativas en las cuentas principales.";

  const matText = data.mpGlobal
    ? `La materialidad de planeación es de $${data.mpGlobal.toLocaleString("es-CO")} ` +
      `y la de ejecución de $${(data.meGlobal ?? 0).toLocaleString("es-CO")}.`
    : "Materialidad pendiente de definir en el perfil del encargo.";

  return `Encargo en sector ${data.sector} con riesgo global ${data.riesgoGlobal}. ` +
    `${matText} ` +
    `Balance en estado: ${data.tbStage}. ` +
    `${alertas} ` +
    `Se recomienda verificar integridad del patrimonio y consistencia entre ` +
    `el estado de resultados y las variaciones del balance general.`;
}

export default function EstadosFinancierosPage() {
  const { clienteId } = useAuditContext();
  const { data: dashboard, isLoading, error } = useDashboard(clienteId);
  const { role } = useLearningRole();

  const baseOptions = useMemo(() => getLsOptions().map((x) => normalizeLsCode(x.codigo)), []);
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
        ? "Estimación automática del motor"
        : "Pendiente de definición";
  const materialidadDetalle = dashboard?.materialidad_detalle;
  const materialidadFormula = materialidadDetalle?.base_usada
    ? `${materialidadDetalle.porcentaje_rango_min.toFixed(1)}% - ${materialidadDetalle.porcentaje_rango_max.toFixed(1)}% de ${materialidadDetalle.base_usada}`
    : "Sin formula tecnica disponible";

  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorMessage message={error} />;
  if (!dashboard) return <ErrorMessage message="No hay datos de estados financieros para este cliente." />;
  const topVariation = cuentasComparativas[0];
  const criterioPrincipal = buildFinancialCriterion({
    riesgoGlobal: dashboard.riesgo_global || "No determinado",
    mpGlobal: dashboard.materialidad_global > 0 ? dashboard.materialidad_global : null,
    meGlobal: me > 0 ? me : null,
    tbStage: tbStageLabel,
    topVarianceAccount: topVariation ? `${topVariation.codigo} - ${topVariation.nombre}` : null,
    sector: dashboard.sector || "No determinado",
  });
  const coherenciaResumen = `Activo ${formatMoney(dashboard.activo)} · Pasivo ${formatMoney(dashboard.pasivo)} · Patrimonio ${formatMoney(dashboard.patrimonio)} · Riesgo global ${dashboard.riesgo_global}.`;

  return (
    <div className="pt-4 pb-10 space-y-8 max-w-screen-2xl">
      <header className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          <h1 data-tour="estados-title" className="font-headline text-4xl text-[#041627]">Estados Financieros - Análisis Comparativo</h1>
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

      <ContextualHelp
        title="Ayuda del modulo Estados Financieros"
        items={[
          {
            label: "Materialidad",
            description:
              "Usa MP, ME y umbral trivial como referencia para evaluar desviaciones.",
          },
          {
            label: "Análisis comparativo",
            description:
              "Compara año actual vs anterior para identificar rubros con mayor impacto.",
          },
          {
            label: "Alertas de integridad",
            description:
              "Resume focos de riesgo para ajustar alcance de pruebas y revelaciones.",
          },
        ]}
      />

      {/* Panel de rol */}
      {role === "junior" && (
        <section className="bg-[#a5eff0]/10 border border-[#a5eff0]/30 rounded-xl p-6 space-y-4">
          <div className="flex items-start gap-4">
            <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#041627] text-[#a5eff0] text-xs font-bold mt-0.5">NIA</span>
            <div>
              <p className="text-xs uppercase tracking-[0.15em] text-[#041627]/60 font-bold mb-1">Cómo usar esta pantalla — Vista Junior</p>
              <p className="text-sm text-[#041627] leading-relaxed">
                Esta tabla compara el <strong>año actual vs el año anterior</strong> cuenta por cuenta. Las filas en rojo tienen variaciones superiores a la materialidad de ejecución o más de 10% — esas son las que debes revisar primero.
              </p>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {[
              { num: 1, texto: "Identifica las filas resaltadas en rojo. Esas cuentas superan la materialidad y requieren procedimientos analíticos (NIA 520).", nia: "NIA 520" },
              { num: 2, texto: "Compara la variación en $ con la materialidad de ejecución mostrada arriba. Si la supera, debes obtener evidencia adicional.", nia: "NIA 320" },
              { num: 3, texto: "Lee el Criterio del Socio AI — resume el enfoque recomendado para este cliente según el riesgo global y el sector.", nia: "NIA 315" },
            ].map((step) => (
              <div key={step.nia} className="flex gap-3 p-4 bg-white rounded-lg border border-slate-100">
                <span className="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#041627] text-white text-xs font-bold mt-0.5">{step.num}</span>
                <div>
                  <p className="text-xs text-slate-700 leading-relaxed">{step.texto}</p>
                  <span className="inline-block mt-2 px-2 py-0.5 rounded-full bg-[#041627]/10 text-[#041627] text-[10px] font-bold uppercase">{step.nia}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {role === "socio" && (
        <section className="rounded-xl p-6 bg-[#001919] border border-[#a5eff0]/20 shadow-md text-white">
          <p className="text-[10px] uppercase tracking-[0.2em] text-[#a5eff0] font-bold mb-3">Resumen Ejecutivo — Vista Socio</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="bg-white/10 rounded-lg p-4">
              <p className="text-[10px] uppercase tracking-[0.12em] text-slate-300">Activo Total</p>
              <p className="font-headline text-xl mt-1 font-semibold text-white">{formatMoney(dashboard.activo, "USD", 0)}</p>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <p className="text-[10px] uppercase tracking-[0.12em] text-slate-300">Pasivo</p>
              <p className="font-headline text-xl mt-1 font-semibold text-white">{formatMoney(dashboard.pasivo, "USD", 0)}</p>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <p className="text-[10px] uppercase tracking-[0.12em] text-slate-300">Patrimonio</p>
              <p className="font-headline text-xl mt-1 font-semibold text-white">{formatMoney(dashboard.patrimonio, "USD", 0)}</p>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <p className="text-[10px] uppercase tracking-[0.12em] text-slate-300">Materialidad</p>
              <p className="font-headline text-xl mt-1 font-semibold text-white">{formatMoney(me, "USD", 0)}</p>
            </div>
          </div>
          <p className="text-[10px] uppercase tracking-[0.12em] text-slate-400 mb-1">Estado del balance</p>
          <p className="text-sm text-slate-200">{tbStageLabel} · Riesgo global: <strong className="text-white">{(dashboard.riesgo_global || "N/D").toUpperCase()}</strong></p>
        </section>
      )}

      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <article data-tour="estados-materialidad" className="sovereign-card border-l-4 border-[#041627]">
          <p className="text-[10px] uppercase tracking-[0.16em] text-slate-500 font-bold">Materialidad de Planeación</p>
          <h3 className="font-headline text-3xl text-[#041627] mt-3">{formatMoney(dashboard.materialidad_global)}</h3>
          <p className="text-xs text-slate-500 mt-2">{materialidadOrigenLabel}</p>
          <p className="text-xs text-slate-500 mt-1">{materialidadFormula}</p>
        </article>

        <article className="sovereign-card border-l-4 border-[#89d3d4]">
          <p className="text-[10px] uppercase tracking-[0.16em] text-slate-500 font-bold">Materialidad de Ejecución</p>
          <h3 className="font-headline text-3xl text-[#041627] mt-3">{formatMoney(me)}</h3>
          <p className="text-xs text-slate-500 mt-2">75% de MP</p>
        </article>

        <article className="rounded-editorial bg-[#1a2b3c] p-6 shadow-editorial text-white">
          <p className="text-[10px] uppercase tracking-[0.16em] text-[#89d3d4] font-bold">Umbral Trivial</p>
          <h3 className="font-headline text-3xl mt-3">{formatMoney(triviales)}</h3>
          <p className="text-xs text-slate-300 mt-2">5% de MP</p>
        </article>
      </section>

      <section data-tour="estados-table" className="bg-[#f1f4f6] rounded-editorial p-1">
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
                  <th className="px-8 py-4 text-right text-[11px] uppercase tracking-[0.14em] text-slate-500">Año actual</th>
                  <th className="px-8 py-4 text-right text-[11px] uppercase tracking-[0.14em] text-slate-500">Año anterior</th>
                  <th className="px-8 py-4 text-right text-[11px] uppercase tracking-[0.14em] text-slate-500">Variación $</th>
                  <th className="px-8 py-4 text-right text-[11px] uppercase tracking-[0.14em] text-slate-500">Variación %</th>
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
            <h3 className="font-headline text-2xl text-[#041627]">Criterio del Socio AI</h3>
          </div>
          <div className="space-y-4">
            <div className="bg-[#f1f4f6] rounded-editorial p-5 border-l-4 border-[#89d3d4]">
              <p className="text-xs uppercase tracking-[0.12em] text-slate-500 font-bold mb-2">Análisis principal</p>
              <p className="text-sm text-slate-700 leading-relaxed">
                {criterioPrincipal}
              </p>
            </div>
            <div className="bg-[#f1f4f6] rounded-editorial p-5">
              <p className="text-xs uppercase tracking-[0.12em] text-slate-500 font-bold mb-2">Coherencia financiera</p>
              <p className="text-sm text-slate-700 leading-relaxed">
                {coherenciaResumen}
              </p>
            </div>
          </div>
        </article>

        <article data-tour="estados-alertas" className="lg:col-span-2 rounded-editorial bg-[#1a2b3c] text-white p-8 shadow-editorial">
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
              <p className="text-sm text-slate-300">Sin alertas automáticas para esta área.</p>
            ) : null}
          </div>
        </article>
      </section>
    </div>
  );
}
