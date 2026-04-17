"use client";

import React, { useEffect, useState } from "react";

interface Modification {
  timestamp: string;
  user_role: string;
  field: string;
  old_value: any;
  new_value: any;
}

interface ModificacionesHistorialProps {
  fileId: number;
  modifications?: Modification[];
}

export function ModificacionesHistorial({
  fileId,
  modifications = [],
}: ModificacionesHistorialProps) {
  const [sortedMods, setSortedMods] = useState<Modification[]>([]);

  useEffect(() => {
    // Sort by timestamp, most recent first
    const sorted = [...modifications].sort(
      (a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
    setSortedMods(sorted);
  }, [modifications]);

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString("es-ES", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case "junior":
        return "bg-blue-100 text-blue-800 border-blue-300";
      case "semi":
        return "bg-purple-100 text-purple-800 border-purple-300";
      case "senior":
        return "bg-orange-100 text-orange-800 border-orange-300";
      case "socio":
        return "bg-red-100 text-red-800 border-red-300";
      default:
        return "bg-gray-100 text-gray-800 border-gray-300";
    }
  };

  const getRoleLabel = (role: string) => {
    const labels: Record<string, string> = {
      junior: "Junior",
      semi: "Semi-Senior",
      senior: "Senior",
      socio: "Socio",
    };
    return labels[role] || role;
  };

  if (sortedMods.length === 0) {
    return (
      <div className="w-full max-w-4xl mx-auto p-6 bg-white rounded-lg shadow">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-gray-600 text-xl">📋</span>
          <h2 className="text-xl font-bold text-gray-900">Historial de Modificaciones</h2>
        </div>
        <p className="text-gray-500 text-center py-8">
          No hay modificaciones registradas para este archivo
        </p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-4xl mx-auto p-6 bg-white rounded-lg shadow">
      <div className="flex items-center gap-2 mb-6">
        <span className="text-gray-600 text-xl">📋</span>
        <h2 className="text-xl font-bold text-gray-900">Historial de Modificaciones</h2>
        <span className="ml-auto bg-gray-200 text-gray-700 px-3 py-1 rounded-full text-sm font-medium">
          {sortedMods.length} cambios
        </span>
      </div>

      <div className="space-y-4">
        {sortedMods.map((mod, index) => (
          <div
            key={index}
            className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
          >
            {/* Header: Role, Field, Timestamp */}
            <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
              <div className="flex items-center gap-3 flex-wrap">
                <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getRoleColor(mod.user_role)}`}>
                  {getRoleLabel(mod.user_role)}
                </span>
                <span className="font-semibold text-gray-900">
                  {mod.field}
                </span>
              </div>

              <div className="flex items-center gap-1 text-xs text-gray-500">
                🗓️ {formatTimestamp(mod.timestamp)}
              </div>
            </div>

            {/* Before/After Values */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
              {/* Old Value */}
              <div className="bg-red-50 border border-red-200 rounded p-3">
                <p className="text-xs font-semibold text-red-700 mb-1">Valor anterior</p>
                <p className="text-sm text-gray-800 break-words font-mono">
                  {mod.old_value !== null && mod.old_value !== undefined
                    ? String(mod.old_value)
                    : "(vacío)"}
                </p>
              </div>

              {/* Arrow */}
              <div className="flex md:hidden items-center justify-center py-2">
                <div className="text-2xl text-gray-400">→</div>
              </div>

              {/* New Value */}
              <div className="bg-green-50 border border-green-200 rounded p-3">
                <p className="text-xs font-semibold text-green-700 mb-1">Valor nuevo</p>
                <p className="text-sm text-gray-800 break-words font-mono">
                  {mod.new_value !== null && mod.new_value !== undefined
                    ? String(mod.new_value)
                    : "(vacío)"}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Summary Stats */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          {["junior", "semi", "senior", "socio"].map((role) => {
            const count = sortedMods.filter((m) => m.user_role === role).length;
            return (
              <div key={role}>
                <p className="text-xs text-gray-500 font-semibold uppercase">
                  {getRoleLabel(role)}
                </p>
                <p className="text-2xl font-bold text-gray-900">{count}</p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
