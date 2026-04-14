export default function LandingPage() {
  return (
    <div className="min-h-screen bg-surface text-slate-900 font-body">
      <header className="sticky top-0 z-40 border-b border-[#041627]/10 bg-white/90 backdrop-blur">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-4 md:px-10">
          <div className="flex items-center gap-3">
            <div className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-[#041627] text-[#a5eff0]">
              <span className="material-symbols-outlined text-base">verified_user</span>
            </div>
            <div>
              <p className="font-headline text-2xl leading-none text-[#041627]">Socio AI</p>
              <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500">Auditoría inteligente</p>
            </div>
          </div>
          <a
            href="/"
            className="rounded-full border border-[#041627]/20 px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-[#041627] transition-colors hover:bg-[#041627] hover:text-white"
          >
            Iniciar sesión
          </a>
        </div>
      </header>

      <main>
        <section className="mx-auto w-full max-w-7xl px-6 pb-16 pt-16 md:px-10 md:pt-24">
          <div className="max-w-4xl">
            <h1 className="font-headline text-4xl leading-tight text-[#041627] md:text-6xl">
              La plataforma de auditoría inteligente para firmas independientes
            </h1>
            <p className="mt-6 max-w-3xl text-base leading-relaxed text-slate-600 md:text-xl">
              Socio AI automatiza la planificación, ejecución y papeles de trabajo de auditoría — para que tu equipo
              se enfoque en el criterio, no en el formato.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <a
                href="mailto:soporte@socioai.app?subject=Solicitud%20de%20demo%20Socio%20AI"
                aria-label="Solicitar demo de Socio AI"
                className="rounded-full bg-[#041627] px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em] text-white shadow-lg shadow-[#041627]/25 transition-opacity hover:opacity-90"
              >
                Solicitar demo
              </a>
              <a
                href="#features"
                aria-label="Ir a la sección de funcionalidades"
                className="rounded-full border border-[#041627]/20 px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em] text-[#041627] transition-colors hover:bg-[#041627] hover:text-white"
              >
                Ver cómo funciona
              </a>
            </div>
            <p className="mt-6 text-sm text-slate-500">
              Usado por firmas de auditoría en Colombia, México y Argentina · Cumple NIA, NIIF e ISAE 3000
            </p>
          </div>
        </section>

        <section className="mx-auto w-full max-w-7xl px-6 pb-16 md:px-10">
          <h2 className="font-headline text-3xl text-[#041627] md:text-4xl">
            ¿Sigues gestionando auditorías en hojas de cálculo?
          </h2>
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            <article className="rounded-editorial border border-[#041627]/10 bg-white p-6 shadow-editorial">
              <span className="material-symbols-outlined text-2xl text-[#002f30]">folder_open</span>
              <p className="mt-3 text-sm font-semibold text-[#041627]">
                Papeles de trabajo desorganizados y sin trazabilidad
              </p>
            </article>
            <article className="rounded-editorial border border-[#041627]/10 bg-white p-6 shadow-editorial">
              <span className="material-symbols-outlined text-2xl text-[#002f30]">calculate</span>
              <p className="mt-3 text-sm font-semibold text-[#041627]">
                Control de materialidad manual y propenso a errores
              </p>
            </article>
            <article className="rounded-editorial border border-[#041627]/10 bg-white p-6 shadow-editorial">
              <span className="material-symbols-outlined text-2xl text-[#002f30]">warning</span>
              <p className="mt-3 text-sm font-semibold text-[#041627]">
                Sin visibilidad del riesgo hasta el cierre del encargo
              </p>
            </article>
          </div>
        </section>

        <section id="features" className="scroll-mt-28 mx-auto w-full max-w-7xl px-6 pb-16 md:px-10">
          <h2 className="font-headline text-3xl text-[#041627] md:text-4xl">
            Todo lo que necesita una firma moderna en un solo lugar
          </h2>
          <div className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <article className="rounded-editorial border border-[#041627]/10 bg-white p-6">
              <span className="material-symbols-outlined text-2xl text-[#002f30]">radar</span>
              <h3 className="mt-3 font-headline text-2xl text-[#041627]">Motor de Riesgos</h3>
              <p className="mt-2 text-sm text-slate-600">
                Mapa de calor automático con riesgo inherente y de control por área.
              </p>
            </article>
            <article className="rounded-editorial border border-[#041627]/10 bg-white p-6">
              <span className="material-symbols-outlined text-2xl text-[#002f30]">task_alt</span>
              <h3 className="mt-3 font-headline text-2xl text-[#041627]">Papeles de Trabajo Inteligentes</h3>
              <p className="mt-2 text-sm text-slate-600">
                Quality gates, evidencias y asignación por rol — sin Excel.
              </p>
            </article>
            <article className="rounded-editorial border border-[#041627]/10 bg-white p-6">
              <span className="material-symbols-outlined text-2xl text-[#002f30]">analytics</span>
              <h3 className="mt-3 font-headline text-2xl text-[#041627]">Materialidad Automática</h3>
              <p className="mt-2 text-sm text-slate-600">
                Calcula MP, ME y umbral de trivialidad desde el balance de comprobación.
              </p>
            </article>
            <article className="rounded-editorial border border-[#041627]/10 bg-white p-6">
              <span className="material-symbols-outlined text-2xl text-[#002f30]">forum</span>
              <h3 className="mt-3 font-headline text-2xl text-[#041627]">Socio AI Chat</h3>
              <p className="mt-2 text-sm text-slate-600">
                Consulta normativa con citas de NIA, NIIF y ISAE en tiempo real.
              </p>
            </article>
            <article className="rounded-editorial border border-[#041627]/10 bg-white p-6">
              <span className="material-symbols-outlined text-2xl text-[#002f30]">groups</span>
              <h3 className="mt-3 font-headline text-2xl text-[#041627]">Gestión de Clientes</h3>
              <p className="mt-2 text-sm text-slate-600">
                Portafolio multi-cliente con roles jerárquicos: socio, manager, senior, junior.
              </p>
            </article>
            <article className="rounded-editorial border border-[#041627]/10 bg-white p-6">
              <span className="material-symbols-outlined text-2xl text-[#002f30]">folder_shared</span>
              <h3 className="mt-3 font-headline text-2xl text-[#041627]">Memoria del Cliente</h3>
              <p className="mt-2 text-sm text-slate-600">
                Expediente maestro permanente con historial de hallazgos y documentos.
              </p>
            </article>
          </div>
        </section>

        <section className="bg-[#041627] py-16 text-white">
          <div className="mx-auto w-full max-w-7xl px-6 md:px-10">
            <h2 className="font-headline text-3xl md:text-4xl">Resultados que justifican el cambio</h2>
            <div className="mt-8 grid gap-4 md:grid-cols-3">
              <article className="rounded-editorial border border-white/15 bg-white/5 p-6">
                <p className="font-headline text-5xl text-[#a5eff0]">60%</p>
                <p className="mt-2 text-sm uppercase tracking-[0.12em] text-slate-200">menos tiempo en planificación</p>
              </article>
              <article className="rounded-editorial border border-white/15 bg-white/5 p-6">
                <p className="font-headline text-5xl text-[#a5eff0]">8 hrs</p>
                <p className="mt-2 text-sm uppercase tracking-[0.12em] text-slate-200">
                  ahorradas por encargo en papeles de trabajo
                </p>
              </article>
              <article className="rounded-editorial border border-white/15 bg-white/5 p-6">
                <p className="font-headline text-5xl text-[#a5eff0]">100%</p>
                <p className="mt-2 text-sm uppercase tracking-[0.12em] text-slate-200">
                  trazabilidad desde riesgo hasta evidencia
                </p>
              </article>
            </div>
          </div>
        </section>

        <section className="mx-auto w-full max-w-7xl px-6 pb-16 pt-16 md:px-10">
          <h2 className="font-headline text-3xl text-[#041627] md:text-4xl">
            Planes pensados para firmas independientes
          </h2>
          <div className="mt-8 grid gap-4 lg:grid-cols-3">
            <article className="rounded-editorial border border-[#041627]/10 bg-white p-6">
              <p className="text-[11px] uppercase tracking-[0.12em] text-slate-500">Starter</p>
              <p className="mt-3 font-headline text-3xl text-[#041627]">Consultar precio</p>
              <p className="mt-3 text-sm text-slate-600">Hasta 5 clientes activos · 3 usuarios · Módulos base</p>
              <a
                href="mailto:soporte@socioai.app?subject=Starter%20Socio%20AI"
                className="mt-6 inline-flex rounded-full border border-[#041627]/20 px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-[#041627]"
              >
                Empezar gratis
              </a>
            </article>
            <article className="rounded-editorial border-2 border-[#89d3d4] bg-white p-6 shadow-editorial">
              <p className="inline-flex rounded-full bg-[#a5eff0] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.12em] text-[#002f30]">
                Más popular
              </p>
              <p className="mt-2 text-[11px] uppercase tracking-[0.12em] text-slate-500">Pro</p>
              <p className="mt-3 font-headline text-3xl text-[#041627]">Desde $X/mes</p>
              <p className="mt-3 text-sm text-slate-600">
                Clientes ilimitados · 10 usuarios · Todos los módulos + Socio AI Chat
              </p>
              <a
                href="mailto:soporte@socioai.app?subject=Demo%20Plan%20Pro%20Socio%20AI"
                className="mt-6 inline-flex rounded-full bg-[#041627] px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-white"
              >
                Solicitar demo
              </a>
            </article>
            <article className="rounded-editorial border border-[#041627]/10 bg-white p-6">
              <p className="text-[11px] uppercase tracking-[0.12em] text-slate-500">Enterprise</p>
              <p className="mt-3 font-headline text-3xl text-[#041627]">Consultar precio</p>
              <p className="mt-3 text-sm text-slate-600">Usuarios ilimitados · Multi-firma · SSO + API</p>
              <a
                href="mailto:soporte@socioai.app?subject=Enterprise%20Socio%20AI"
                className="mt-6 inline-flex rounded-full border border-[#041627]/20 px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em] text-[#041627]"
              >
                Contactar ventas
              </a>
            </article>
          </div>
        </section>

        <section id="contacto" className="scroll-mt-28 mx-auto w-full max-w-7xl px-6 pb-16 md:px-10">
          <div className="rounded-editorial border border-[#041627]/10 bg-white p-8 md:p-12">
            <h2 className="font-headline text-3xl text-[#041627] md:text-4xl">¿Listo para modernizar tu firma?</h2>
            <p className="mt-3 max-w-3xl text-sm text-slate-600 md:text-base">
              Solicita una demo personalizada y te mostramos el sistema con tus propios clientes en menos de 30
              minutos.
            </p>
            <a
              href="mailto:soporte@socioai.app?subject=Agendar%20demo%20Socio%20AI"
              className="mt-6 inline-flex rounded-full bg-[#041627] px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em] text-white"
            >
              Agendar demo ahora
            </a>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200/80 bg-slate-50 py-8">
        <div className="mx-auto flex w-full max-w-7xl flex-col items-center justify-between gap-4 px-6 md:flex-row md:px-10">
          <p className="text-[11px] uppercase tracking-[0.12em] text-slate-400">
            © 2026 Socio AI · Todos los derechos reservados
          </p>
          <div className="flex flex-wrap items-center justify-center gap-6">
            <a className="text-[11px] uppercase tracking-[0.12em] text-slate-500 hover:text-[#002f30]" href="https://socioai.app/privacy" target="_blank" rel="noreferrer">
              Política de privacidad
            </a>
            <a className="text-[11px] uppercase tracking-[0.12em] text-slate-500 hover:text-[#002f30]" href="https://socioai.app/security" target="_blank" rel="noreferrer">
              Arquitectura de seguridad
            </a>
            <a className="text-[11px] uppercase tracking-[0.12em] text-slate-500 hover:text-[#002f30]" href="https://socioai.app/compliance" target="_blank" rel="noreferrer">
              Cumplimiento normativo
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
