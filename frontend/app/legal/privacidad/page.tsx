/**
 * Página de Política de Privacidad
 * Ubicación: /legal/privacidad
 */

import fs from 'fs'
import path from 'path'
import { ReactMarkdown } from '@/components/ReactMarkdown'

export const metadata = {
  title: 'Política de Privacidad - SocioAI',
  description:
    'Política de privacidad de SocioAI. Cómo protegemos tus datos.',
}

export default function PrivacidadPage() {
  const filePath = path.join(
    process.cwd(),
    'legal',
    'POLITICA_PRIVACIDAD.md'
  )
  const content = fs.readFileSync(filePath, 'utf-8')

  return (
    <>
      <ReactMarkdown>{content}</ReactMarkdown>

      <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded">
        <p className="text-sm text-blue-900">
          <strong>Derechos de privacidad:</strong> Puedes ejercer tus derechos
          de acceso, rectificación, eliminación y portabilidad de datos en
          cualquier momento.
        </p>
        <p className="text-sm text-blue-800 mt-2">
          Contacta:{' '}
          <a href="mailto:privacy@socioai.ec" className="underline font-semibold">
            privacy@socioai.ec
          </a>
        </p>
      </div>
    </>
  )
}
