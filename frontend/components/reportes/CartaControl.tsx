'use client';

import React, { useState, useEffect } from 'react';

interface Hallazgo {
  codigo_papel: string;
  nombre: string;
  motivo: string;
  aseveracion: string;
  observacion_final: string;
  efecto_financiero: string;
  impacto: string;
  accion_recomendada: string;
  revisado_por_socio: string;
  fecha_finalizacion: string;
}

interface CartaControlData {
  cliente_id: string;
  tipo_reporte: string;
  total_hallazgos: number;
  hallazgos: Hallazgo[];
  resumen: {
    sin_efecto: number;
    con_efecto: number;
    ajuste_requerido: number;
    total: number;
  };
}

interface HallazgoPorLS {
  total: number;
  sin_efecto: number;
  con_efecto: number;
  hallazgos: Array<{
    codigo: string;
    nombre: string;
    observacion: string;
    efecto: string;
  }>;
}

interface ResumenEjecutivoData {
  cliente_id: string;
  tipo_reporte: string;
  estadisticas: {
    total_papeles_auditados: number;
    total_hallazgos: number;
    hallazgos_sin_efecto: number;
    hallazgos_con_efecto: number;
    ajustes_requeridos: number;
    porcentaje_hallazgos: number;
  };
  hallazgos_significativos: Array<{
    codigo: string;
    nombre: string;
    impacto: string;
    accion: string;
  }>;
  conclusiones: string[];
}

interface CartaControlProps {
  clienteId: string;
  clienteNombre?: string;
}

function getEfectoColor(efecto: string): string {
  switch (efecto) {
    case 'SIN_EFECTO':
      return 'bg-green-100 text-green-800 border-green-300';
    case 'CON_EFECTO':
      return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    case 'AJUSTE_REQUERIDO':
      return 'bg-red-100 text-red-800 border-red-300';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-300';
  }
}

function getEfectoLabel(efecto: string): string {
  switch (efecto) {
    case 'SIN_EFECTO':
      return 'Sin Efecto';
    case 'CON_EFECTO':
      return 'Con Efecto';
    case 'AJUSTE_REQUERIDO':
      return 'Ajuste Requerido';
    default:
      return efecto;
  }
}

export function CartaControl({ clienteId, clienteNombre = 'Cliente' }: CartaControlProps) {
  const [cartaControl, setCartaControl] = useState<CartaControlData | null>(null);
  const [hallazgosPorLS, setHallazgosPorLS] = useState<Record<string, HallazgoPorLS> | null>(null);
  const [resumenEjecutivo, setResumenEjecutivo] = useState<ResumenEjecutivoData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('resumen');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const [cartaRes, lsRes, resumenRes] = await Promise.all([
          fetch(`/api/reportes/papeles-trabajo/${clienteId}/carta-control`),
          fetch(`/api/reportes/papeles-trabajo/${clienteId}/hallazgos-por-ls`),
          fetch(`/api/reportes/papeles-trabajo/${clienteId}/resumen-ejecutivo`),
        ]);

        if (!cartaRes.ok) throw new Error('Error fetching carta de control');
        if (!lsRes.ok) throw new Error('Error fetching hallazgos por LS');
        if (!resumenRes.ok) throw new Error('Error fetching resumen ejecutivo');

        const cartaData = await cartaRes.json();
        const lsData = await lsRes.json();
        const resumenData = await resumenRes.json();

        setCartaControl(cartaData.data);
        setHallazgosPorLS(lsData.data.hallazgos_por_ls);
        setResumenEjecutivo(resumenData.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error desconocido');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [clienteId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="mb-4">Cargando reporte...</div>
          <div className="text-sm text-gray-500">Por favor espera mientras se genera la carta de control</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="border border-red-300 bg-red-50 text-red-800 p-4 rounded mb-4">
        <div className="font-semibold">Error: {error}</div>
      </div>
    );
  }

  if (!cartaControl || !resumenEjecutivo) {
    return (
      <div className="border border-blue-300 bg-blue-50 text-blue-800 p-4 rounded">
        <div>No hay hallazgos registrados para este cliente.</div>
      </div>
    );
  }

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="border-b pb-4">
        <h1 className="text-3xl font-bold">CARTA DE CONTROL</h1>
        <p className="text-gray-600 mt-1">Reporte de Papeles de Trabajo Auditados</p>
        <div className="flex gap-4 mt-4 text-sm">
          <div>
            <span className="text-gray-600">Cliente: </span>
            <span className="font-semibold">{clienteNombre}</span>
          </div>
          <div>
            <span className="text-gray-600">Fecha: </span>
            <span className="font-semibold">{new Date().toLocaleDateString('es-ES')}</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="w-full">
        <div className="flex border-b gap-0">
          <button
            onClick={() => setActiveTab('resumen')}
            className={`px-4 py-2 font-medium text-sm ${
              activeTab === 'resumen'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Resumen Ejecutivo
          </button>
          <button
            onClick={() => setActiveTab('hallazgos')}
            className={`px-4 py-2 font-medium text-sm ${
              activeTab === 'hallazgos'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Hallazgos Detallados
          </button>
          <button
            onClick={() => setActiveTab('por-ls')}
            className={`px-4 py-2 font-medium text-sm ${
              activeTab === 'por-ls'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            Por Línea de Cuenta
          </button>
        </div>

        {/* TAB 1: Resumen Ejecutivo */}
        {activeTab === 'resumen' && (
          <div className="space-y-4 mt-4">
            {/* Estadísticas */}
            <div className="border rounded-lg p-6 bg-white">
              <h2 className="text-xl font-bold mb-4">Estadísticas Generales</h2>
              <div className="grid grid-cols-5 gap-4">
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">
                    {resumenEjecutivo.estadisticas.total_papeles_auditados}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">Papeles Auditados</p>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-purple-600">
                    {resumenEjecutivo.estadisticas.total_hallazgos}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">Hallazgos</p>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">
                    {resumenEjecutivo.estadisticas.hallazgos_sin_efecto}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">Sin Efecto</p>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-yellow-600">
                    {resumenEjecutivo.estadisticas.hallazgos_con_efecto}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">Con Efecto</p>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-red-600">
                    {resumenEjecutivo.estadisticas.ajustes_requeridos}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">Ajustes Requeridos</p>
                </div>
              </div>
              <div className="mt-4 text-center pt-4 border-t">
                <p className="text-2xl font-bold">
                  {resumenEjecutivo.estadisticas.porcentaje_hallazgos}%
                </p>
                <p className="text-sm text-gray-600">Porcentaje de Hallazgos</p>
              </div>
            </div>

            {/* Hallazgos Significativos */}
            {resumenEjecutivo.hallazgos_significativos.length > 0 && (
              <div className="border rounded-lg p-6 bg-white">
                <h2 className="text-xl font-bold mb-4">Hallazgos Significativos</h2>
                <p className="text-sm text-gray-600 mb-4">Hallazgos que requieren ajuste en estados financieros</p>
                <div className="space-y-3">
                  {resumenEjecutivo.hallazgos_significativos.map((h) => (
                    <div key={h.codigo} className="border-l-4 border-red-500 pl-4 py-2">
                      <p className="font-semibold">{h.nombre}</p>
                      <p className="text-xs text-gray-500">Código: {h.codigo}</p>
                      <p className="text-sm mt-1">
                        <span className="font-medium">Impacto:</span> {h.impacto}
                      </p>
                      <p className="text-sm">
                        <span className="font-medium">Acción:</span> {h.accion}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Conclusiones */}
            <div className="border rounded-lg p-6 bg-white">
              <h2 className="text-xl font-bold mb-4">Conclusiones</h2>
              <ul className="space-y-2">
                {resumenEjecutivo.conclusiones.map((c, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-green-600 text-lg">✓</span>
                    <span>{c}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* TAB 2: Hallazgos Detallados */}
        {activeTab === 'hallazgos' && (
          <div className="space-y-4 mt-4">
            {cartaControl.hallazgos.length === 0 ? (
              <div className="border border-blue-300 bg-blue-50 text-blue-800 p-4 rounded">
                No hay hallazgos registrados.
              </div>
            ) : (
              cartaControl.hallazgos.map((hallazgo) => (
                <div key={hallazgo.codigo_papel} className="border rounded-lg p-6 bg-white">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-bold">{hallazgo.nombre}</h3>
                      <p className="text-sm text-gray-600">Código: {hallazgo.codigo_papel}</p>
                    </div>
                    <span className={`px-3 py-1 rounded border text-sm font-medium ${getEfectoColor(hallazgo.efecto_financiero)}`}>
                      {getEfectoLabel(hallazgo.efecto_financiero)}
                    </span>
                  </div>

                  <div className="space-y-4">
                    {/* Motivo */}
                    <div>
                      <p className="text-sm font-semibold text-gray-600 mb-1">Por Qué Auditar (Motivo)</p>
                      <p className="text-sm">{hallazgo.motivo}</p>
                    </div>

                    {/* Aseveración */}
                    <div className="flex gap-4">
                      <div>
                        <p className="text-sm font-semibold text-gray-600">Aseveración</p>
                        <span className="inline-block px-2 py-1 bg-gray-200 text-gray-800 text-xs rounded">
                          {hallazgo.aseveracion}
                        </span>
                      </div>
                    </div>

                    {/* Observación Final */}
                    <div>
                      <p className="text-sm font-semibold text-gray-600 mb-1">Observación Final</p>
                      <p className="text-sm bg-gray-50 p-3 rounded">{hallazgo.observacion_final}</p>
                    </div>

                    {/* Impacto */}
                    {hallazgo.impacto && (
                      <div>
                        <p className="text-sm font-semibold text-gray-600 mb-1">Impacto en Estados Financieros</p>
                        <p className="text-sm bg-blue-50 p-3 rounded">{hallazgo.impacto}</p>
                      </div>
                    )}

                    {/* Acción Recomendada */}
                    {hallazgo.accion_recomendada && (
                      <div>
                        <p className="text-sm font-semibold text-gray-600 mb-1">Acción Recomendada</p>
                        <p className="text-sm bg-green-50 p-3 rounded">{hallazgo.accion_recomendada}</p>
                      </div>
                    )}

                    {/* Footer */}
                    <div className="text-xs text-gray-500 pt-2 border-t">
                      <p>Revisado por: {hallazgo.revisado_por_socio} · {new Date(hallazgo.fecha_finalizacion).toLocaleDateString('es-ES')}</p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* TAB 3: Por Línea de Cuenta */}
        {activeTab === 'por-ls' && (
          <div className="space-y-4 mt-4">
            {hallazgosPorLS && Object.keys(hallazgosPorLS).length > 0 ? (
              Object.entries(hallazgosPorLS).map(([ls, data]) => (
                <div key={ls} className="border rounded-lg p-6 bg-white">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-bold">L/S {ls}</h3>
                    <div className="flex gap-2">
                      <span className="px-2 py-1 bg-gray-200 text-gray-800 text-xs rounded">
                        Total: {data.total}
                      </span>
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded border border-green-300">
                        Sin efecto: {data.sin_efecto}
                      </span>
                      <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded border border-red-300">
                        Con efecto: {data.con_efecto}
                      </span>
                    </div>
                  </div>
                  <div className="space-y-3">
                    {data.hallazgos.map((h, idx) => (
                      <div key={idx} className="flex justify-between items-start p-3 bg-gray-50 rounded">
                        <div className="flex-1">
                          <p className="font-semibold text-sm">{h.nombre}</p>
                          <p className="text-xs text-gray-500">Código: {h.codigo}</p>
                          <p className="text-sm mt-1">{h.observacion}</p>
                        </div>
                        <span className={`px-2 py-1 rounded text-xs font-medium whitespace-nowrap ml-2 border ${getEfectoColor(h.efecto)}`}>
                          {getEfectoLabel(h.efecto)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            ) : (
              <div className="border border-blue-300 bg-blue-50 text-blue-800 p-4 rounded">
                No hay hallazgos agrupados por línea de cuenta.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
