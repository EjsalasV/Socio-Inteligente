/**
 * Página de Registro - SocioAI
 * Integra modal legal de aceptación de términos
 */

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import LegalAcceptanceModal from '@/components/legal/LegalAcceptanceModal'

interface FormData {
  nombre: string
  email: string
  empresa: string
  contraseña: string
  rol: 'junior' | 'semi' | 'senior' | 'manager' | 'socio'
}

export default function RegistroPage() {
  const router = useRouter()
  const [showLegal, setShowLegal] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formData, setFormData] = useState<FormData>({
    nombre: '',
    email: '',
    empresa: '',
    contraseña: '',
    rol: 'junior',
  })

  const handleLegalAccept = () => {
    setShowLegal(false)
    localStorage.setItem('legal_accepted_date', new Date().toISOString())
    localStorage.setItem('alpha_rules_accepted_version', '2026-08-09')
  }

  const handleLegalDecline = () => {
    router.push('/')
  }

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/auth/registro', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          legal_accepted: true,
          alpha_rules_accepted: true,
          alpha_rules_version: '2026-08-09',
          accepted_at: new Date().toISOString(),
        }),
      })

      if (!response.ok) {
        throw new Error('Error al crear cuenta')
      }

      const { token } = await response.json()
      localStorage.setItem('token', token)
      router.push('/dashboard')
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Error desconocido'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* Modal Legal - Debe aceptar antes de ver formulario */}
      <LegalAcceptanceModal
        isOpen={showLegal}
        onAccept={handleLegalAccept}
        onDecline={handleLegalDecline}
      />

      {/* Formulario de Registro - Solo visible después de aceptar legal */}
      {!showLegal && (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full">
            {/* Header */}
            <div className="mb-8 text-center">
              <h1 className="text-3xl font-bold text-gray-900">SocioAI</h1>
              <p className="text-gray-600 mt-2">Crea tu cuenta para auditoría inteligente</p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                {error}
              </div>
            )}

            {/* Formulario */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Nombre */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nombre Completo
                </label>
                <input
                  type="text"
                  name="nombre"
                  value={formData.nombre}
                  onChange={handleInputChange}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                  placeholder="Juan Pérez García"
                />
              </div>

              {/* Email */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email Profesional
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                  placeholder="juan@firma-auditoria.com"
                />
              </div>

              {/* Empresa */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Firma / Empresa
                </label>
                <input
                  type="text"
                  name="empresa"
                  value={formData.empresa}
                  onChange={handleInputChange}
                  required
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                  placeholder="Firma de Auditoría XYZ"
                />
              </div>

              {/* Rol */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tu Rol en Auditoría
                </label>
                <select
                  name="rol"
                  value={formData.rol}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                >
                  <option value="junior">Junior Auditor</option>
                  <option value="semi">Auditor Semi-Senior</option>
                  <option value="senior">Senior Auditor</option>
                  <option value="manager">Manager / Coordinador</option>
                  <option value="socio">Socio / Director</option>
                </select>
              </div>

              {/* Contraseña */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Contraseña
                </label>
                <input
                  type="password"
                  name="contraseña"
                  value={formData.contraseña}
                  onChange={handleInputChange}
                  required
                  minLength={8}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                  placeholder="••••••••"
                />
                <p className="text-xs text-gray-500 mt-1">Mínimo 8 caracteres</p>
              </div>

              {/* Legal Acceptance Info */}
              <div className="bg-blue-50 border border-blue-200 p-3 rounded text-xs text-blue-900">
                ✓ Has aceptado nuestros términos, política de privacidad y documento de responsabilidad
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full px-4 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition"
              >
                {loading ? 'Creando cuenta...' : 'Crear Cuenta'}
              </button>

              {/* Login Link */}
              <p className="text-center text-sm text-gray-600">
                ¿Ya tienes cuenta?{' '}
                <a href="/login" className="text-blue-600 hover:underline font-semibold">
                  Inicia sesión aquí
                </a>
              </p>
            </form>

            {/* Legal Links */}
            <div className="mt-6 pt-6 border-t border-gray-200 text-xs text-gray-500 space-y-1">
              <p>
                <a href="/legal/terminos" target="_blank" className="text-blue-600 hover:underline">
                  Términos de Servicio
                </a>
              </p>
              <p>
                <a href="/legal/privacidad" target="_blank" className="text-blue-600 hover:underline">
                  Política de Privacidad
                </a>
              </p>
              <p>
                <a href="/legal/responsabilidad" target="_blank" className="text-blue-600 hover:underline">
                  Documento de Responsabilidad
                </a>
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
