/**
 * FeedbackCard - Mentor Feature
 * Muestra feedback inteligente sobre progreso de auditoría
 */

'use client'

import { useEffect, useState } from 'react'
import { useAuditContext } from '@/lib/hooks/useAuditContext'

interface FeedbackItem {
  level: 'success' | 'info' | 'warning' | 'critical'
  title: string
  message: string
  actionable?: boolean
  action?: string
}

interface FeedbackData {
  cliente_id: string
  completion: {
    pct: number
    areas_total: number
    areas_completadas: number
  }
  feedback: FeedbackItem[]
  summary: {
    blocking_count: number
    warning_count: number
    ready_for_close: boolean
  }
}

export default function FeedbackCard() {
  const { clienteId } = useAuditContext()
  const [feedback, setFeedback] = useState<FeedbackData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!clienteId) {
      setLoading(false)
      return
    }

    const fetchFeedback = async () => {
      try {
        setLoading(true)
        setError(null)

        // Esperar un poco para asegurar que el backend está listo
        await new Promise(resolve => setTimeout(resolve, 500))

        const response = await fetch(`/api/feedback/${clienteId}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        })

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        const data = await response.json()
        setFeedback(data.data || null)
      } catch (err) {
        console.error('Feedback fetch error:', err)
        setError(err instanceof Error ? err.message : 'Error desconocido')
        setFeedback(null)
      } finally {
        setLoading(false)
      }
    }

    fetchFeedback()

    // Re-fetch cada 30 segundos
    const interval = setInterval(fetchFeedback, 30000)
    return () => clearInterval(interval)
  }, [clienteId])

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="space-y-2">
          <div className="h-3 bg-gray-200 rounded w-full"></div>
          <div className="h-3 bg-gray-200 rounded w-5/6"></div>
        </div>
      </div>
    )
  }

  // Si hay error, mostrar mensaje minimalista
  if (error && !feedback) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-900">
          <strong>💬 Mentor listo:</strong> El feedback se mostrará cuando completes más datos.
        </p>
      </div>
    )
  }

  if (!feedback) {
    return null
  }

  const { completion, summary } = feedback
  const progressColor =
    completion.pct < 30 ? 'bg-blue-500' :
    completion.pct < 70 ? 'bg-yellow-500' :
    completion.pct < 100 ? 'bg-green-500' :
    'bg-green-600'

  const getLevelStyles = (level: string) => {
    switch (level) {
      case 'critical':
        return 'bg-red-50 border-l-4 border-red-500 text-red-900'
      case 'warning':
        return 'bg-yellow-50 border-l-4 border-yellow-500 text-yellow-900'
      case 'info':
        return 'bg-blue-50 border-l-4 border-blue-500 text-blue-900'
      case 'success':
        return 'bg-green-50 border-l-4 border-green-500 text-green-900'
      default:
        return 'bg-gray-50 border-l-4 border-gray-500 text-gray-900'
    }
  }

  return (
    <div className="space-y-6">
      {/* Progress Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          📊 Progreso de Auditoría
        </h3>

        {/* Completion Bar */}
        <div className="mb-4">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">
              Completitud: {completion.pct}%
            </span>
            <span className="text-xs text-gray-500">
              {completion.areas_completadas}/{completion.areas_total} áreas
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className={`h-full ${progressColor} transition-all duration-300`}
              style={{ width: `${completion.pct}%` }}
            ></div>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-gray-200">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {summary.warning_count}
            </div>
            <div className="text-xs text-gray-500">Advertencias</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">
              {summary.blocking_count}
            </div>
            <div className="text-xs text-gray-500">Críticos</div>
          </div>
          <div className="text-center">
            <div className={`text-2xl font-bold ${summary.ready_for_close ? 'text-green-600' : 'text-gray-400'}`}>
              {summary.ready_for_close ? '✓' : '○'}
            </div>
            <div className="text-xs text-gray-500">Listo para cierre</div>
          </div>
        </div>
      </div>

      {/* Feedback Items */}
      {feedback.feedback && feedback.feedback.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-gray-900">
            💡 Recomendaciones del Mentor
          </h3>
          {feedback.feedback.map((item, idx) => (
            <div
              key={idx}
              className={`rounded-lg p-4 ${getLevelStyles(item.level)}`}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h4 className="font-semibold text-sm mb-1">{item.title}</h4>
                  <p className="text-sm leading-relaxed">{item.message}</p>
                  {item.actionable && item.action && (
                    <div className="mt-2 text-xs font-medium opacity-75">
                      → {item.action}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Mentor Tip */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-200">
        <p className="text-sm text-blue-900">
          <strong>💬 Tip del Mentor:</strong> El feedback se actualiza conforme avanzas. Consulta el chat para explicaciones detalladas.
        </p>
      </div>
    </div>
  )
}
