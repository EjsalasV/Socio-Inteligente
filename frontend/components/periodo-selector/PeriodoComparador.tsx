'use client';

import { useEffect, useState } from 'react';
import { useAuditContext } from '@/lib/hooks/useAuditContext';

interface PeriodoData {
  periodo: string;
  fecha: string;
  snapshot_exists: boolean;
}

interface ComparisonSnapshot {
  periodo: string;
  activo: number;
  pasivo: number;
  patrimonio: number;
  ingresos: number;
  resultado_periodo: number;
  ratio_values?: Record<string, number>;
  top_areas?: Array<Record<string, any>>;
  hallazgos_count: number;
}

interface DeltaValue {
  valor_absoluto: number;
  porcentaje: number;
  mejoró: boolean;
}

interface Deltas {
  activo: DeltaValue;
  pasivo: DeltaValue;
  patrimonio: DeltaValue;
  ingresos: DeltaValue;
  resultado_periodo: DeltaValue;
  hallazgos_count_delta: number;
}

export function PeriodoComparador() {
  const { clienteId } = useAuditContext();
  const [periodos, setPeriodos] = useState<PeriodoData[]>([]);
  const [selectedPeriodo, setSelectedPeriodo] = useState<string>('');
  const [currentSnapshot, setCurrentSnapshot] = useState<ComparisonSnapshot | null>(null);
  const [previousSnapshot, setPreviousSnapshot] = useState<ComparisonSnapshot | null>(null);
  const [deltas, setDeltas] = useState<Deltas | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Cargar períodos disponibles
  useEffect(() => {
    if (!clienteId) return;

    const fetchPeriodos = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/clientes/${clienteId}/historicos`);
        const data = await response.json();
        if (data.status === 'ok' && data.data?.periodos) {
          setPeriodos(data.data.periodos);
          if (data.data.periodos.length > 0) {
            setSelectedPeriodo(data.data.periodos[0].periodo);
          }
        }
      } catch (err) {
        setError(`Error cargando períodos: ${String(err)}`);
      } finally {
        setLoading(false);
      }
    };

    fetchPeriodos();
  }, [clienteId]);

  // Cargar período anterior cuando cambia la selección
  useEffect(() => {
    if (!clienteId || !selectedPeriodo) return;

    const loadPreviousPeriod = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/clientes/${clienteId}/load-previous-period`, {
          method: 'POST',
        });
        const data = await response.json();
        if (data.status === 'ok' && data.data?.snapshot) {
          setPreviousSnapshot(data.data.snapshot);
          // Calcular deltas
          if (currentSnapshot && data.data.snapshot) {
            calculateDeltas(currentSnapshot, data.data.snapshot);
          }
        }
      } catch (err) {
        setError(`Error cargando período anterior: ${String(err)}`);
      } finally {
        setLoading(false);
      }
    };

    loadPreviousPeriod();
  }, [selectedPeriodo, clienteId, currentSnapshot]);

  const calculateDeltas = (current: ComparisonSnapshot, previous: ComparisonSnapshot) => {
    const calc_delta = (actual: number, anterior: number) => {
      if (anterior === 0) {
        return {
          valor_absoluto: actual - anterior,
          porcentaje: 0,
          mejoró: actual > anterior,
        };
      }
      const pct = ((actual - anterior) / Math.abs(anterior)) * 100;
      return {
        valor_absoluto: actual - anterior,
        porcentaje: pct,
        mejoró: actual > anterior,
      };
    };

    setDeltas({
      activo: calc_delta(current.activo, previous.activo),
      pasivo: calc_delta(current.pasivo, previous.pasivo),
      patrimonio: calc_delta(current.patrimonio, previous.patrimonio),
      ingresos: calc_delta(current.ingresos, previous.ingresos),
      resultado_periodo: calc_delta(current.resultado_periodo, previous.resultado_periodo),
      hallazgos_count_delta: current.hallazgos_count - previous.hallazgos_count,
    });
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const getDeltaClass = (delta: number, mejoró: boolean) => {
    if (delta === 0) return 'text-gray-600';
    return mejoró ? 'text-green-600' : 'text-red-600';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-4">
        <p className="text-gray-500">Cargando períodos...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 p-4">
        <p className="text-sm text-red-700">{error}</p>
      </div>
    );
  }

  if (periodos.length === 0) {
    return (
      <div className="rounded-lg bg-yellow-50 p-4">
        <p className="text-sm text-yellow-700">No hay períodos anteriores disponibles para comparación</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 rounded-lg border border-gray-200 bg-white p-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Comparativo de Períodos</h3>
        <div className="flex items-center gap-4">
          <div className="flex flex-col gap-2">
            <label className="text-xs font-medium text-gray-600">Período actual</label>
            <select
              value={selectedPeriodo}
              onChange={(e) => setSelectedPeriodo(e.target.value)}
              className="rounded border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            >
              {periodos.map((p) => (
                <option key={p.periodo} value={p.periodo}>
                  {p.periodo}
                </option>
              ))}
            </select>
          </div>
          {previousSnapshot && (
            <div className="flex flex-col gap-2">
              <label className="text-xs font-medium text-gray-600">Período anterior</label>
              <div className="rounded border border-gray-300 bg-gray-50 px-3 py-2 text-sm text-gray-700">
                {previousSnapshot.periodo}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Comparativo de KPIs */}
      {deltas && previousSnapshot && (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-5">
          {/* Activo */}
          <div className="rounded border border-gray-200 bg-gray-50 p-4">
            <p className="text-xs font-medium text-gray-600">Activo</p>
            <p className="mt-1 text-lg font-bold text-gray-900">
              {currentSnapshot ? formatCurrency(currentSnapshot.activo) : 'N/A'}
            </p>
            {deltas && (
              <div className={`mt-2 text-sm font-semibold ${getDeltaClass(deltas.activo.valor_absoluto, deltas.activo.mejoró)}`}>
                <span>{deltas.activo.mejoró ? '↑' : '↓'}</span>
                {formatPercentage(deltas.activo.porcentaje)}
              </div>
            )}
          </div>

          {/* Pasivo */}
          <div className="rounded border border-gray-200 bg-gray-50 p-4">
            <p className="text-xs font-medium text-gray-600">Pasivo</p>
            <p className="mt-1 text-lg font-bold text-gray-900">
              {currentSnapshot ? formatCurrency(currentSnapshot.pasivo) : 'N/A'}
            </p>
            {deltas && (
              <div className={`mt-2 text-sm font-semibold ${getDeltaClass(deltas.pasivo.valor_absoluto, !deltas.pasivo.mejoró)}`}>
                <span>{deltas.pasivo.mejoró ? '↓' : '↑'}</span>
                {formatPercentage(Math.abs(deltas.pasivo.porcentaje))}
              </div>
            )}
          </div>

          {/* Patrimonio */}
          <div className="rounded border border-gray-200 bg-gray-50 p-4">
            <p className="text-xs font-medium text-gray-600">Patrimonio</p>
            <p className="mt-1 text-lg font-bold text-gray-900">
              {currentSnapshot ? formatCurrency(currentSnapshot.patrimonio) : 'N/A'}
            </p>
            {deltas && (
              <div className={`mt-2 text-sm font-semibold ${getDeltaClass(deltas.patrimonio.valor_absoluto, deltas.patrimonio.mejoró)}`}>
                <span>{deltas.patrimonio.mejoró ? '↑' : '↓'}</span>
                {formatPercentage(deltas.patrimonio.porcentaje)}
              </div>
            )}
          </div>

          {/* Resultado del Período */}
          <div className="rounded border border-gray-200 bg-gray-50 p-4">
            <p className="text-xs font-medium text-gray-600">Resultado Período</p>
            <p className="mt-1 text-lg font-bold text-gray-900">
              {currentSnapshot ? formatCurrency(currentSnapshot.resultado_periodo) : 'N/A'}
            </p>
            {deltas && (
              <div className={`mt-2 text-sm font-semibold ${getDeltaClass(deltas.resultado_periodo.valor_absoluto, deltas.resultado_periodo.mejoró)}`}>
                <span>{deltas.resultado_periodo.mejoró ? '↑' : '↓'}</span>
                {formatPercentage(deltas.resultado_periodo.porcentaje)}
              </div>
            )}
          </div>

          {/* Hallazgos */}
          <div className="rounded border border-gray-200 bg-gray-50 p-4">
            <p className="text-xs font-medium text-gray-600">Hallazgos</p>
            <p className="mt-1 text-lg font-bold text-gray-900">{currentSnapshot?.hallazgos_count || 0}</p>
            {deltas && (
              <div className={`mt-2 text-sm font-semibold ${getDeltaClass(deltas.hallazgos_count_delta, deltas.hallazgos_count_delta <= 0)}`}>
                {deltas.hallazgos_count_delta === 0 && <span>Sin cambios</span>}
                {deltas.hallazgos_count_delta > 0 && <span className="text-red-600">+{deltas.hallazgos_count_delta}</span>}
                {deltas.hallazgos_count_delta < 0 && <span className="text-green-600">{deltas.hallazgos_count_delta}</span>}
              </div>
            )}
          </div>
        </div>
      )}

      {!deltas && previousSnapshot && (
        <div className="rounded bg-blue-50 p-4">
          <p className="text-sm text-blue-700">Cargando comparación de períodos...</p>
        </div>
      )}
    </div>
  );
}
