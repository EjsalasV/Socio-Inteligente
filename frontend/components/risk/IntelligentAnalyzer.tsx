/**
 * Intelligent Audit Analyzer - Integrado en Risk Engine
 * Detecta anomalías automáticamente en datos financieros del cliente
 */

'use client'

import { useState, useEffect } from 'react'
import { authFetchJson } from '../../lib/api'
import type { ApiEnvelope } from '../../lib/contracts'

interface Hallazgo {
  id: string
  descripcion: string
  nivel: 'CRÍTICO' | 'IMPORTANTE' | 'MENOR'
  norma: string
  riesgo: string
  auditoria: string[]
  evidencia_buscar: string[]
  cuenta_afectada: string
  monto_impactado: number | string
}

interface AnalysisResult {
  cliente_id: string
  hallazgos: Hallazgo[]
  resumen: string
  observaciones_sector: string
  error?: string
}

interface TrialBalanceDataResponse {
  data?: {
    datos?: Record<string, number>
  }
}

interface ClientSummaryResponse {
  data?: {
    sector?: string
    tamano?: string
    normativa?: string
  }
}

export default function IntelligentAnalyzer({ clienteId }: { clienteId: string }) {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [selectedHallazgo, setSelectedHallazgo] = useState<Hallazgo | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Auto-cargar análisis cuando se monta el componente
  useEffect(() => {
    if (clienteId) {
      loadAnalysis()
    }
  }, [clienteId])

  const loadAnalysis = async () => {
    try {
      setLoading(true)
      setError(null)

      console.log('Cargando balance para cliente:', clienteId)

      // Obtener trial balance del cliente desde el sistema
      let balanceData: TrialBalanceDataResponse = { data: { datos: {} } }
      try {
        const balanceResponse = await fetch(`/api/trial-balance/${clienteId}/data-simple`)
        console.log('Balance response status:', balanceResponse.status)
        if (balanceResponse.ok) {
          balanceData = await balanceResponse.json()
          console.log('Balance cargado:', balanceData)
        } else {
          console.warn('Balance response not ok, usando datos vacíos')
          balanceData = { data: { datos: {} } }
        }
      } catch (e) {
        console.error('Error cargando balance:', e)
        balanceData = { data: { datos: {} } }
      }

      // Obtener información del cliente para sector y tamaño
      let clientData: ClientSummaryResponse = {}
      try {
        const clientResponse = await fetch(`/api/clientes/${clienteId}`)
        if (clientResponse.ok) {
          clientData = (await clientResponse.json()) as ClientSummaryResponse
        }
      } catch (e) {
        console.error('Error cargando cliente:', e)
      }

      console.log('Enviando análisis...')

      // Llamar al analizador con datos del sistema
      const analysisData = await authFetchJson<ApiEnvelope<AnalysisResult>>(`/api/audit-analysis/${clienteId}/analyze`, {
        method: 'POST',
        body: JSON.stringify({
          sector: clientData.data?.sector || 'Comercio',
          tamaño: clientData.data?.tamano || 'Mediana',
          marco_referencial: clientData.data?.normativa || 'NIIF Completas',
          balance_trial: balanceData?.data?.datos || {},
          income_statement: {},
        }),
      })

      console.log('Análisis completado:', analysisData)
      setResult(analysisData.data)
    } catch (err) {
      console.error('Error en loadAnalysis:', err)
      setError(err instanceof Error ? err.message : 'Error desconocido')
    } finally {
      setLoading(false)
    }
  }

  const getLevelColor = (nivel: string) => {
    switch (nivel) {
      case 'CRÍTICO': return 'bg-red-50 border-red-200'
      case 'IMPORTANTE': return 'bg-yellow-50 border-yellow-200'
      case 'MENOR': return 'bg-blue-50 border-blue-200'
      default: return 'bg-gray-50'
    }
  }

  const getLevelBadgeColor = (nivel: string) => {
    switch (nivel) {
      case 'CRÍTICO': return 'bg-red-500'
      case 'IMPORTANTE': return 'bg-yellow-500'
      case 'MENOR': return 'bg-blue-500'
      default: return 'bg-gray-500'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            🔍 Analizador Inteligente
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Detección automática de anomalías con IA
          </p>
        </div>
        <button
          onClick={loadAnalysis}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-semibold transition"
        >
          {loading ? '⏳ Analizando...' : '🔄 Re-analizar'}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-900">❌ {error}</p>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
          <div className="inline-block animate-spin">⏳</div>
          <p className="text-blue-900 mt-2">Analizando datos financieros con IA...</p>
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <>
          {/* Resumen */}
          {result.resumen && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">📊 Resumen</h3>
              <p className="text-gray-700">{result.resumen}</p>
              {result.observaciones_sector && (
                <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded">
                  <p className="text-sm text-blue-900">
                    <strong>Observación del sector:</strong> {result.observaciones_sector}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Hallazgos */}
          {result.hallazgos && result.hallazgos.length > 0 ? (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                🎯 Hallazgos Detectados ({result.hallazgos.length})
              </h3>

              <div className="space-y-3">
                {result.hallazgos.map((hallazgo, idx) => (
                  <button
                    key={idx}
                    onClick={() => setSelectedHallazgo(hallazgo)}
                    className={`w-full text-left p-4 border-2 rounded-lg hover:shadow-md transition cursor-pointer ${getLevelColor(
                      hallazgo.nivel
                    )}`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className={`${getLevelBadgeColor(hallazgo.nivel)} text-white px-3 py-1 rounded text-xs font-bold`}>
                            {hallazgo.nivel}
                          </span>
                          <span className="text-sm font-semibold text-gray-700">{hallazgo.norma}</span>
                        </div>
                        <p className="font-semibold text-gray-900">{hallazgo.descripcion}</p>
                        <p className="text-sm mt-2 opacity-75">
                          Cuenta: {hallazgo.cuenta_afectada}
                          {hallazgo.monto_impactado && ` | Monto: ${hallazgo.monto_impactado}`}
                        </p>
                      </div>
                      <span className="text-2xl">→</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <p className="text-green-900">
                ✅ No se detectaron anomalías significativas en los datos
              </p>
            </div>
          )}

          {/* Detalle Hallazgo */}
          {selectedHallazgo && (
            <div className="bg-white rounded-lg shadow p-6">
              <button
                onClick={() => setSelectedHallazgo(null)}
                className="mb-4 text-blue-600 hover:text-blue-800 text-sm font-semibold"
              >
                ← Volver a lista
              </button>

              <h3 className="text-xl font-bold text-gray-900 mb-4">{selectedHallazgo.descripcion}</h3>

              <div className="grid grid-cols-2 gap-6 mb-6">
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Riesgo de Auditoría</h4>
                  <p className="text-gray-700">{selectedHallazgo.riesgo}</p>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Norma Aplicable</h4>
                  <p className="text-gray-700">{selectedHallazgo.norma}</p>
                </div>
              </div>

              <div className="mb-6">
                <h4 className="font-semibold text-gray-900 mb-3">Procedimientos de Auditoría</h4>
                <ol className="list-decimal list-inside space-y-2 text-gray-700">
                  {selectedHallazgo.auditoria.map((proc, idx) => (
                    <li key={idx} className="ml-4">{proc}</li>
                  ))}
                </ol>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900 mb-3">Evidencia a Buscar</h4>
                <ul className="space-y-2">
                  {selectedHallazgo.evidencia_buscar.map((ev, idx) => (
                    <li key={idx} className="text-gray-700 flex items-start">
                      <span className="mr-2">▪</span> {ev}
                    </li>
                  ))}
                </ul>
              </div>

              <button
                onClick={() => alert('Hallazgo guardado (próxima funcionalidad)')}
                className="mt-6 w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-2 rounded-lg transition"
              >
                ✓ Guardar como Hallazgo de Auditoría
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
