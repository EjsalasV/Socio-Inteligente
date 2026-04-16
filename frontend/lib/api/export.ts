/**
 * Export API client for generating PDF reports
 */

export type ReportType = 'resumen_ejecutivo' | 'informe_completo' | 'hallazgos';
export type Role = 'junior' | 'semi' | 'senior' | 'socio';

export interface ExportRequest {
  report_type: ReportType;
  role: Role;
  incluir_comparativa?: boolean;
  fecha_periodo?: string;
}

export interface ExportResponse {
  filename: string;
  tamanio_bytes: number;
  tamanio_kb: number;
  report_type: ReportType;
  role: Role;
  generado_en: string;
}

/**
 * Generate and download PDF report
 */
export async function exportReport(
  clienteId: string,
  options: ExportRequest
): Promise<Blob> {
  const res = await fetch(`/api/reportes/${clienteId}/export/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(options),
  });

  if (!res.ok) {
    throw new Error(`Export failed: ${res.status}`);
  }

  return await res.blob();
}

/**
 * Generate report and get metadata (without immediate download)
 */
export async function generateReport(
  clienteId: string,
  options: ExportRequest
): Promise<ExportResponse> {
  const res = await fetch(`/api/reportes/${clienteId}/export`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(options),
  });

  if (!res.ok) {
    throw new Error(`Report generation failed: ${res.status}`);
  }

  const data = await res.json();
  return data.data;
}

/**
 * Download file blob to user's device
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}
