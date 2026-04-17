"use client";

import React, { useState, useEffect } from "react";

interface Papel {
  id: number;
  codigo: string;
  numero: string;
  ls: number;
  nombre: string;
  aseveracion: string;
  importancia: string;
  obligatorio: string;
  descripcion: string | null;
}

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
  const [papeles, setPapeles] = useState<Papel[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedPapelId, setExpandedPapelId] = useState<number | null>(null);
  const [observations, setObservations] = useState<{
    [key: number]: string;
  }>({});

  const linesOfAccount = [130, 140, 150, 160, 170, 180, 190, 200, 210, 220]; // Common L/S codes

  const handleFetchPapeles = async (ls: string) => {
    if (!ls) {
      setError("Selecciona una Línea de Cuenta");
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const response = await fetch(
        `/api/papeles-trabajo/${clienteId}/papeles-por-ls?ls=${ls}`
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData?.message || "Error cargando papeles de trabajo"
        );
      }

      const data = await response.json();
      setPapeles(data.data?.papeles || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
      setPapeles([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLSChange = (ls: string) => {
    setSelectedLS(ls);
    if (ls) {
      handleFetchPapeles(ls);
    }
  };

  const handleAddObservation = (papelId: number) => {
    const currentObs = observations[papelId] || "";
    const newObs = prompt("Agregar observación:", currentObs);
    if (newObs !== null) {
      setObservations((prev) => ({
        ...prev,
        [papelId]: newObs,
      }));
    }
  };

  const getImportanciaColor = (importancia: string) => {
    const colors: { [key: string]: string } = {
      CRITICO: "bg-red-100 border-red-300 text-red-900",
      ALTO: "bg-orange-100 border-orange-300 text-orange-900",
      MEDIO: "bg-yellow-100 border-yellow-300 text-yellow-900",
      BAJO: "bg-green-100 border-green-300 text-green-900",
    };
    return colors[importancia] || "bg-gray-100 border-gray-300 text-gray-900";
  };

  const getAseveracionBadge = (aseveracion: string) => {
    const badges: { [key: string]: string } = {
      EXISTENCIA: "🎯",
      INTEGRIDAD: "🔐",
      VALORACION: "💰",
      DERECHOS: "📜",
      PRESENTACION: "📋",
    };
    return badges[aseveracion] || "📌";
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-6 bg-white rounded-lg shadow">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Papeles de Trabajo - V1
        </h1>
        <p className="text-gray-600 mb-4">
          Área: <span className="font-semibold">{areaName}</span>
        </p>
        <p className="text-sm text-gray-500">
          Role: <span className="font-medium capitalize">{role}</span>
        </p>
      </div>

      {/* L/S Selector */}
      <div className="mb-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          📌 Seleccionar Línea de Cuenta (L/S)
        </h2>
        <div className="flex flex-wrap gap-3">
          {linesOfAccount.map((ls) => (
            <button
              key={ls}
              onClick={() => handleLSChange(ls.toString())}
              className={`px-4 py-2 rounded font-medium transition-colors ${
                selectedLS === ls.toString()
                  ? "bg-blue-600 text-white"
                  : "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
              }`}
            >
              L/S {ls}
            </button>
          ))}
        </div>
      </div>

      {/* Loading & Error States */}
      {isLoading && (
        <div className="text-center py-8">
          <p className="text-gray-600">Cargando papeles de trabajo...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-900">
          ❌ {error}
        </div>
      )}

      {/* Papeles List */}
      {!isLoading && papeles.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-xl font-bold text-gray-900">
            {papeles.length} Papeles en L/S {selectedLS}
          </h3>

          {papeles.map((papel) => (
            <div
              key={papel.id}
              className="border border-gray-300 rounded-lg bg-white hover:shadow-lg transition-shadow"
            >
              {/* Header del papel */}
              <div
                onClick={() =>
                  setExpandedPapelId(
                    expandedPapelId === papel.id ? null : papel.id
                  )
                }
                className="p-4 bg-gradient-to-r from-gray-50 to-gray-100 cursor-pointer flex justify-between items-center"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-xl font-bold text-gray-900">
                      {papel.codigo}
                    </span>
                    <span className="text-2xl">
                      {getAseveracionBadge(papel.aseveracion)}
                    </span>
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-semibold border ${getImportanciaColor(
                        papel.importancia
                      )}`}
                    >
                      {papel.importancia}
                    </span>
                    {papel.obligatorio === "SÍ" && (
                      <span className="px-3 py-1 bg-red-100 border border-red-300 text-red-900 rounded-full text-xs font-semibold">
                        OBLIGATORIO
                      </span>
                    )}
                  </div>
                  <h4 className="text-lg font-semibold text-gray-900">
                    {papel.nombre}
                  </h4>
                </div>
                <div className="text-2xl">
                  {expandedPapelId === papel.id ? "▼" : "▶"}
                </div>
              </div>

              {/* Contenido expandible */}
              {expandedPapelId === papel.id && (
                <div className="p-6 border-t border-gray-300 bg-white">
                  {/* Información del papel */}
                  <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                    <h5 className="font-semibold text-gray-900 mb-3">
                      📋 Información del Papel
                    </h5>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-gray-600 font-medium">Aseveración</p>
                        <p className="text-gray-900">{papel.aseveracion}</p>
                      </div>
                      <div>
                        <p className="text-gray-600 font-medium">Importancia</p>
                        <p className="text-gray-900">{papel.importancia}</p>
                      </div>
                      <div>
                        <p className="text-gray-600 font-medium">Obligatorio</p>
                        <p className="text-gray-900">{papel.obligatorio}</p>
                      </div>
                      <div>
                        <p className="text-gray-600 font-medium">Número</p>
                        <p className="text-gray-900">{papel.numero}</p>
                      </div>
                    </div>

                    {papel.descripcion && (
                      <div className="mt-4 pt-4 border-t border-gray-300">
                        <p className="text-gray-600 font-medium mb-2">
                          POR QUÉ (Motivo)
                        </p>
                        <p className="text-gray-900 leading-relaxed">
                          {papel.descripcion}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Observaciones */}
                  <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex justify-between items-center mb-3">
                      <h5 className="font-semibold text-gray-900">
                        💬 Observación ({role})
                      </h5>
                      <button
                        onClick={() => handleAddObservation(papel.id)}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-medium text-sm flex items-center gap-2"
                      >
                        ➕ Agregar Observación
                      </button>
                    </div>

                    {observations[papel.id] ? (
                      <div className="bg-white p-3 rounded border border-blue-300 text-sm text-gray-900">
                        {observations[papel.id]}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-600 italic">
                        No hay observación aún
                      </p>
                    )}
                  </div>

                  {/* Acciones */}
                  <div className="flex gap-2">
                    <button className="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded font-medium">
                      ✓ Guardar Observación
                    </button>
                    <button className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-900 px-4 py-2 rounded font-medium">
                      📥 Descargar Modelo
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {!isLoading && papeles.length === 0 && selectedLS && (
        <div className="text-center py-12 text-gray-600">
          <p className="text-lg mb-2">
            No se encontraron papeles para L/S {selectedLS}
          </p>
          <p className="text-sm">Selecciona otra línea de cuenta</p>
        </div>
      )}

      {!selectedLS && !isLoading && (
        <div className="text-center py-12 text-gray-600">
          <p className="text-lg">Selecciona una Línea de Cuenta para comenzar</p>
        </div>
      )}
    </div>
  );
}
