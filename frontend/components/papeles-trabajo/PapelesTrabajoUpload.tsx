"use client";

import React, { useState } from "react";

interface PapelesTrabajoUploadProps {
  clienteId: string;
  areaCode: string;
  areaName: string;
  role: "junior" | "semi" | "senior" | "socio";
  onUploadSuccess?: (fileId: number, version: number) => void;
}

export function PapelesTrabajoUpload({
  clienteId,
  areaCode,
  areaName,
  role,
  onUploadSuccess,
}: PapelesTrabajoUploadProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [selectedLS, setSelectedLS] = useState<string>("");
  const [uploadStatus, setUploadStatus] = useState<{
    type: "success" | "error" | "pending";
    message: string;
    details?: any;
  } | null>(null);

  const handleDownloadTemplate = async (ls?: string) => {
    try {
      setIsLoading(true);
      let url = `/api/papeles-trabajo/${clienteId}/plantilla`;
      // Only add ls parameter if it's a valid number
      if (ls && ls.trim() !== "") {
        const lsNum = parseInt(ls, 10);
        if (!isNaN(lsNum)) {
          url += `?ls=${lsNum}`;
        }
      }

      const response = await fetch(url, {
        method: "GET",
      });

      if (!response.ok) {
        let errorMessage = "Error descargando plantilla";
        try {
          const errorData = await response.json();
          errorMessage = errorData?.message || errorData?.detail?.message || errorMessage;
        } catch {
          // Si no es JSON, usar mensaje por defecto
        }
        throw new Error(errorMessage);
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      const lsNum = ls && ls.trim() !== "" ? parseInt(ls, 10) : null;
      link.download = lsNum
        ? `plantilla_papeles_trabajo_LS${lsNum}.xlsx`
        : `plantilla_papeles_trabajo_completa.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);

      setUploadStatus({
        type: "success",
        message: lsNum
          ? `Plantilla descargada correctamente (L/S ${lsNum})`
          : "Plantilla descargada correctamente",
      });
    } catch (error) {
      setUploadStatus({
        type: "error",
        message: `Error descargando plantilla: ${error instanceof Error ? error.message : "Error desconocido"}`,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.currentTarget.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileUpload = async (file: File) => {
    // Only Junior and Semi can upload (Senior/Socio only review)
    if (role === "senior" || role === "socio") {
      setUploadStatus({
        type: "error",
        message: "No tienes permisos para subir archivos. Solo Junior y Semi pueden crear/subir.",
      });
      return;
    }

    if (!file.name.endsWith(".xlsx") && !file.name.endsWith(".xls")) {
      setUploadStatus({
        type: "error",
        message: "Por favor selecciona un archivo Excel (.xlsx o .xls)",
      });
      return;
    }

    try {
      setIsLoading(true);
      setUploadStatus({
        type: "pending",
        message: "Subiendo archivo...",
      });

      const formData = new FormData();
      formData.append("file", file);
      formData.append("area_code", areaCode);
      formData.append("area_name", areaName);

      const response = await fetch(`/api/papeles-trabajo/${clienteId}/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.message || `Error: ${response.statusText}`
        );
      }

      const data = await response.json();

      setUploadStatus({
        type: "success",
        message: "Archivo subido correctamente",
        details: {
          fileId: data.data.file_id,
          version: data.data.version,
          parsedRows: data.data.parsed_rows,
          summary: data.data.summary,
        },
      });

      if (onUploadSuccess) {
        onUploadSuccess(data.data.file_id, data.data.version);
      }
    } catch (error) {
      setUploadStatus({
        type: "error",
        message: `Error subiendo archivo: ${error instanceof Error ? error.message : "Error desconocido"}`,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-6 bg-white rounded-lg shadow">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Papeles de Trabajo v2
        </h2>
        <p className="text-gray-600">
          Área: <span className="font-semibold">{areaName}</span> ({areaCode})
        </p>
        <p className="text-sm text-gray-500 mt-1">
          Role: <span className="font-medium capitalize">{role}</span>
        </p>
      </div>

      {/* Download Template Section */}
      <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">📋 Descargar Plantilla Excel</h3>
        <p className="text-sm text-gray-600 mb-4">
          Descarga la plantilla Excel vacía con estructura correcta para llenarla offline. Puedes descargar la plantilla completa o solo para una línea de cuenta específica.
        </p>

        <div className="flex flex-col md:flex-row gap-4 items-start md:items-end">
          {/* L/S Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Línea de Cuenta (L/S) - Opcional
            </label>
            <input
              type="number"
              min="100"
              max="999"
              placeholder="ej: 130, 140"
              value={selectedLS}
              onChange={(e) => setSelectedLS(e.target.value)}
              disabled={isLoading}
              className="px-3 py-2 border border-gray-300 rounded font-medium text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">Déjalo vacío para descargar todas las líneas</p>
          </div>

          {/* Download Buttons */}
          <div className="flex gap-2">
            <button
              onClick={() => handleDownloadTemplate(selectedLS)}
              disabled={isLoading}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-medium disabled:opacity-50"
            >
              ⬇️ Descargar {selectedLS ? `L/S ${selectedLS}` : "Todas"}
            </button>
          </div>
        </div>
      </div>

      {/* Upload Area */}
      {role !== "senior" && role !== "socio" ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            isDragging
              ? "border-blue-500 bg-blue-50"
              : "border-gray-300 bg-gray-50"
          }`}
        >
          <div className="mx-auto mb-4 text-5xl text-gray-400">⬆️</div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Sube tu archivo Excel rellenado
          </h3>
          <p className="text-gray-600 mb-4">
            Arrastra y suelta tu archivo Excel aquí, o haz clic para seleccionar
          </p>

          <input
            type="file"
            accept=".xlsx,.xls"
            onChange={handleFileInputChange}
            disabled={isLoading}
            className="hidden"
            id="file-input"
          />
          <label htmlFor="file-input" className="inline-block bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-medium cursor-pointer">
            Seleccionar archivo
          </label>

          <p className="text-xs text-gray-500 mt-4">
            Formatos aceptados: .xlsx, .xls
          </p>
        </div>
      ) : (
        <div className="border border-blue-200 bg-blue-50 rounded-lg p-6 text-center">
          <div className="mx-auto mb-3 text-4xl">📄</div>
          <p className="text-gray-700 font-medium">
            Solo Junior y Semi pueden subir archivos.
          </p>
          <p className="text-sm text-gray-600 mt-1">
            Como {role}, puedes revisar, modificar campos y firmar los papeles.
          </p>
        </div>
      )}

      {/* Status Messages */}
      {uploadStatus && (
        <div
          className={`mt-6 p-4 rounded-lg flex items-start gap-3 ${
            uploadStatus.type === "success"
              ? "bg-green-50 border border-green-200"
              : uploadStatus.type === "error"
              ? "bg-red-50 border border-red-200"
              : "bg-yellow-50 border border-yellow-200"
          }`}
        >
          {uploadStatus.type === "success" && <span className="text-green-600 flex-shrink-0 mt-0.5">✓</span>}
          {uploadStatus.type === "error" && <span className="text-red-600 flex-shrink-0 mt-0.5">✗</span>}
          {uploadStatus.type === "pending" && (
            <div className="w-5 h-5 flex-shrink-0 mt-0.5">
              <div className="animate-spin h-5 w-5 border-2 border-yellow-500 border-t-transparent rounded-full" />
            </div>
          )}
          <div>
            <p
              className={`font-medium ${
                uploadStatus.type === "success"
                  ? "text-green-900"
                  : uploadStatus.type === "error"
                  ? "text-red-900"
                  : "text-yellow-900"
              }`}
            >
              {uploadStatus.message}
            </p>
            {uploadStatus.details && (
              <div className="text-sm text-gray-700 mt-2 space-y-1">
                <p>ID Archivo: {uploadStatus.details.fileId}</p>
                <p>Versión: {uploadStatus.details.version}</p>
                <p>Filas parseadas: {uploadStatus.details.parsedRows}</p>
                {uploadStatus.details.summary && (
                  <p>
                    Completadas: {uploadStatus.details.summary.completed}/
                    {uploadStatus.details.summary.total_rows}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
