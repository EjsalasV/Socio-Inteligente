/**
 * página de Términos de Servicio
 * Ubicación: /legal/terminos
 * Renderiza el archivo markdown de términos
 */

import fs from 'fs'
import path from 'path'
import { ReactMarkdown } from '@/components/ReactMarkdown'

export const metadata = {
  title: 'Términos de Servicio - SocioAI',
  description:
    'Términos y condiciones de uso de SocioAI. Plataforma de auditoría inteligente.',
}

export default function TerminosPage() {
  // Leer el archivo markdown de términos
  const filePath = path.join(
    process.cwd(),
    '..',
    'legal',
    'TERMINOS_SERVICIO.md'
  )
  const content = fs.readFileSync(filePath, 'utf-8')

  return (
    <>
      <ReactMarkdown>{content}</ReactMarkdown>

      <div className="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded">
        <p className="text-sm text-yellow-900">
          <strong>Última actualización:</strong> 16 de mayo de 2026
        </p>
        <p className="text-sm text-yellow-800 mt-2">
          Este documento es vinculante y debe ser aceptado al crear tu cuenta
          en SocioAI. Si tienes dudas, contacta a{' '}
          <a href="mailto:legal@socioai.ec" className="underline font-semibold">
            legal@socioai.ec
          </a>
        </p>
      </div>
    </>
  )
}
