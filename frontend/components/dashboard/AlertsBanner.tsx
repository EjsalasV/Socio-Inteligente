'use client';

import { useEffect, useState } from 'react';
import { useAuditContext } from '@/lib/hooks/useAuditContext';

interface Alert {
  id: string;
  tipo: string;
  severidad: string;
  mensaje: string;
  fecha_creada: string;
  metadata?: Record<string, any>;
}

interface AlertStats {
  total_criticos: number;
  total_altos: number;
}

export function AlertsBanner() {
  const { clienteId } = useAuditContext();
  const [alertas, setAlertas] = useState<Alert[]>([]);
  const [stats, setStats] = useState<AlertStats>({ total_criticos: 0, total_altos: 0 });
  const [expandedAlert, setExpandedAlert] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Cargar alertas al montar
  useEffect(() => {
    if (!clienteId) return;

    const fetchAlertas = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/alertas/${clienteId}`);
        const data = await response.json();
        if (data.status === 'ok' && data.data?.alertas) {
          setAlertas(data.data.alertas);
          setStats({
            total_criticos: data.data.total_criticos || 0,
            total_altos: data.data.total_altos || 0,
          });
        }
      } catch (err) {
        setError(`Error cargando alertas: ${String(err)}`);
      } finally {
        setLoading(false);
      }
    };

    fetchAlertas();
    // Recargar cada 5 minutos
    const interval = setInterval(fetchAlertas, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [clienteId]);

  const handleResolveAlert = async (alertId: string) => {
    try {
      const response = await fetch(`/api/alertas/${alertId}/resolve`, {
        method: 'POST',
      });
      if (response.ok) {
        // Actualizar lista
        setAlertas(alertas.filter((a) => a.id !== alertId));
      }
    } catch (err) {
      setError(`Error resolviendo alerta: ${String(err)}`);
    }
  };

  const getSeverityStyles = (severidad: string) => {
    switch (severidad) {
      case 'CRITICO':
        return 'bg-red-50 border-l-4 border-red-500';
      case 'ALTO':
        return 'bg-orange-50 border-l-4 border-orange-500';
      case 'MEDIO':
        return 'bg-yellow-50 border-l-4 border-yellow-500';
      case 'BAJO':
        return 'bg-blue-50 border-l-4 border-blue-500';
      default:
        return 'bg-gray-50 border-l-4 border-gray-500';
    }
  };

  const getSeverityTextColor = (severidad: string) => {
    switch (severidad) {
      case 'CRITICO':
        return 'text-red-800';
      case 'ALTO':
        return 'text-orange-800';
      case 'MEDIO':
        return 'text-yellow-800';
      case 'BAJO':
        return 'text-blue-800';
      default:
        return 'text-gray-800';
    }
  };

  if (loading) {
    return <div className="text-center text-sm text-gray-500">Cargando alertas...</div>;
  }

  if (alertas.length === 0 && !error) {
    return null; // No mostrar nada si no hay alertas
  }

  // Mostrar banner rojo si hay críticos
  if (stats.total_criticos > 0) {
    return (
      <div className="rounded-lg bg-red-50 p-4 ring-1 ring-red-200">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex-shrink-0">
              <svg className="h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-red-800">
                Alertas Críticas ({stats.total_criticos})
              </h3>
              <p className="mt-1 text-sm text-red-700">Requieren atención inmediata</p>
              <div className="mt-3 space-y-2">
                {alertas
                  .filter((a) => a.severidad === 'CRITICO')
                  .map((alert) => (
                    <div key={alert.id} className="rounded border border-red-200 bg-white p-2">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="text-xs font-semibold text-red-900">{alert.tipo}</p>
                          <p className="mt-1 text-xs text-red-700">{alert.mensaje}</p>
                          <p className="mt-1 text-xs text-gray-500">
                            {new Date(alert.fecha_creada).toLocaleString()}
                          </p>
                        </div>
                        <button
                          onClick={() => handleResolveAlert(alert.id)}
                          className="flex-shrink-0 rounded bg-red-100 px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-200"
                        >
                          Resolver
                        </button>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Mostrar banner naranja si hay altos
  if (stats.total_altos > 0) {
    return (
      <div className="rounded-lg bg-orange-50 p-4 ring-1 ring-orange-200">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex-shrink-0">
              <svg className="h-5 w-5 text-orange-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-orange-800">
                Alertas Altas ({stats.total_altos})
              </h3>
              <p className="mt-1 text-sm text-orange-700">Necesitan revisión</p>
              <div className="mt-3 space-y-2">
                {alertas
                  .filter((a) => a.severidad === 'ALTO')
                  .map((alert) => (
                    <div key={alert.id} className="rounded border border-orange-200 bg-white p-2">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="text-xs font-semibold text-orange-900">{alert.tipo}</p>
                          <p className="mt-1 text-xs text-orange-700">{alert.mensaje}</p>
                        </div>
                        <button
                          onClick={() => handleResolveAlert(alert.id)}
                          className="flex-shrink-0 rounded bg-orange-100 px-2 py-1 text-xs font-medium text-orange-700 hover:bg-orange-200"
                        >
                          Resolver
                        </button>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        </div>
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

  return null;
}
