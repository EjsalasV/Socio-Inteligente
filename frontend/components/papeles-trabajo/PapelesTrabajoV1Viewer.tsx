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

const linesOfAccount = [
  { ls: 130, name: "Cuentas por Cobrar" },
  { ls: 140, name: "Inventarios" },
  { ls: 150, name: "Propiedad Planta Equipo" },
  { ls: 160, name: "Cuentas por Pagar" },
  { ls: 170, name: "Pasivos Laborales" },
  { ls: 180, name: "Deuda Financiera" },
  { ls: 190, name: "Patrimonio" },
  { ls: 200, name: "Ingresos" },
  { ls: 210, name: "Costos" },
  { ls: 220, name: "Gastos" },
];

export function PapelesTrabajoV1Viewer({
  clienteId,
  areaName,
  role,
}: PapelesTrabajoV1ViewerProps) {
  const [papelesByLS, setPapelesByLS] = useState<{ [key: number]: Papel[] }>({});
  const [expandedLS, setExpandedLS] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [observations, setObservations] = useState<{ [key: number]: string }>({});

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

  const getImportanciaColor = (importancia: string) => {
    const colors: { [key: string]: string } = {
      CRITICO: "bg-red-50 text-red-700 border-red-200",
      ALTO: "bg-orange-50 text-orange-700 border-orange-200",
      MEDIO: "bg-yellow-50 text-yellow-700 border-yellow-200",
      BAJO: "bg-green-50 text-green-700 border-green-200",
    };
    return colors[importancia] || "bg-gray-50 text-gray-700 border-gray-200";
  };

  const handleDownloadPapel = async (ls: number) => {
    try {
      const response = await fetch(
        `/api/papeles-trabajo/${clienteId}/plantilla?ls=${ls}`
      );
      if (!response.ok) throw new Error("Error descargando");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `plantilla_LS${ls}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Error descargando plantilla");
    }
  };

  const handleAddObservation = (papelId: number) => {
    const current = observations[papelId] || "";
    const newText = prompt("Agregar observación:", current);
    if (newText !== null) {
      setObservations((prev) => ({ ...prev, [papelId]: newText }));
    }
  };

  const toggleLS = async (ls: number) => {
    if (expandedLS === ls) {
      setExpandedLS(null);
      return;
    }

    if (papelesByLS[ls]) {
      setExpandedLS(ls);
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(
        `/api/papeles-trabajo/${clienteId}/papeles-por-ls?ls=${ls}`
      );
      if (!response.ok) throw new Error("Error");

      const data = await response.json();
      setPapelesByLS((prev) => ({
        ...prev,
        [ls]: data.data?.papeles || [],
      }));
      setExpandedLS(ls);
    } catch (err) {
      alert("Error cargando papeles");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-gray-900">Papeles Modelo por L/S</h3>
        <a
          href="#"
          onClick={(e) => {
            e.preventDefault();
            // Descargar todos
            alert("Descarga de plantilla completa - próximamente");
          }}
          className="text-sm text-blue-600 hover:underline"
        >
          Descargar todos
        </a>
      </div>

      {linesOfAccount.map(({ ls, name }) => {
        const isExpanded = expandedLS === ls;
        const papeles = papelesByLS[ls] || [];

        return (
          <article
            key={ls}
            className="sovereign-card border border-[#041627]/20 overflow-hidden"
          >
            <button
              onClick={() => toggleLS(ls)}
              className="w-full text-left p-4 bg-gradient-to-r from-[#f8fbff] to-white hover:bg-[#f1f4f6] transition-colors flex items-center justify-between"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-lg text-[#041627]">{ls}</span>
                  <span className="text-gray-600 font-semibold">{name}</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {papeles.length > 0
                    ? `${papeles.length} papeles de trabajo`
                    : "Cargando..."}
                </p>
              </div>
              <span className="text-xl text-gray-600">
                {isExpanded ? "▼" : "▶"}
              </span>
            </button>

            {isExpanded && (
              <div className="border-t border-[#041627]/10 p-4 space-y-4 bg-white">
                {isLoading ? (
                  <p className="text-sm text-gray-600 text-center py-4">
                    Cargando papeles...
                  </p>
                ) : papeles.length === 0 ? (
                  <p className="text-sm text-gray-600 text-center py-4">
                    No hay papeles para esta L/S
                  </p>
                ) : (
                  papeles.map((papel) => (
                    <div
                      key={papel.id}
                      className="border border-gray-200 rounded-lg p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
                    >
                      {/* Header */}
                      <div className="flex items-start justify-between gap-2 mb-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-bold text-[#041627]">
                              {papel.codigo}
                            </span>
                            <span className="text-xl">
                              {getAseveracionBadge(papel.aseveracion)}
                            </span>
                            <span
                              className={`text-xs font-semibold px-2 py-1 rounded border ${getImportanciaColor(
                                papel.importancia
                              )}`}
                            >
                              {papel.importancia}
                            </span>
                          </div>
                          <p className="text-sm font-semibold text-[#041627]">
                            {papel.nombre}
                          </p>
                          {papel.descripcion && (
                            <p className="text-xs text-gray-600 mt-2">
                              {papel.descripcion}
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Observación */}
                      <div className="bg-white border border-blue-200 rounded p-3 mb-3">
                        <div className="flex items-center justify-between mb-2">
                          <label className="text-xs font-semibold text-gray-700">
                            💬 Observación ({role})
                          </label>
                          <button
                            onClick={() => handleAddObservation(papel.id)}
                            className="text-sm bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded flex items-center gap-1"
                          >
                            ➕
                          </button>
                        </div>
                        {observations[papel.id] ? (
                          <p className="text-xs text-gray-900 bg-blue-50 p-2 rounded">
                            {observations[papel.id]}
                          </p>
                        ) : (
                          <p className="text-xs text-gray-500 italic">
                            Sin observación
                          </p>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="flex gap-2">
                        <button className="flex-1 text-xs font-semibold px-2 py-1 bg-green-600 hover:bg-green-700 text-white rounded">
                          ✓ Guardar
                        </button>
                        <button
                          onClick={() => handleDownloadPapel(papel.ls)}
                          className="flex-1 text-xs font-semibold px-2 py-1 bg-gray-300 hover:bg-gray-400 text-gray-900 rounded"
                        >
                          📥 Descargar
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </article>
        );
      })}
    </div>
  );
}
