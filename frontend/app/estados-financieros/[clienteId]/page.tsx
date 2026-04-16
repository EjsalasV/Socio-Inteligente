"use client";

import { useEffect, useMemo, useState } from "react";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import EstadosFinancierosJunior from "../../../components/estados-financieros/EstadosFinancierosJunior";
import EstadosFinancierosSemi from "../../../components/estados-financieros/EstadosFinancierosSemi";
import EstadosFinancierosSenior from "../../../components/estados-financieros/EstadosFinancierosSenior";
import EstadosFinancierosSocio from "../../../components/estados-financieros/EstadosFinancierosSocio";
import type { FinancialRatio, RatioStatus } from "../../../components/estados-financieros/types";
import { createPeriodSnapshot, getHistoricos, type PeriodInfo } from "../../../lib/api";
import { formatMoney } from "../../../lib/formatters";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import { useDashboard } from "../../../lib/hooks/useDashboard";
import { type LearningRole, useLearningRole } from "../../../lib/hooks/useLearningRole";

const AC_CODES = new Set(["140", "141", "130", "130.1", "130.2", "120", "110", "135", "136"]);
const PC_CODES = new Set(["425", "300.1", "324", "410", "420"]);
const INV_CODES = new Set(["110"]);

function buildRatios(params: {
  activo: number;
  pasivo: number;
  patrimonio: number;
  ingresos: number;
  resultado_periodo: number;
  ac: number;
  pc: number;
  inventarios: number;
}): FinancialRatio[] {
  const { activo, pasivo, patrimonio, ingresos, resultado_periodo, ac, pc, inventarios } = params;
  const list: FinancialRatio[] = [];

  if (ac > 0 && pc > 0) {
    const liquidez = ac / pc;
    list.push({
      label: "Liquidez Corriente",
      formatted: `${liquidez.toFixed(2)}x`,
      rawValue: liquidez,
      benchmark: "> 1.5x óptimo",
      status: liquidez >= 1.5 ? "ok" : liquidez >= 1.0 ? "warning" : "risk",
      audit_note:
        liquidez < 1.0
          ? "Activo corriente no cubre pasivo corriente. Evaluar continuidad del negocio (NIA 570)."
          : liquidez < 1.5
            ? "Liquidez ajustada. Revisar plazos de cobro y pago."
            : "Liquidez suficiente para cubrir obligaciones de corto plazo.",
      nia: "NIA 570",
      category: "liquidez",
    });

    const pruebaAcida = (ac - inventarios) / pc;
    list.push({
      label: "Prueba Ácida",
      formatted: `${pruebaAcida.toFixed(2)}x`,
      rawValue: pruebaAcida,
      benchmark: "> 1.0x óptimo",
      status: pruebaAcida >= 1.0 ? "ok" : pruebaAcida >= 0.7 ? "warning" : "risk",
      audit_note:
        pruebaAcida < 0.7
          ? "Alta dependencia de inventarios para cubrir deuda corriente. Revisar valuación y rotación."
          : pruebaAcida < 1.0
            ? "Liquidez inmediata ajustada. Monitorear rotación de cartera."
            : "Liquidez inmediata adecuada sin depender de inventarios.",
      nia: "NIA 500",
      category: "liquidez",
    });
  }

  if (ac > 0 || pc > 0) {
    const capitalTrabajo = ac - pc;
    list.push({
      label: "Capital de Trabajo",
      formatted: formatMoney(capitalTrabajo, "USD", 0),
      rawValue: capitalTrabajo,
      benchmark: "Debe ser positivo",
      status: capitalTrabajo > 0 ? "ok" : "risk",
      audit_note:
        capitalTrabajo < 0
          ? "Capital de trabajo negativo: obligaciones corrientes superan activos líquidos."
          : "La empresa mantiene colchón operativo positivo.",
      nia: "NIA 570",
      category: "liquidez",
    });
  }

  if (activo > 0) {
    const endeudamiento = pasivo / activo;
    list.push({
      label: "Endeudamiento",
      formatted: `${(endeudamiento * 100).toFixed(1)}%`,
      rawValue: endeudamiento,
      benchmark: "< 60% óptimo",
      status: endeudamiento < 0.6 ? "ok" : endeudamiento < 0.75 ? "warning" : "risk",
      audit_note:
        endeudamiento > 0.75
          ? "Alta dependencia de deuda. Revisar incentivos de fraude y presión por resultados (NIA 240)."
          : endeudamiento > 0.6
            ? "Endeudamiento elevado. Verificar cumplimiento de covenants bancarios."
            : "Nivel de deuda manejable dentro del activo total.",
      nia: "NIA 240",
      category: "solvencia",
    });
  }

  if (patrimonio > 0) {
    const apalancamiento = pasivo / patrimonio;
    list.push({
      label: "Apalancamiento",
      formatted: `${apalancamiento.toFixed(2)}x`,
      rawValue: apalancamiento,
      benchmark: "< 1.0x óptimo",
      status: apalancamiento < 1.0 ? "ok" : apalancamiento < 2.0 ? "warning" : "risk",
      audit_note:
        apalancamiento > 2.0
          ? "Deuda superior al doble del patrimonio. Riesgo significativo de incumplimiento."
          : apalancamiento > 1.0
            ? "Pasivos por encima del patrimonio. Vigilar estructura de financiamiento."
            : "Estructura de capital equilibrada.",
      nia: "NIA 315",
      category: "solvencia",
    });
  }

  if (activo > 0 && resultado_periodo !== 0) {
    const roa = resultado_periodo / activo;
    list.push({
      label: "ROA",
      formatted: `${(roa * 100).toFixed(1)}%`,
      rawValue: roa,
      benchmark: "> 3% óptimo",
      status: roa >= 0.03 ? "ok" : roa >= 0 ? "warning" : "risk",
      audit_note:
        roa < 0
          ? "Resultado negativo: destruye valor sobre activos."
          : roa < 0.03
            ? "Rentabilidad baja sobre activos."
            : "Rentabilidad sobre activos aceptable.",
      nia: "NIA 240",
      category: "rentabilidad",
    });
  }

  if (patrimonio > 0 && resultado_periodo !== 0) {
    const roe = resultado_periodo / patrimonio;
    list.push({
      label: "ROE",
      formatted: `${(roe * 100).toFixed(1)}%`,
      rawValue: roe,
      benchmark: "> 5% óptimo",
      status: roe >= 0.05 ? "ok" : roe >= 0 ? "warning" : "risk",
      audit_note:
        roe < 0
          ? "Resultado negativo: erosiona el patrimonio."
          : roe < 0.05
            ? "Retorno bajo para accionistas."
            : "Retorno al accionista adecuado.",
      nia: "NIA 570",
      category: "rentabilidad",
    });
  }

  if (ingresos > 0) {
    const margenNeto = resultado_periodo / ingresos;
    list.push({
      label: "Margen Neto",
      formatted: `${(margenNeto * 100).toFixed(1)}%`,
      rawValue: margenNeto,
      benchmark: "> 5% óptimo",
      status: margenNeto >= 0.05 ? "ok" : margenNeto >= 0 ? "warning" : "risk",
      audit_note:
        margenNeto < 0
          ? "Empresa opera a pérdida. Revisar reconocimiento de ingresos y gastos (NIA 540)."
          : margenNeto < 0.05
            ? "Margen ajustado. Errores en ingresos/gastos impactan materialmente el resultado."
            : "Margen neto saludable.",
      nia: "NIA 540",
      category: "rentabilidad",
    });
  }

  return list;
}

function normalizeRole(role: LearningRole): LearningRole {
  if (role === "junior" || role === "semi" || role === "senior" || role === "socio") {
    return role;
  }
  return "semi";
}

function statusChipTone(status: RatioStatus): string {
  if (status === "ok") return "bg-emerald-100 text-emerald-800";
  if (status === "warning") return "bg-amber-100 text-amber-800";
  return "bg-rose-100 text-rose-800";
}

function formatPeriodo(periodo: string): string {
  // "202412" → "Dic 2024"  |  "202501" → "Ene 2025"
  if (periodo.length !== 6) return periodo;
  const months = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"];
  const y = periodo.slice(0, 4);
  const m = parseInt(periodo.slice(4, 6), 10);
  return `${months[m - 1] ?? m} ${y}`;
}

export default function IndicesFinancierosPage() {
  const { clienteId } = useAuditContext();
  const { data, isLoading, error } = useDashboard(clienteId);
  const { role } = useLearningRole();
  const activeRole = normalizeRole(role);

  // ── Gestión de períodos ──────────────────────────────────────
  const [historicos, setHistoricos] = useState<PeriodInfo[]>([]);
  const [savingSnapshot, setSavingSnapshot] = useState(false);
  const [snapshotMsg, setSnapshotMsg] = useState<{ type: "ok" | "err"; text: string } | null>(null);
  const [showSnapshotForm, setShowSnapshotForm] = useState(false);
  const [snapshotPeriodo, setSnapshotPeriodo] = useState<string>(() => {
    const now = new Date();
    return `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, "0")}`;
  });

  useEffect(() => {
    if (!clienteId) return;
    getHistoricos(clienteId)
      .then((list) => setHistoricos(list))
      .catch(() => setHistoricos([]));
  }, [clienteId]);

  async function handleSaveSnapshot(): Promise<void> {
    if (!clienteId || !data) return;
    setSavingSnapshot(true);
    setSnapshotMsg(null);
    try {
      await createPeriodSnapshot(clienteId, snapshotPeriodo, {
        activo: data.activo,
        pasivo: data.pasivo,
        patrimonio: data.patrimonio,
        ingresos: data.ingresos,
        resultado_periodo: data.resultado_periodo,
        hallazgos_count: 0,
      });
      setSnapshotMsg({ type: "ok", text: `Período ${formatPeriodo(snapshotPeriodo)} guardado correctamente.` });
      setShowSnapshotForm(false);
      // Refresh list
      const updated = await getHistoricos(clienteId);
      setHistoricos(updated);
    } catch (e) {
      setSnapshotMsg({ type: "err", text: e instanceof Error ? e.message : "Error al guardar período." });
    } finally {
      setSavingSnapshot(false);
    }
  }

  const { ac, pc, inventarios } = useMemo(() => {
    let acTotal = 0;
    let pcTotal = 0;
    let inventariosTotal = 0;
    for (const area of data?.top_areas ?? []) {
      if (!area.con_saldo) continue;
      const code = area.codigo.toString().trim();
      const base = code.includes(".") ? code.split(".")[0] : code;
      if (AC_CODES.has(code) || AC_CODES.has(base)) acTotal += Math.abs(area.saldo_total);
      if (PC_CODES.has(code) || PC_CODES.has(base)) pcTotal += Math.abs(area.saldo_total);
      if (INV_CODES.has(code) || INV_CODES.has(base)) inventariosTotal += Math.abs(area.saldo_total);
    }
    return { ac: acTotal, pc: pcTotal, inventarios: inventariosTotal };
  }, [data]);

  const ratios = useMemo(() => {
    if (!data) return [];
    return buildRatios({
      activo: data.activo,
      pasivo: data.pasivo,
      patrimonio: data.patrimonio,
      ingresos: data.ingresos,
      resultado_periodo: data.resultado_periodo,
      ac,
      pc,
      inventarios,
    });
  }, [data, ac, pc, inventarios]);

  const riskRatios = ratios.filter((ratio) => ratio.status === "risk");
  const warningRatios = ratios.filter((ratio) => ratio.status === "warning");

  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorMessage message={error} />;
  if (!data) return <ErrorMessage message="No hay datos para analizar." />;

  return (
    <div className="pt-4 pb-10 space-y-8 max-w-screen-2xl">

      {/* ── Panel de períodos históricos ── */}
      <section className="rounded-xl border border-slate-200/60 bg-white shadow-sm p-4">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <p className="text-[10px] uppercase tracking-[0.16em] text-slate-500 font-bold">Períodos guardados</p>
            <p className="text-sm text-slate-600 mt-0.5">
              {historicos.length === 0
                ? "Aún no hay períodos guardados. Guarda el estado actual para comparar entre años."
                : `${historicos.length} período${historicos.length > 1 ? "s" : ""} guardado${historicos.length > 1 ? "s" : ""}: ${historicos.map((h) => formatPeriodo(h.periodo)).join(" · ")}`}
            </p>
          </div>
          <button
            type="button"
            onClick={() => { setShowSnapshotForm((v) => !v); setSnapshotMsg(null); }}
            className="inline-flex items-center gap-2 rounded-lg border border-[#041627]/20 bg-[#041627] text-white px-3 py-2 text-xs font-semibold uppercase tracking-[0.12em] hover:opacity-90"
          >
            <span className="material-symbols-outlined text-sm">bookmark_add</span>
            Guardar período actual
          </button>
        </div>

        {showSnapshotForm && data ? (
          <div className="mt-4 pt-4 border-t border-slate-200 flex flex-wrap items-end gap-4">
            <label className="flex flex-col gap-1">
              <span className="text-[11px] uppercase tracking-[0.12em] text-slate-500 font-bold">Período (YYYYMM)</span>
              <input
                type="text"
                value={snapshotPeriodo}
                onChange={(e) => setSnapshotPeriodo(e.target.value.replace(/\D/g, "").slice(0, 6))}
                placeholder="202412"
                maxLength={6}
                className="w-32 rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono focus:border-[#89d3d4] focus:outline-none"
              />
              <span className="text-[10px] text-slate-400">Ej: 202412 = Dic 2024</span>
            </label>
            <div className="flex flex-col gap-1 text-xs text-slate-600">
              <span>Se guardará el estado actual:</span>
              <span>Activo <b>{formatMoney(data.activo, "USD", 0)}</b> · Pasivo <b>{formatMoney(data.pasivo, "USD", 0)}</b> · Ingresos <b>{formatMoney(data.ingresos, "USD", 0)}</b></span>
            </div>
            <button
              type="button"
              disabled={savingSnapshot || snapshotPeriodo.length !== 6}
              onClick={() => { void handleSaveSnapshot(); }}
              className="inline-flex items-center gap-2 rounded-lg bg-emerald-700 text-white px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] disabled:opacity-50 hover:bg-emerald-800"
            >
              {savingSnapshot ? "Guardando..." : "Confirmar"}
            </button>
          </div>
        ) : null}

        {snapshotMsg ? (
          <p className={`mt-3 text-xs font-medium ${snapshotMsg.type === "ok" ? "text-emerald-700" : "text-rose-700"}`}>
            {snapshotMsg.type === "ok" ? "✓" : "✗"} {snapshotMsg.text}
          </p>
        ) : null}

        {historicos.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {historicos.map((h) => (
              <span key={h.periodo} className="inline-flex items-center gap-1.5 rounded-full border border-[#89d3d4]/50 bg-[#a5eff0]/10 px-3 py-1 text-[11px] font-semibold text-[#041627]">
                <span className="material-symbols-outlined text-xs">check_circle</span>
                {formatPeriodo(h.periodo)}
              </span>
            ))}
          </div>
        )}
      </section>

      <header className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          <p className="text-[10px] uppercase tracking-[0.16em] text-slate-500 font-bold">Análisis Financiero</p>
          <h1 className="font-headline text-4xl text-[#041627] mt-1">Índices Financieros</h1>
          <p className="text-sm text-slate-500 mt-2">
            {data.nombre_cliente} · {data.periodo || "Periodo actual"} · Sector: {data.sector || "N/D"}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {riskRatios.length > 0 && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-rose-100 text-rose-800 text-xs font-bold">
              <span className="h-2 w-2 rounded-full bg-rose-600 inline-block" />
              {riskRatios.length} señal{riskRatios.length > 1 ? "es" : ""} de riesgo
            </span>
          )}
          {warningRatios.length > 0 && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-amber-100 text-amber-800 text-xs font-bold">
              <span className="h-2 w-2 rounded-full bg-amber-500 inline-block" />
              {warningRatios.length} en atención
            </span>
          )}
          <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-[0.08em] ${statusChipTone(data.riesgo_global === "ALTO" ? "risk" : data.riesgo_global === "MEDIO" ? "warning" : "ok")}`}>
            Riesgo global {data.riesgo_global}
          </span>
        </div>
      </header>

      <section className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {[
          { label: "Activo Total", value: formatMoney(data.activo, "USD", 0) },
          { label: "Pasivo Total", value: formatMoney(data.pasivo, "USD", 0) },
          { label: "Patrimonio", value: formatMoney(data.patrimonio, "USD", 0) },
          { label: "Ingresos", value: formatMoney(data.ingresos, "USD", 0) },
          {
            label: "Resultado",
            value: formatMoney(data.resultado_periodo, "USD", 0),
            highlight: data.resultado_periodo < 0,
          },
        ].map((kpi) => (
          <div key={kpi.label} className="bg-white rounded-xl p-5 shadow-sm border border-slate-200/60">
            <p className="text-[10px] uppercase tracking-[0.15em] text-slate-500 font-bold">{kpi.label}</p>
            <p className={`font-headline text-2xl mt-1 font-semibold ${kpi.highlight ? "text-rose-700" : "text-[#041627]"}`}>
              {kpi.value}
            </p>
          </div>
        ))}
      </section>

      {ratios.length === 0 ? (
        <section className="bg-white rounded-xl p-10 text-center border border-slate-200/50 shadow-sm">
          <p className="text-slate-500 text-sm">No hay suficientes datos para calcular índices.</p>
          <p className="text-xs text-slate-400 mt-2">
            Carga el Trial Balance y configura la materialidad en el perfil para habilitar el análisis.
          </p>
        </section>
      ) : activeRole === "junior" ? (
        <EstadosFinancierosJunior ratios={ratios} />
      ) : activeRole === "semi" ? (
        <EstadosFinancierosSemi ratios={ratios} />
      ) : activeRole === "senior" ? (
        <EstadosFinancierosSenior ratios={ratios} />
      ) : (
        <EstadosFinancierosSocio ratios={ratios} />
      )}

      {ratios.length > 0 && (
        <p className="text-[11px] text-slate-400">
          Los indicadores de liquidez se estiman a partir de áreas con saldo cargadas en Trial Balance clasificadas por código LS.
          Activo, pasivo, patrimonio e ingresos provienen de los datos del encargo.
        </p>
      )}
    </div>
  );
}
