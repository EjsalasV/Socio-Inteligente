/**
 * LegalAcceptanceModal.tsx
 * Modal que aparece al crear cuenta - usuario debe aceptar términos
 */

'use client'

import { useState } from 'react'
import Link from 'next/link'

interface LegalAcceptanceModalProps {
  isOpen: boolean
  onAccept: () => void
  onDecline: () => void
}

export default function LegalAcceptanceModal({
  isOpen,
  onAccept,
  onDecline,
}: LegalAcceptanceModalProps) {
  const [checked, setChecked] = useState({
    terms: false,
    privacy: false,
    responsibility: false,
    alphaData: false,
  })

  const allChecked = Object.values(checked).every(Boolean)

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-96 overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-blue-600 text-white p-6 border-b">
          <h2 className="text-xl font-bold">Términos y Políticas - SocioAI</h2>
          <p className="text-sm text-blue-100 mt-1">
            Antes de continuar, debes aceptar nuestros documentos legales
          </p>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Términos */}
          <div className="flex items-start space-x-4">
            <input
              type="checkbox"
              id="terms"
              checked={checked.terms}
              onChange={(e) =>
                setChecked({ ...checked, terms: e.target.checked })
              }
              className="mt-1 w-5 h-5 accent-blue-600"
            />
            <div className="flex-1">
              <label
                htmlFor="terms"
                className="font-semibold text-gray-900 cursor-pointer"
              >
                He leído y acepto los Términos de Servicio
              </label>
              <p className="text-sm text-gray-600 mt-1">
                SocioAI es una herramienta asistente. Yo (el auditor) soy
                responsable de validar todas las recomendaciones.
              </p>
              <Link
                href="/legal/terminos"
                target="_blank"
                className="text-blue-600 hover:underline text-sm mt-2 inline-block"
              >
                Leer términos completos →
              </Link>
            </div>
          </div>

          {/* Privacidad */}
          <div className="flex items-start space-x-4">
            <input
              type="checkbox"
              id="privacy"
              checked={checked.privacy}
              onChange={(e) =>
                setChecked({ ...checked, privacy: e.target.checked })
              }
              className="mt-1 w-5 h-5 accent-blue-600"
            />
            <div className="flex-1">
              <label
                htmlFor="privacy"
                className="font-semibold text-gray-900 cursor-pointer"
              >
                Acepto la Política de Privacidad
              </label>
              <p className="text-sm text-gray-600 mt-1">
                Entiendo cómo se recopilan, usan y protegen mis datos. Puedo
                ejercer mis derechos de privacidad en cualquier momento.
              </p>
              <Link
                href="/legal/privacidad"
                target="_blank"
                className="text-blue-600 hover:underline text-sm mt-2 inline-block"
              >
                Leer política completa →
              </Link>
            </div>
          </div>

          {/* Responsabilidad */}
          <div className="flex items-start space-x-4">
            <input
              type="checkbox"
              id="responsibility"
              checked={checked.responsibility}
              onChange={(e) =>
                setChecked({ ...checked, responsibility: e.target.checked })
              }
              className="mt-1 w-5 h-5 accent-blue-600"
            />
            <div className="flex-1">
              <label
                htmlFor="responsibility"
                className="font-semibold text-gray-900 cursor-pointer"
              >
                Entiendo los Límites de Responsabilidad
              </label>
              <p className="text-sm text-gray-600 mt-1">
                Reconozco que SocioAI tiene límites legales de responsabilidad.
                Yo asumo la responsabilidad profesional por mis decisiones
                técnicas.
              </p>
              <Link
                href="/legal/responsabilidad"
                target="_blank"
                className="text-blue-600 hover:underline text-sm mt-2 inline-block"
              >
                Leer documento de responsabilidad →
              </Link>
            </div>
          </div>

          <div className="flex items-start space-x-4">
            <input
              type="checkbox"
              id="alphaData"
              checked={checked.alphaData}
              onChange={(e) => setChecked({ ...checked, alphaData: e.target.checked })}
              className="mt-1 h-5 w-5 accent-amber-600"
            />
            <div className="flex-1">
              <label htmlFor="alphaData" className="cursor-pointer font-semibold text-gray-900">
                Entiendo las reglas de la Alpha cerrada
              </label>
              <p className="mt-1 text-sm text-gray-600">
                Usaré datos ficticios o anonimizados. SocioAI no reutiliza expedientes ni auditorías cerradas para entrenar modelos o mejorar criterio compartido.
              </p>
            </div>
          </div>

          {/* Warning Box */}
          <div className="bg-red-50 border-l-4 border-red-600 p-4 mt-6">
            <p className="text-red-900 font-semibold">⚠️ Importante</p>
            <p className="text-red-800 text-sm mt-1">
              SocioAI es una herramienta asistente en auditoría. No reemplaza
              tu juicio profesional ni tu responsabilidad legal como auditor. Si
              algo no es claro, por favor contacta a:{' '}
              <a href="mailto:legal@socioai.ec" className="font-semibold">
                legal@socioai.ec
              </a>
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-gray-100 p-6 flex space-x-4 border-t">
          <button
            onClick={onDecline}
            className="flex-1 px-4 py-3 bg-gray-300 text-gray-900 font-semibold rounded hover:bg-gray-400 transition"
          >
            Rechazar
          </button>
          <button
            onClick={onAccept}
            disabled={!allChecked}
            className={`flex-1 px-4 py-3 rounded font-semibold transition ${
              allChecked
                ? 'bg-blue-600 text-white hover:bg-blue-700 cursor-pointer'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            {allChecked ? '✓ Acepto todos los términos' : 'Acepta todo para continuar'}
          </button>
        </div>
      </div>
    </div>
  )
}
