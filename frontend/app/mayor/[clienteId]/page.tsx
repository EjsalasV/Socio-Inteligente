"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import DashboardSkeleton from "../../../components/dashboard/DashboardSkeleton";
import ErrorMessage from "../../../components/dashboard/ErrorMessage";
import MayorFilters from "../../../components/mayor/MayorFilters";
import MayorFindingsPanel from "../../../components/mayor/MayorFindingsPanel";
import MayorSummaryPanel from "../../../components/mayor/MayorSummaryPanel";
import MayorTable from "../../../components/mayor/MayorTable";
import { exportMayorFile, getMayorMovimientos, getMayorResumen, getMayorValidaciones } from "../../../lib/api/mayor";
import { useAuditContext } from "../../../lib/hooks/useAuditContext";
import type {
  MayorMovimientosParams,
  MayorMovimientosResponse,
  MayorResumenResponse,
  MayorValidacionesResponse,
} from "../../../types/mayor";

const DEFAULT_PAGE_SIZE = 25;

const EMPTY_MOVIMIENTOS: MayorMovimientosResponse = {
  items: [],
  total: 0,
  page: 1,
  page_size: DEFAULT_PAGE_SIZE,
  total_pages: 1,
  resumen_filtrado: {
    total_movimientos: 0,
    total_debe: 0,
    total_haber: 0,
    total_neto: 0,
    cuentas_distintas: 0,
    asientos_distintos: 0,
    fecha_min: "",
    fecha_max: "",
    monto_promedio: 0,
  },
  source: {
    cliente_id: "",
    source_file: "",
    source_path: "",
    source_format: "",
    signature: "",
    rows: 0,
    cache: "none",
  },
};

export default function MayorPage() {
  const { clienteId } = useAuditContext();
  const [filters, setFilters] = useState<MayorMovimientosParams>({
    page: 1,
    page_size: DEFAULT_PAGE_SIZE,
  });
  const [movimientos, setMovimientos] = useState<MayorMovimientosResponse>(EMPTY_MOVIMIENTOS);
  const [resumen, setResumen] = useState<MayorResumenResponse | null>(null);
  const [validaciones, setValidaciones] = useState<MayorValidacionesResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  const loadData = useCallback(
    async (params: MayorMovimientosParams, initial = false) => {
      if (!clienteId) return;
      if (initial) setIsLoading(true);
      else setIsRefreshing(true);
      setError("");
      try {
        const [mov, res, val] = await Promise.all([
          getMayorMovimientos(clienteId, params),
          getMayorResumen(clienteId),
          getMayorValidaciones(clienteId),
        ]);
        setMovimientos(mov);
        setResumen(res);
        setValidaciones(val);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "No se pudo cargar el módulo de mayor.";
        setError(msg);
      } finally {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    },
    [clienteId],
  );

  useEffect(() => {
    void loadData(filters, true);
  }, [filters, loadData]);

  const handleApplyFilters = (next: MayorMovimientosParams) => {
    setFilters((prev) => ({
      ...prev,
      ...next,
      page: 1,
      page_size: prev.page_size || DEFAULT_PAGE_SIZE,
    }));
  };

  const handleResetFilters = () => {
    setFilters({ page: 1, page_size: DEFAULT_PAGE_SIZE });
  };

  const handlePageChange = (nextPage: number) => {
    const safePage = Math.max(1, nextPage);
    setFilters((prev) => ({ ...prev, page: safePage }));
  };

  const handleExport = async (format: "csv" | "xlsx") => {
    if (!clienteId) return;
    setIsExporting(true);
    try {
      const { blob, filename } = await exportMayorFile(clienteId, {
        format,
        fecha_desde: filters.fecha_desde,
        fecha_hasta: filters.fecha_hasta,
        cuenta: filters.cuenta,
        ls: filters.ls,
        referencia: filters.referencia,
        texto: filters.texto,
        monto_min: filters.monto_min,
        monto_max: filters.monto_max,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "No se pudo exportar.";
      setError(msg);
    } finally {
      setIsExporting(false);
    }
  };

  const sourceLabel = useMemo(() => {
    if (!movimientos.source.source_file) return "Sin archivo fuente";
    return `${movimientos.source.source_file} (${movimientos.source.source_format || "N/A"})`;
  }, [movimientos.source.source_file, movimientos.source.source_format]);

  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <div className="pt-4 pb-10 space-y-6 max-w-[1600px]">
      <section className="space-y-2">
        <p className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">Motor contable / Mayor</p>
        <h1 className="font-headline text-5xl text-[#041627]">Libro Mayor</h1>
        <p className="text-sm text-slate-500">
          Fuente: <span className="font-semibold text-slate-700">{sourceLabel}</span> · cache{" "}
          <span className="font-semibold text-slate-700">{movimientos.source.cache || "N/A"}</span>
        </p>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => void handleExport("xlsx")}
            disabled={isExporting || isRefreshing}
            className="rounded-editorial px-4 py-2 text-xs uppercase tracking-[0.12em] font-bold text-white bg-[#0d9488] hover:bg-[#0b7e72] min-h-[44px] disabled:opacity-50"
          >
            {isExporting ? "Exportando..." : "Exportar XLSX"}
          </button>
          <button
            type="button"
            onClick={() => void handleExport("csv")}
            disabled={isExporting || isRefreshing}
            className="rounded-editorial px-4 py-2 text-xs uppercase tracking-[0.12em] font-bold text-slate-700 border border-[#041627]/20 hover:bg-[#f5f8fb] min-h-[44px] disabled:opacity-50"
          >
            CSV
          </button>
        </div>
      </section>

      <MayorFilters value={filters} onApply={handleApplyFilters} onReset={handleResetFilters} isLoading={isRefreshing} />

      <MayorSummaryPanel
        summary={movimientos.resumen_filtrado}
        globalSummary={resumen?.resumen ?? null}
        isLoading={isRefreshing}
      />

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
        <div className="xl:col-span-8">
          <MayorTable
            items={movimientos.items}
            total={movimientos.total}
            page={movimientos.page}
            pageSize={movimientos.page_size}
            totalPages={movimientos.total_pages}
            isLoading={isRefreshing}
            onPageChange={handlePageChange}
          />
        </div>
        <div className="xl:col-span-4">
          <MayorFindingsPanel validaciones={validaciones?.validaciones ?? null} isLoading={isRefreshing} />
        </div>
      </div>
    </div>
  );
}
