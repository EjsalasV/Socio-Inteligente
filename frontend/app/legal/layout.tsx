/**
 * layout.tsx para página de documentos legales
 * Ubicación: /legal/terminos, /legal/privacidad, etc.
 */

export default function LegalLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar */}
      <nav className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex justify-between items-center">
          <a href="/" className="text-2xl font-bold text-blue-600">
            SocioAI
          </a>
          <div className="text-sm text-gray-600">Documentos Legales</div>
          <a
            href="/"
            className="px-4 py-2 text-blue-600 hover:bg-blue-50 rounded transition"
          >
            ← Volver
          </a>
        </div>
      </nav>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-4 py-12">
        <article className="bg-white rounded-lg shadow-sm p-8 prose prose-sm max-w-none">
          {children}
        </article>

        {/* Quick Links */}
        <div className="mt-12 bg-blue-50 p-6 rounded-lg border border-blue-200">
          <h3 className="font-bold text-gray-900 mb-4">Otros Documentos</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <a
              href="/legal/terminos"
              className="text-blue-600 hover:underline text-sm"
            >
              → Términos de Servicio
            </a>
            <a
              href="/legal/privacidad"
              className="text-blue-600 hover:underline text-sm"
            >
              → Política de Privacidad
            </a>
            <a
              href="/legal/responsabilidad"
              className="text-blue-600 hover:underline text-sm"
            >
              → Responsabilidad Legal
            </a>
            <a
              href="/legal/seguridad"
              className="text-blue-600 hover:underline text-sm"
            >
              → Checklist Seguridad
            </a>
          </div>
        </div>

        {/* Support */}
        <div className="mt-8 bg-gray-100 p-6 rounded-lg text-center">
          <p className="text-gray-700 mb-3">
            ¿Tienes dudas sobre nuestras políticas?
          </p>
          <a
            href="mailto:legal@socioai.ec"
            className="inline-block px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            Contactar al equipo legal
          </a>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-300 py-6 mt-16">
        <div className="max-w-4xl mx-auto px-4 text-center text-xs text-slate-500">
          <p>
            © 2026 SocioAI. Documentos legales en español para Ecuador. Última
            actualización: Mayo 16, 2026
          </p>
        </div>
      </footer>
    </div>
  )
}
