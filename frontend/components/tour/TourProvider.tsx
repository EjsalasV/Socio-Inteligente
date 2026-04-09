"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { ACTIONS, EVENTS, Joyride, STATUS, type EventData, type Step } from "react-joyride";

import { TOUR_MODULES, TOUR_STEPS, TOUR_STORAGE_KEYS, type TourModule } from "../../lib/tour/config";
import { useUserPreferences } from "../providers/UserPreferencesProvider";

type TourContextValue = {
  activeModule: TourModule | null;
  startTour: (module?: TourModule) => void;
  stopTour: () => void;
  resetTours: () => void;
};

const TourContext = createContext<TourContextValue | null>(null);

function resolveTourModule(pathname: string): TourModule | null {
  if (pathname.startsWith("/clientes")) return "clientes";
  if (/^\/perfil\/[^/]+/.test(pathname)) return "perfil";
  if (/^\/dashboard\/[^/]+/.test(pathname)) return "dashboard";
  if (/^\/risk-engine\/[^/]+/.test(pathname)) return "risk-engine";
  if (/^\/trial-balance\/[^/]+/.test(pathname)) return "trial-balance";
  if (/^\/estados-financieros\/[^/]+/.test(pathname)) return "estados-financieros";
  if (/^\/areas\/[^/]+\/[^/]+/.test(pathname)) return "areas";
  if (/^\/papeles-trabajo\/[^/]+/.test(pathname)) return "papeles-trabajo";
  if (/^\/reportes\/[^/]+/.test(pathname)) return "reportes";
  if (/^\/socio-chat\/[^/]+/.test(pathname)) return "socio-chat";
  if (/^\/client-memory\/[^/]+/.test(pathname)) return "client-memory";
  return null;
}

function isTourModule(value: string): value is TourModule {
  return (TOUR_MODULES as readonly string[]).includes(value);
}

function readStringArrayStorage(key: string, session = false): string[] {
  if (typeof window === "undefined") return [];
  const storage = session ? window.sessionStorage : window.localStorage;
  try {
    const raw = storage.getItem(key);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.map((x) => String(x)) : [];
  } catch {
    return [];
  }
}

function writeStringArrayStorage(key: string, values: string[], session = false): void {
  if (typeof window === "undefined") return;
  const storage = session ? window.sessionStorage : window.localStorage;
  storage.setItem(key, JSON.stringify(Array.from(new Set(values))));
}

export default function TourProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const activeModule = useMemo(() => resolveTourModule(pathname), [pathname]);
  const { loading: preferencesLoading, preferences, patchPreferences } = useUserPreferences();

  const [run, setRun] = useState(false);
  const [steps, setSteps] = useState<Step[]>([]);
  const [stepIndex, setStepIndex] = useState(0);
  const [currentModule, setCurrentModule] = useState<TourModule | null>(null);
  const [dismissedInSession, setDismissedInSession] = useState<TourModule[]>([]);
  const lastAutoLaunchRef = useRef<string>("");
  const completedModules = useMemo(
    () =>
      (Array.isArray(preferences.tour_completed_modules) ? preferences.tour_completed_modules : [])
        .filter((x): x is TourModule => isTourModule(String(x)))
        .map((x) => x as TourModule),
    [preferences.tour_completed_modules],
  );
  const onboardingWelcomeSeen = Boolean(preferences.onboarding_ui?.welcome_seen);

  useEffect(() => {
    setDismissedInSession(
      readStringArrayStorage(TOUR_STORAGE_KEYS.dismissedInSession, true).filter((x): x is TourModule =>
        isTourModule(x),
      ),
    );
  }, []);

  const startTour = useCallback(
    (module?: TourModule) => {
      const resolved = module ?? activeModule;
      if (!resolved || typeof window === "undefined") return;

      const moduleSteps = TOUR_STEPS[resolved] ?? [];
      if (!moduleSteps.length) return;

      const availableSteps = moduleSteps
        .filter((step) => {
          const target = typeof step.target === "string" ? step.target : "";
          return !!target && !!document.querySelector(target);
        })
        .map((step) => ({
          ...step,
          hideOverlay: true,
          disableFocusTrap: true,
          blockTargetInteraction: false,
          overlayClickAction: "close" as const,
        }));
      if (!availableSteps.length) return;

      setCurrentModule(resolved);
      setSteps(availableSteps);
      setStepIndex(0);
      setRun(true);
      if (!preferences.tour_welcome_seen) {
        void patchPreferences({ tour_welcome_seen: true });
      }
    },
    [activeModule, patchPreferences, preferences.tour_welcome_seen],
  );

  const resetTours = useCallback(() => {
    if (typeof window === "undefined") return;
    window.sessionStorage.removeItem(TOUR_STORAGE_KEYS.dismissedInSession);
    setDismissedInSession([]);
    void patchPreferences({
      tour_completed_modules: [],
      tour_welcome_seen: false,
      onboarding_ui: {
        welcome_seen: false,
        dismissed: false,
      },
    });
  }, [patchPreferences]);

  const stopTour = useCallback(() => {
    setRun(false);
    setStepIndex(0);
    setCurrentModule(null);
  }, []);

  useEffect(() => {
    if (preferencesLoading) return;
    if (!activeModule || run) return;
    if (completedModules.includes(activeModule)) return;
    if (dismissedInSession.includes(activeModule)) return;
    // Evita que el tour tape el modal de bienvenida de onboarding.
    if (activeModule !== "clientes" && !onboardingWelcomeSeen) return;

    const launchKey = `${pathname}:${activeModule}`;
    if (lastAutoLaunchRef.current === launchKey) return;
    lastAutoLaunchRef.current = launchKey;

    if (!preferences.tour_welcome_seen) {
      void patchPreferences({ tour_welcome_seen: true });
    }
    const timer = window.setTimeout(() => startTour(activeModule), 350);
    return () => window.clearTimeout(timer);
  }, [
    activeModule,
    completedModules,
    dismissedInSession,
    onboardingWelcomeSeen,
    pathname,
    patchPreferences,
    preferences.tour_welcome_seen,
    preferencesLoading,
    run,
    startTour,
  ]);

  const handleJoyrideCallback = useCallback(
    (data: EventData) => {
      const { action, index, status, type } = data;

      if (type === EVENTS.TARGET_NOT_FOUND) {
        setStepIndex((prev) => {
          const next = prev + 1;
          if (next >= steps.length) {
            stopTour();
            return 0;
          }
          return next;
        });
        return;
      }

      if (type === EVENTS.STEP_AFTER) {
        const next = action === ACTIONS.PREV ? index - 1 : index + 1;
        setStepIndex(next < 0 ? 0 : next);
      }

      if (status === STATUS.FINISHED) {
        if (currentModule) {
          const nextCompleted = Array.from(new Set([...completedModules, currentModule])) as TourModule[];
          void patchPreferences({ tour_completed_modules: nextCompleted });
        }
        stopTour();
        return;
      }

      if (status === STATUS.SKIPPED || action === ACTIONS.CLOSE) {
        if (currentModule) {
          const nextDismissed = Array.from(new Set([...dismissedInSession, currentModule])) as TourModule[];
          setDismissedInSession(nextDismissed);
          writeStringArrayStorage(TOUR_STORAGE_KEYS.dismissedInSession, nextDismissed, true);
        }
        stopTour();
      }
    },
    [completedModules, currentModule, dismissedInSession, patchPreferences, steps.length, stopTour],
  );

  useEffect(() => {
    // Si el usuario cambia de módulo mientras el tour corre, cerramos para no bloquear la UI.
    if (!run || !currentModule || !activeModule) return;
    if (currentModule !== activeModule) {
      stopTour();
    }
  }, [activeModule, currentModule, run, stopTour]);

  const value = useMemo<TourContextValue>(
    () => ({
      activeModule,
      startTour,
      stopTour,
      resetTours,
    }),
    [activeModule, resetTours, startTour, stopTour],
  );

  return (
    <TourContext.Provider value={value}>
      {children}
      <Joyride
        run={run}
        stepIndex={stepIndex}
        steps={steps}
        onEvent={handleJoyrideCallback}
        continuous
        scrollToFirstStep
        options={{
          buttons: ["back", "close", "primary", "skip"],
          skipScroll: false,
          hideOverlay: true,
          disableFocusTrap: true,
          blockTargetInteraction: false,
          overlayClickAction: "close",
          primaryColor: "#041627",
          textColor: "#0f172a",
          zIndex: 999999,
          overlayColor: "#00000066",
        }}
        locale={{
          back: "Atras",
          close: "Cerrar",
          last: "Finalizar",
          next: "Siguiente",
          skip: "Omitir",
        }}
        styles={{
          tooltip: {
            borderRadius: 14,
          },
          buttonPrimary: {
            borderRadius: 8,
            padding: "8px 14px",
          },
          buttonBack: {
            color: "#334155",
          },
        }}
      />
    </TourContext.Provider>
  );
}

export function useTour(): TourContextValue {
  const ctx = useContext(TourContext);
  if (!ctx) {
    return {
      activeModule: null,
      startTour: () => undefined,
      stopTour: () => undefined,
      resetTours: () => undefined,
    };
  }
  return ctx;
}
