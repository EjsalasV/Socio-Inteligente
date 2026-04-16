'use client';

import React, { useState } from 'react';
import { useLearningRole } from '@/lib/hooks/useLearningRole';

interface ExportButtonProps {
  clienteId: string;
  disabled?: boolean;
  className?: string;
}

type ReportType = 'resumen_ejecutivo' | 'informe_completo' | 'hallazgos';

export default function ExportButton({ clienteId, disabled = false, className = '' }: ExportButtonProps) {
  const { role } = useLearningRole();
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [reportType, setReportType] = useState<ReportType>('resumen_ejecutivo');
  const [incluirComparativa, setIncluirComparativa] = useState(false);

  async function handleExport() {
    if (!clienteId) return;

    try {
      setIsLoading(true);

      const response = await fetch(`/api/reportes/${clienteId}/export/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          report_type: reportType,
          role: role,
          incluir_comparativa: incluirComparativa,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate report');
      }

      // Get filename from content-disposition header
      const contentDisposition = response.headers.get('content-disposition');
      const filename = contentDisposition
        ? contentDisposition.split('filename=')[1]?.replace(/"/g, '')
        : `Reporte_${role}_${new Date().toISOString().slice(0, 10)}.pdf`;

      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setIsOpen(false);
    } catch (error) {
      console.error('Export error:', error);
      alert('Error al generar el reporte. Intenta de nuevo.');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        disabled={disabled || isLoading}
        className={`inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors ${className}`}
      >
        <span>📥</span>
        {isLoading ? 'Generando...' : 'Descargar PDF'}
      </button>

      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Descargar Reporte</h2>

            <div className="space-y-4">
              {/* Report Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tipo de Reporte
                </label>
                <select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value as ReportType)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="resumen_ejecutivo">Resumen Ejecutivo (1-2 páginas)</option>
                  <option value="informe_completo">Informe Completo (10+ páginas)</option>
                  <option value="hallazgos">Solo Hallazgos</option>
                </select>
              </div>

              {/* Comparativa */}
              <div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={incluirComparativa}
                    onChange={(e) => setIncluirComparativa(e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-sm text-gray-700">Incluir comparativa con período anterior</span>
                </label>
              </div>

              {/* Role Info */}
              <div className="bg-blue-50 p-3 rounded-lg">
                <p className="text-xs text-gray-600">
                  <span className="font-medium">Rol:</span> {role.charAt(0).toUpperCase() + role.slice(1)}
                </p>
                <p className="text-xs text-gray-600 mt-1">
                  Se incluirá el nivel de detalle correspondiente a tu rol.
                </p>
              </div>

              {/* Confirmation */}
              <div className="bg-yellow-50 p-3 rounded-lg border border-yellow-200">
                <p className="text-xs text-yellow-800">
                  ¿Descargar reporte final de {new Date().getFullYear()}?
                </p>
              </div>
            </div>

            {/* Buttons */}
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setIsOpen(false)}
                disabled={isLoading}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleExport}
                disabled={isLoading}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {isLoading ? 'Generando...' : 'Descargar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
