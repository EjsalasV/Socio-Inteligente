/**
 * LegalFooter.tsx
 * Footer con enlaces a documentos legales
 * Coloca esto al final de cada página
 */

'use client'

import Link from 'next/link'

export default function LegalFooter() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="bg-slate-900 text-slate-300 mt-16 py-12">
      <div className="max-w-7xl mx-auto px-4">
        {/* Main Footer Content */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* About */}
          <div>
            <h3 className="text-white font-bold text-lg mb-4">SocioAI</h3>
            <p className="text-sm text-slate-400">
              Plataforma de auditoría inteligente impulsada por IA. Diseñada para
              profesionales de auditoría en Latinoamérica.
            </p>
            <p className="text-xs text-slate-500 mt-2">
              v1.0 © {currentYear} Joao Salas
            </p>
          </div>

          {/* Product */}
          <div>
            <h4 className="text-white font-semibold mb-4">Producto</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/features" className="hover:text-white transition">
                  Características
                </Link>
              </li>
              <li>
                <Link href="/pricing" className="hover:text-white transition">
                  Pricing
                </Link>
              </li>
              <li>
                <Link href="/docs" className="hover:text-white transition">
                  Documentación
                </Link>
              </li>
              <li>
                <Link href="/api" className="hover:text-white transition">
                  API
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h4 className="text-white font-semibold mb-4">Legal</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link
                  href="/legal/terminos"
                  className="hover:text-white transition"
                >
                  Términos de Servicio
                </Link>
              </li>
              <li>
                <Link
                  href="/legal/privacidad"
                  className="hover:text-white transition"
                >
                  Política de Privacidad
                </Link>
              </li>
              <li>
                <Link
                  href="/legal/responsabilidad"
                  className="hover:text-white transition"
                >
                  Responsabilidad Legal
                </Link>
              </li>
              <li>
                <Link
                  href="/legal/seguridad"
                  className="hover:text-white transition"
                >
                  Checklist Seguridad
                </Link>
              </li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="text-white font-semibold mb-4">Contacto</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a
                  href="mailto:legal@socioai.ec"
                  className="hover:text-white transition"
                >
                  legal@socioai.ec
                </a>
              </li>
              <li>
                <a
                  href="mailto:security@socioai.ec"
                  className="hover:text-white transition"
                >
                  security@socioai.ec
                </a>
              </li>
              <li>
                <a
                  href="mailto:support@socioai.ec"
                  className="hover:text-white transition"
                >
                  support@socioai.ec
                </a>
              </li>
              <li className="pt-2 text-xs">
                Quito, Ecuador
              </li>
            </ul>
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-slate-700 py-6">
          {/* Bottom Links */}
          <div className="flex flex-col md:flex-row justify-between items-center gap-4 mb-4">
            <p className="text-xs text-slate-500">
              SocioAI - Auditoría Inteligente para Latinoamérica
            </p>
            <div className="flex space-x-4 text-xs text-slate-500">
              <a href="#" className="hover:text-slate-300 transition">
                Status
              </a>
              <a href="#" className="hover:text-slate-300 transition">
                Blog
              </a>
              <a href="#" className="hover:text-slate-300 transition">
                Twitter
              </a>
              <a href="#" className="hover:text-slate-300 transition">
                LinkedIn
              </a>
            </div>
          </div>

          {/* Legal Notice */}
          <p className="text-xs text-slate-600 text-center">
            Al usar SocioAI, aceptas nuestros{' '}
            <Link href="/legal/terminos" className="hover:text-slate-500">
              Términos de Servicio
            </Link>
            {' '} y{' '}
            <Link href="/legal/privacidad" className="hover:text-slate-500">
              Política de Privacidad
            </Link>
            . SocioAI es una herramienta asistente. El auditor es responsable
            de todas las decisiones técnicas. Última actualización: Mayo 2026.
          </p>
        </div>
      </div>
    </footer>
  )
}
