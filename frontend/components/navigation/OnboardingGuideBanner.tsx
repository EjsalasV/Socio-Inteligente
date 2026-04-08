"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { useTour } from "../tour/TourProvider";
import { useOnboardingGuide } from "../../lib/hooks/useOnboardingGuide";
import { useAuditContext } from "../../lib/hooks/useAuditContext";

export default function OnboardingGuideBanner() {
  const router = useRouter();
  const { clienteId, moduleKey } = useAuditContext();
  const { startTour } = useTour();
  const [hideWelcome, setHideWelcome] = useState<boolean>(false);

  const guide = useOnboardingGuide(moduleKey);

  const showWelcome = useMemo(
    () => !guide.welcomeSeen && !hideWelcome && !!clienteId,
    [guide.welcomeSeen, hideWelcome, clienteId],
  );

  if (!clienteId) return null;

  return (
    <>
      {showWelcome ? (
        <div className="fixed inset-0 z-[100000] bg-black/45 backdrop-blur-[1px] flex items-center justify-center p-4">
          <div className="w-full max-w-2xl rounded-2xl border border-[#041627]/20 bg-white shadow-2xl p-6 md:p-8">
            <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 font-bold">Primer ingreso</p>
            <h2 className="font-headline text-3xl text-[#041627] mt-2">Bienvenido a Socio AI</h2>
            <p className="text-sm text-slate-600 mt-3 leading-relaxed">
              Sigue la guia de 6 pasos para completar una auditoria de punta a punta sin perderte.
            </p>

            <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-3">
              <button
                type="button"
                onClick={() => {
                  guide.markWelcomeSeen();
                  guide.showGuide();
                  startTour();
                }}
                className="px-4 py-3 rounded-xl bg-[#041627] text-white text-sm font-semibold"
              >
                Iniciar tutorial
              </button>
              <button
                type="button"
                onClick={() => {
                  guide.markWelcomeSeen();
                  guide.showGuide();
                  router.push(`/perfil/${clienteId}`);
                }}
                className="px-4 py-3 rounded-xl border border-[#041627]/15 text-[#041627] text-sm font-semibold bg-white"
              >
                Empezar por Perfil
              </button>
              <button
                type="button"
                onClick={() => {
                  guide.markWelcomeSeen();
                  setHideWelcome(true);
                }}
                className="px-4 py-3 rounded-xl border border-slate-300 text-slate-600 text-sm font-semibold bg-white"
              >
                Omitir por ahora
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {!guide.dismissed ? (
        <div className="mx-4 md:mx-8 mt-4 rounded-xl border border-[#041627]/10 bg-white/90 backdrop-blur-sm p-4">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
            <div>
              <p className="text-[10px] uppercase tracking-[0.14em] text-slate-500 font-bold">Guia del sistema</p>
              <h3 className="font-headline text-xl text-[#041627]">
                Progreso onboarding: {guide.completedCount}/{guide.totalCount} ({guide.progressPct}%)
              </h3>
              <p className="text-sm text-slate-600 mt-1">
                {guide.nextStep
                  ? `Siguiente accion: ${guide.nextStep.label}. ${guide.nextStep.description}`
                  : "Checklist completado. Ya puedes operar el flujo completo."}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {guide.nextStep ? (
                <button
                  type="button"
                  onClick={() => router.push(guide.nextStep!.href(clienteId))}
                  className="px-3 py-2 rounded-lg bg-[#041627] text-white text-xs font-semibold uppercase tracking-[0.08em]"
                >
                  Ir al siguiente paso
                </button>
              ) : null}
              <button
                type="button"
                onClick={() => startTour()}
                className="px-3 py-2 rounded-lg border border-[#041627]/20 text-slate-700 text-xs font-semibold uppercase tracking-[0.08em]"
              >
                Ver tutorial modulo
              </button>
              <button
                type="button"
                onClick={guide.dismissGuide}
                className="px-3 py-2 rounded-lg border border-slate-300 text-slate-600 text-xs font-semibold uppercase tracking-[0.08em]"
              >
                Ocultar
              </button>
            </div>
          </div>

          <div className="mt-4 w-full h-2 rounded-full bg-[#e8edf3] overflow-hidden">
            <div className="h-full bg-[#041627]" style={{ width: `${guide.progressPct}%` }} />
          </div>
          <div className="mt-3 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2">
            {guide.steps.map((step) => (
              <button
                key={step.module}
                type="button"
                onClick={() => router.push(step.href(clienteId))}
                className={`text-left px-3 py-2 rounded-lg border text-xs ${
                  step.done
                    ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                    : "bg-white border-slate-200 text-slate-700"
                }`}
              >
                <span className="font-semibold">{step.done ? "Completado:" : "Pendiente:"}</span> {step.label}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="mx-4 md:mx-8 mt-4">
          <button
            type="button"
            onClick={guide.showGuide}
            className="px-3 py-2 rounded-lg border border-[#041627]/20 bg-white text-slate-700 text-xs font-semibold uppercase tracking-[0.08em]"
          >
            Mostrar guia de onboarding
          </button>
        </div>
      )}
    </>
  );
}

