const featureCards = [
  {
    icon: "insights",
    title: "Juicio aumentado",
    body: "Organiza la información relevante para construir mejores conclusiones, sin perder criterio.",
    label: "Capítulo 01",
  },
  {
    icon: "route",
    title: "Trazabilidad completa",
    body: "Cada hallazgo y evidencia queda conectado a su fundamento para revisión y respaldo.",
    label: "Capítulo 02",
  },
  {
    icon: "verified_user",
    title: "Confianza defendible",
    body: "Documentación sólida, transparente y lista para cualquier revisión interna o externa.",
    label: "Capítulo 03",
  },
];

const trustMarks = [
  { name: "NIA", copy: "Normas Internacionales de Auditoría", icon: "shield" },
  { name: "NIIF", copy: "Normas Internacionales de Información Financiera", icon: "book_4" },
  { name: "Trazabilidad", copy: "Evidencia con línea de auditoría completa", icon: "fingerprint" },
  { name: "Evidencias", copy: "Respaldo verificable, ordenado y seguro", icon: "assignment" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen overflow-hidden text-slate-900">
      <header className="sticky top-0 z-40 border-b border-[#041627]/10 bg-[rgba(251,248,241,0.92)] backdrop-blur-xl">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-4 md:px-10">
          <a href="/" className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-2xl bg-[#041627] text-[#a5eff0] shadow-[0_10px_24px_rgba(4,22,39,0.16)]">
              <span className="material-symbols-outlined text-[22px]">verified_user</span>
            </div>
            <div>
              <p className="font-headline text-2xl leading-none text-[#041627]">Socio AI</p>
              <p className="text-[10px] uppercase tracking-[0.24em] text-[#b89a5a]">Dossier de auditoría</p>
            </div>
          </a>

          <nav className="hidden items-center gap-8 lg:flex">
            <a className="text-[12px] uppercase tracking-[0.16em] text-slate-700 transition hover:text-[#041627]" href="#solution">
              Solución
            </a>
            <a className="text-[12px] uppercase tracking-[0.16em] text-slate-700 transition hover:text-[#041627]" href="#how-it-works">
              Cómo funciona
            </a>
            <a className="text-[12px] uppercase tracking-[0.16em] text-slate-700 transition hover:text-[#041627]" href="#resources">
              Recursos
            </a>
            <a className="text-[12px] uppercase tracking-[0.16em] text-slate-700 transition hover:text-[#041627]" href="#about">
              Nosotros
            </a>
          </nav>

          <div className="flex items-center gap-3">
            <a
              href="/"
              className="hidden rounded-full border border-[#041627]/20 px-5 py-3 text-xs font-semibold uppercase tracking-[0.16em] text-[#041627] transition hover:border-[#041627]/40 hover:bg-white lg:inline-flex"
            >
              Iniciar sesión
            </a>
            <a
              href="mailto:soporte@socioai.app?subject=Solicitud%20de%20demo%20Socio%20AI"
              className="inline-flex items-center gap-2 rounded-full bg-[#041627] px-5 py-3 text-xs font-semibold uppercase tracking-[0.16em] text-white shadow-[0_16px_28px_rgba(4,22,39,0.18)] transition hover:opacity-95"
            >
              Solicitar demo
              <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
            </a>
          </div>
        </div>
      </header>

      <main>
        <section className="relative mx-auto w-full max-w-7xl px-6 pb-14 pt-12 md:px-10 md:pb-20 md:pt-16">
          <div className="grid items-center gap-12 lg:grid-cols-[0.98fr_1.02fr]">
            <div className="max-w-2xl">
              <p className="text-[11px] uppercase tracking-[0.3em] text-[#b89a5a]">Inteligencia que respalda tu juicio</p>
              <h1 className="mt-4 font-headline text-5xl leading-[1.02] text-[#041627] md:text-6xl">
                Eleva el juicio.
                <br />
                Asegura la trazabilidad.
                <br />
                Trabaja con <span className="text-[#3b7f7a]">confianza</span>.
              </h1>
              <p className="mt-6 max-w-xl text-base leading-relaxed text-slate-600 md:text-xl">
                Socio AI combina experiencia y tecnología para transformar auditorías en decisiones respaldadas,
                transparentes y defendibles.
              </p>

              <div className="mt-8 flex flex-wrap items-center gap-3">
                <a
                  href="mailto:soporte@socioai.app?subject=Solicitud%20de%20demo%20Socio%20AI"
                  aria-label="Solicitar demo de Socio AI"
                  className="inline-flex items-center gap-2 rounded-full bg-[#041627] px-6 py-3 text-sm font-semibold uppercase tracking-[0.14em] text-white shadow-[0_16px_28px_rgba(4,22,39,0.18)] transition hover:opacity-95"
                >
                  Solicitar demo
                  <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                </a>
                <a
                  href="#solution"
                  aria-label="Ir a la sección de solución"
                  className="inline-flex items-center gap-2 rounded-full border border-[#041627]/20 px-6 py-3 text-sm font-semibold uppercase tracking-[0.14em] text-[#041627] transition hover:border-[#041627]/40 hover:bg-white"
                >
                  Conocer la solución
                  <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
                </a>
              </div>

              <div className="mt-8 flex flex-wrap items-center gap-4">
                <div className="rounded-full border border-[#b89a5a]/35 bg-white/70 px-4 py-2 text-[11px] uppercase tracking-[0.2em] text-[#b89a5a]">
                  Confidencial
                </div>
                <div className="rounded-full border border-[#d8e1e8] bg-white/70 px-4 py-2 text-[11px] uppercase tracking-[0.2em] text-slate-600">
                  Capítulo 01 · Apertura
                </div>
                <div className="font-headline italic text-3xl text-[#3b7f7a]">Socio AI</div>
                <div className="text-sm text-slate-500">Firma en el expediente</div>
              </div>
            </div>

            <div className="relative">
              <div className="absolute inset-0 rounded-[36px] bg-[radial-gradient(circle_at_30%_25%,rgba(59,127,122,0.12),transparent_22%),radial-gradient(circle_at_75%_15%,rgba(184,154,90,0.1),transparent_18%),radial-gradient(circle_at_70%_75%,rgba(165,239,240,0.16),transparent_24%)]" />
              <div className="relative h-[560px] overflow-hidden rounded-[36px] border border-[#d8e1e8] bg-[linear-gradient(180deg,#fbf8f1_0%,#f5efe4_100%)] shadow-[0_28px_80px_rgba(24,28,30,0.12)]">
                <div
                  className="absolute inset-0 opacity-[0.35]"
                  style={{
                    backgroundImage:
                      "linear-gradient(rgba(4,22,39,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(4,22,39,0.05) 1px, transparent 1px)",
                    backgroundSize: "60px 60px",
                  }}
                />

                <div className="absolute left-6 top-6 rounded-full border border-[#b89a5a]/35 bg-white/80 px-4 py-2 text-[10px] uppercase tracking-[0.24em] text-[#b89a5a] shadow-[0_10px_20px_rgba(0,0,0,0.06)]">
                  Caso activo
                </div>

                <div className="absolute right-6 top-6 rounded-full border border-[#041627]/10 bg-white/80 px-4 py-2 text-[10px] uppercase tracking-[0.24em] text-slate-600">
                  Expediente AI-0247-25
                </div>

                <div className="absolute right-5 top-24 rounded-[20px] border border-[#d8e1e8] bg-white/90 px-4 py-5 text-[#243041] shadow-[0_16px_30px_rgba(24,28,30,0.08)]">
                  <p className="text-[10px] uppercase tracking-[0.24em] text-[#b89a5a]">Índice del dossier</p>
                  <div className="mt-4 space-y-2 text-sm">
                    <p>01 Apertura</p>
                    <p>02 Juicio aumentado</p>
                    <p>03 Trazabilidad completa</p>
                    <p>04 Cierre y notas</p>
                  </div>
                </div>

                <div className="absolute left-10 top-24 h-[200px] w-[230px] -rotate-6 rounded-[24px] border border-[#d8cdb8] bg-[#f7f1e4] shadow-[0_18px_30px_rgba(0,0,0,0.08)]" />
                <div className="absolute left-16 top-28 h-[200px] w-[230px] rotate-[-2deg] rounded-[24px] border border-[#d8cdb8] bg-[#fbf5ea] shadow-[0_18px_30px_rgba(0,0,0,0.08)]" />
                <div className="absolute left-20 top-32 h-[270px] w-[320px] rounded-[28px] border border-[#041627]/12 bg-white shadow-[0_24px_48px_rgba(0,0,0,0.12)]">
                  <div className="absolute -top-5 left-1/2 grid h-12 w-12 -translate-x-1/2 place-items-center rounded-full border border-[#b89a5a]/40 bg-[#f5f1e8] text-[#b89a5a] shadow-[0_8px_18px_rgba(0,0,0,0.12)]">
                    <span className="material-symbols-outlined text-[22px]">attachment</span>
                  </div>
                  <div className="flex h-full flex-col justify-between p-6">
                    <div>
                      <p className="text-[10px] uppercase tracking-[0.24em] text-[#3b7f7a]">Página 1 · Apertura</p>
                      <h2 className="mt-3 font-headline text-3xl text-[#041627]">Juicio aumentado</h2>
                      <p className="mt-2 text-sm leading-relaxed text-slate-600">
                        Organiza la información relevante para mejores conclusiones.
                      </p>
                    </div>

                    <div className="space-y-3">
                      <div className="flex items-center gap-3 rounded-2xl border border-[#d8e1e8] bg-[#faf7f0] px-4 py-3">
                        <span className="material-symbols-outlined text-[18px] text-[#3b7f7a]">check_circle</span>
                        <p className="text-sm text-slate-700">Evidencia trazable</p>
                      </div>
                      <div className="flex items-center gap-3 rounded-2xl border border-[#d8e1e8] bg-[#faf7f0] px-4 py-3">
                        <span className="material-symbols-outlined text-[18px] text-[#3b7f7a]">verified</span>
                        <p className="text-sm text-slate-700">Criterio defendible</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="absolute right-12 bottom-12 w-[200px] rotate-[7deg] rounded-[22px] border border-[#b89a5a]/25 bg-[#f7f1e4] px-4 py-4 text-[#243041] shadow-[0_16px_28px_rgba(0,0,0,0.08)]">
                  <p className="text-[10px] uppercase tracking-[0.24em] text-[#b89a5a]">Confidencial</p>
                  <p className="mt-2 text-sm leading-relaxed text-slate-700">Uso restringido · Solo personal autorizado</p>
                </div>

                <div className="absolute bottom-8 left-8 right-8 rounded-[28px] border border-[#d8e1e8] bg-[rgba(255,255,255,0.78)] px-5 py-4 shadow-[0_14px_28px_rgba(0,0,0,0.06)] backdrop-blur-[2px]">
                  <div className="grid gap-3 md:grid-cols-3">
                    <div>
                      <p className="text-[10px] uppercase tracking-[0.2em] text-[#b89a5a]">Contexto</p>
                      <p className="mt-1 text-sm text-slate-700">Auditoría guiada por rol</p>
                    </div>
                    <div>
                      <p className="text-[10px] uppercase tracking-[0.2em] text-[#b89a5a]">Señal</p>
                      <p className="mt-1 text-sm text-slate-700">Riesgos, pruebas y cierre</p>
                    </div>
                    <div>
                      <p className="text-[10px] uppercase tracking-[0.2em] text-[#b89a5a]">Firma</p>
                      <p className="mt-1 text-sm text-slate-700">Socio AI en el expediente</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="solution" className="mx-auto w-full max-w-7xl px-6 pb-16 md:px-10">
          <div className="grid gap-4 lg:grid-cols-3">
            {featureCards.map((card) => (
              <article
                key={card.title}
                className="rounded-[26px] border border-[#d8e1e8] bg-[rgba(255,255,255,0.78)] p-6 shadow-[0_14px_32px_rgba(24,28,30,0.05)] backdrop-blur-[2px]"
              >
                <p className="text-[10px] uppercase tracking-[0.24em] text-[#b89a5a]">{card.label}</p>
                <div className="mt-4 flex items-start gap-4">
                  <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl border border-[#d8e1e8] bg-[#f7f1e6] text-[#3b7f7a]">
                    <span className="material-symbols-outlined text-[22px]">{card.icon}</span>
                  </div>
                  <div>
                    <h3 className="font-headline text-2xl text-[#041627]">{card.title}</h3>
                    <p className="mt-2 text-sm leading-relaxed text-slate-600">{card.body}</p>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section id="resources" className="mx-auto w-full max-w-7xl px-6 pb-16 md:px-10">
          <div className="rounded-[32px] border border-[#d8e1e8] bg-[rgba(255,255,255,0.72)] px-6 py-8 shadow-[0_16px_32px_rgba(24,28,30,0.05)] md:px-8">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
              <div className="max-w-2xl">
                <p className="text-[11px] uppercase tracking-[0.24em] text-[#b89a5a]">Construido sobre estándares globales</p>
                <h2 className="mt-3 font-headline text-3xl text-[#041627] md:text-4xl">
                  Diseñado para firmas que valoran el rigor y la calidad.
                </h2>
              </div>
              <p className="max-w-lg text-sm leading-relaxed text-slate-600">
                Cada hallazgo, evidencia y conclusión queda con una línea clara de respaldo para que el equipo avance
                con más criterio y menos fricción.
              </p>
            </div>

            <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {trustMarks.map((mark) => (
                <div key={mark.name} className="rounded-[24px] border border-[#d8e1e8] bg-[#faf7f0] px-4 py-5">
                  <div className="flex items-center gap-3">
                    <div className="grid h-11 w-11 place-items-center rounded-2xl border border-[#d8e1e8] bg-white text-[#041627]">
                      <span className="material-symbols-outlined text-[20px]">{mark.icon}</span>
                    </div>
                    <div>
                      <p className="font-headline text-xl text-[#041627]">{mark.name}</p>
                      <p className="mt-1 text-xs uppercase tracking-[0.14em] text-slate-500">{mark.copy}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="about" className="mx-auto w-full max-w-7xl px-6 pb-16 md:px-10">
          <div className="rounded-[34px] border border-[#1a2b3c] bg-[#041627] px-6 py-10 text-white shadow-[0_24px_60px_rgba(4,22,39,0.18)] md:px-10">
            <div className="grid gap-8 lg:grid-cols-[1.15fr_0.85fr] lg:items-center">
              <div>
                <p className="text-[11px] uppercase tracking-[0.28em] text-[#a7d9d3]">Hecho para auditores</p>
                <h2 className="mt-4 font-headline text-4xl leading-[1.04] md:text-5xl">
                  Socio AI no reemplaza tu experiencia.
                  <br />
                  La potencia para que <span className="text-[#a5eff0]">tu juicio</span> llegue más lejos.
                </h2>
              </div>
              <div className="space-y-4">
                <p className="text-base leading-relaxed text-slate-200/85">
                  Liberamos tiempo de lo repetitivo para que te enfoques en lo que realmente importa: analizar,
                  cuestionar y concluir con criterio.
                </p>
                <div className="flex items-center gap-3">
                  <div className="grid h-12 w-12 place-items-center rounded-full border border-[#b89a5a]/35 text-[#b89a5a]">
                    <span className="material-symbols-outlined text-[22px]">stylus</span>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.24em] text-[#b89a5a]">Socio AI</p>
                    <p className="font-headline text-2xl italic text-[#a5eff0]">Firma del expediente</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-8 flex flex-wrap items-center justify-between gap-4 border-t border-white/10 pt-6 text-xs uppercase tracking-[0.18em] text-slate-300/80">
              <p>Registro final · 24 / 05 / 25</p>
              <p>Versión 1.0</p>
              <p>Auditoría inteligente · decisiones confiables</p>
            </div>
          </div>
        </section>

        <section id="how-it-works" className="mx-auto w-full max-w-7xl px-6 pb-16 md:px-10">
          <div className="rounded-[28px] border border-[#d8e1e8] bg-[rgba(255,255,255,0.72)] px-6 py-8 shadow-[0_16px_32px_rgba(24,28,30,0.05)] md:px-8">
            <p className="text-[11px] uppercase tracking-[0.24em] text-[#b89a5a]">Cómo funciona</p>
            <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-600">
              La experiencia arranca en el login, se organiza en la landing y desemboca en una cartera y un dashboard
              más limpios, para que el usuario entienda el flujo sin perderse.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}
