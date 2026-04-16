'use client';

import { useEffect, useState } from 'react';

interface MissingProcedure {
  procedure_id: string;
  procedure_name: string;
  obligatorio: boolean;
  executed: boolean;
  status: string;
}

interface ClosingAreaWarningProps {
  clienteId: string;
  areaCode: string;
  onClose?: (forceClose: boolean) => void;
  open?: boolean;
}

export function ClosingAreaWarning({ clienteId, areaCode, onClose, open = false }: ClosingAreaWarningProps) {
  const [isOpen, setIsOpen] = useState(open);
  const [missingProcedures, setMissingProcedures] = useState<MissingProcedure[]>([]);
  const [loading, setLoading] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Validar cierre cuando se abre el diálogo
  useEffect(() => {
    if (!isOpen || !clienteId || !areaCode) return;

    const validateClosure = async () => {
      try {
        setLoading(true);
        const response = await fetch(
          `/areas/${clienteId}/${areaCode}/finalize?force_close=false`,
          { method: 'POST' }
        );
        const data = await response.json();
        if (data.data?.missing_procedures) {
          setMissingProcedures(data.data.missing_procedures);
        }
      } catch (err) {
        setError(`Error validando cierre: ${String(err)}`);
      } finally {
        setLoading(false);
      }
    };

    validateClosure();
  }, [isOpen, clienteId, areaCode]);

  const handleForceClose = async () => {
    try {
      setConfirming(true);
      const response = await fetch(
        `/areas/${clienteId}/${areaCode}/finalize?force_close=true`,
        { method: 'POST' }
      );
      const data = await response.json();
      if (data.status === 'ok') {
        setIsOpen(false);
        onClose?.(true);
      } else {
        setError(data.message || 'Error cerrando área');
      }
    } catch (err) {
      setError(`Error: ${String(err)}`);
    } finally {
      setConfirming(false);
    }
  };

  const handleCancel = () => {
    setIsOpen(false);
    onClose?.(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg">
        <h2 className="text-lg font-semibold text-gray-900">
          {missingProcedures.length > 0 ? '⚠️ Procedimientos Faltantes' : 'Cerrar Área'}
        </h2>

        {loading && (
          <div className="mt-4 text-center text-sm text-gray-500">
            Validando cierre del área...
          </div>
        )}

        {!loading && missingProcedures.length > 0 && (
          <>
            <div className="mt-4">
              <p className="text-sm text-gray-700">
                Los siguientes procedimientos obligatorios no han sido ejecutados:
              </p>
              <ul className="mt-3 space-y-2">
                {missingProcedures.map((proc) => (
                  <li key={proc.procedure_id} className="flex items-start gap-2 rounded bg-yellow-50 p-2">
                    <span className="mt-0.5 flex-shrink-0 text-red-500">✗</span>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{proc.procedure_id}</p>
                      <p className="text-xs text-gray-600">{proc.procedure_name}</p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-4 rounded bg-yellow-50 p-3">
              <p className="text-xs text-yellow-800">
                Puedes cerrar el área igualmente (se registrará la advertencia), o cancelar para completar los procedimientos.
              </p>
            </div>

            <div className="mt-6 flex gap-3">
              <button
                onClick={handleCancel}
                disabled={confirming}
                className="flex-1 rounded border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleForceClose}
                disabled={confirming}
                className="flex-1 rounded bg-orange-600 px-4 py-2 text-sm font-medium text-white hover:bg-orange-700 disabled:opacity-50"
              >
                {confirming ? 'Cerrando...' : 'Cerrar Igualmente'}
              </button>
            </div>
          </>
        )}

        {!loading && missingProcedures.length === 0 && (
          <>
            <p className="mt-4 text-sm text-gray-700">
              Todos los procedimientos obligatorios han sido ejecutados. El área puede ser cerrada.
            </p>
            <div className="mt-6 flex gap-3">
              <button
                onClick={handleCancel}
                className="flex-1 rounded border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleForceClose}
                className="flex-1 rounded bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700"
              >
                Confirmar Cierre
              </button>
            </div>
          </>
        )}

        {error && (
          <div className="mt-4 rounded bg-red-50 p-3">
            <p className="text-xs text-red-700">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}
