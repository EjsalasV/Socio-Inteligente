/**
 * Página de Documento de Responsabilidad
 * Ubicación: /legal/responsabilidad
 */

import fs from 'fs'
import path from 'path'
import { ReactMarkdown } from '@/components/ReactMarkdown'

export const metadata = {
  title: 'Documento de Responsabilidad - SocioAI',
  description:
    'Aclaración de responsabilidades legales entre SocioAI y usuarios.',
}

export default function ResponsabilidadPage() {
  const filePath = path.join(
    process.cwd(),
    'legal',
    'DOCUMENTO_RESPONSABILIDAD.md'
  )
  const content = fs.readFileSync(filePath, 'utf-8')

  return (
    <>
      <ReactMarkdown>{content}</ReactMarkdown>

      <div className="mt-8 p-4 bg-red-50 border border-red-200 rounded">
        <p className="text-sm text-red-900">
          <strong>⚠️ Importante:</strong> Este documento clarifica que SocioAI
          es una herramienta asistente. El auditor es responsable de todas las
          decisiones técnicas.
        </p>
        <p className="text-sm text-red-800 mt-2">
          Si no estás seguro de algo, por favor contacta a{' '}
          <a href="mailto:legal@socioai.ec" className="underline font-semibold">
            legal@socioai.ec
          </a>{' '}
          antes de usar la plataforma.
        </p>
      </div>
    </>
  )
}
