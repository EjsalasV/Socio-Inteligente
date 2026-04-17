"use client";

import React, { useState } from "react";

interface PapelesTrabajoV1ViewerProps {
  clienteId: string;
  areaName: string;
  role: "junior" | "semi" | "senior" | "socio";
}

export function PapelesTrabajoV1Viewer({
  clienteId,
  areaName,
  role,
}: PapelesTrabajoV1ViewerProps) {
  const [selectedLS, setSelectedLS] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const linesOfAccount = [130, 140, 150, 160, 170, 180, 190, 200, 210, 220];

  const handleDownload = async (ls: string) => {
    if (!ls) {
      setMessage({ type: "error", text: "Selecciona una L/S" });
      return;
    }

    try {
      setIsLoading(true);
      const url = `/api/papeles-trabajo/${clienteId}/plantilla?ls=${ls}`;
      const response = await fetch(url);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData?.message || "Error descargando plantilla");
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = `plantilla_papeles_LS${ls}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);

      setMessage({
        type: "success",
        text: `✓ Plantilla L/S ${ls} descargada`,
      });
    } catch (err) {
      setMessage({
        type: "error",
        text: err instanceof Error ? err.message : "Error desconocido",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full">
      <div className="flex flex-col md:flex-row gap-4 items-start md:items-end">
        {/* L/S Selector */}
        <div className="flex-1">
          <label className="block text-sm font-semibold text-gray-900 mb-2">
            Línea de Cuenta (L/S)
          </label>
          <div className="flex flex-wrap gap-2">
            {linesOfAccount.map((ls) => (
              <button
                key={ls}
                onClick={() => setSelectedLS(ls.toString())}
                className={`px-3 py-2 rounded font-medium transition-colors text-sm ${
                  selectedLS === ls.toString()
                    ? "bg-blue-600 text-white"
                    : "bg-gray-200 text-gray-800 hover:bg-gray-300"
                }`}
              >
                {ls}
              </button>
            ))}
          </div>
        </div>

        {/* Download Button */}
        <button
          onClick={() => handleDownload(selectedLS)}
          disabled={isLoading || !selectedLS}
          className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded font-medium flex items-center gap-2"
        >
          {isLoading ? "⏳ Descargando..." : "⬇️ Descargar Plantilla"}
        </button>
      </div>

      {/* Message */}
      {message && (
        <div
          className={`mt-4 p-3 rounded text-sm ${
            message.type === "success"
              ? "bg-green-100 text-green-900 border border-green-300"
              : "bg-red-100 text-red-900 border border-red-300"
          }`}
        >
          {message.text}
        </div>
      )}
    </div>
  );
}
