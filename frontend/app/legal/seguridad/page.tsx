/**
 * Página de Checklist de Seguridad
 * Ubicación: /legal/seguridad
 */

import fs from 'fs'
import path from 'path'
import { ReactMarkdown } from '@/components/ReactMarkdown'

export const metadata = {
  title: 'Checklist de Seguridad - SocioAI',
  description:
    'Medidas de seguridad implementadas en SocioAI para proteger tus datos.',
}

export default function SeguridadPage() {
  const filePath = path.join(
    process.cwd(),
    'legal',
    'CHECKLIST_SEGURIDAD.md'
  )
  const content = fs.readFileSync(filePath, 'utf-8')

  return (
    <>
      <ReactMarkdown>{content}</ReactMarkdown>

      <div className="mt-8 p-4 bg-green-50 border border-green-200 rounded">
        <p className="text-sm text-green-900">
          <strong>Seguridad de datos:</strong> SocioAI implementa múltiples capas
          de encriptación, autenticación y auditoría.
        </p>
        <p className="text-sm text-green-800 mt-2">
          Para reportar vulnerabilidades:{' '}
          <a href="mailto:security@socioai.ec" className="underline font-semibold">
            security@socioai.ec
          </a>
        </p>
      </div>
    </>
  )
}
