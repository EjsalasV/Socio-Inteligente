"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { ACTIONS, EVENTS, Joyride, STATUS, type EventData, type Step } from "react-joyride";

import { TOUR_MODULES, TOUR_STEPS, TOUR_STORAGE_KEYS, type TourModule } from "../../lib/tour/config";

type TourContextValue = {
  activeModule: TourModule | null;
  startTour: (module?: TourModule) => void;
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

  const [run, setRun] = useState(false);
  const [steps, setSteps] = useState<Step[]>([]);
  const [stepIndex, setStepIndex] = useState(0);
  const [currentModule, setCurrentModule] = useState<TourModule | null>(null);
  const [completedModules, setCompletedModules] = useState<TourModule[]>([]);
  const [dismissedInSession, setDismissedInSession] = useState<TourModule[]>([]);
  const lastAutoLaunchRef = useRef<string>("");

  useEffect(() => {
    setCompletedModules(
      readStringArrayStorage(TOUR_STORAGE_KEYS.completedModules).filter((x): x is TourModule => isTourModule(x)),
    );
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

      const availableSteps = moduleSteps.filter((step) => {
        const target = typeof step.target === "string" ? step.target : "";
        return !!target && !!document.querySelector(target);
      });
      if (!availableSteps.length) return;

      setCurrentModule(resolved);
      setSteps(availableSteps);
      setStepIndex(0);
      setRun(true);
    },
    [activeModule],
  );

  const resetTours = useCallback(() => {
    if (typeof window === "undefined") return;
    window.localStorage.removeItem(TOUR_STORAGE_KEYS.completedModules);
    window.localStorage.removeItem(TOUR_STORAGE_KEYS.welcomeSeen);
    window.sessionStorage.removeItem(TOUR_STORAGE_KEYS.dismissedInSession);
    setCompletedModules([]);
    setDismissedInSession([]);
  }, []);

  useEffect(() => {
    if (!activeModule || run) return;
    if (completedModules.includes(activeModule)) return;
    if (dismissedInSession.includes(activeModule)) return;

    const launchKey = `${pathname}:${activeModule}`;
    if (lastAutoLaunchRef.current === launchKey) return;
    lastAutoLaunchRef.current = launchKey;

    if (typeof window !== "undefined") {
      window.localStorage.setItem(TOUR_STORAGE_KEYS.welcomeSeen, "true");
    }
    const timer = window.setTimeout(() => startTour(activeModule), 350);
    return () => window.clearTimeout(timer);
  }, [activeModule, completedModules, dismissedInSession, pathname, run, startTour]);

  const handleJoyrideCallback = useCallback(
    (data: EventData) => {
      const { action, index, status, type } = data;

      if (type === EVENTS.TARGET_NOT_FOUND) {
        setStepIndex((prev) => prev + 1);
        return;
      }

      if (type === EVENTS.STEP_AFTER) {
        const next = action === ACTIONS.PREV ? index - 1 : index + 1;
        setStepIndex(next < 0 ? 0 : next);
      }

      if (status === STATUS.FINISHED) {
        if (currentModule) {
          const nextCompleted = Array.from(new Set([...completedModules, currentModule])) as TourModule[];
          setCompletedModules(nextCompleted);
          writeStringArrayStorage(TOUR_STORAGE_KEYS.completedModules, nextCompleted);
        }
        setRun(false);
        setStepIndex(0);
        return;
      }

      if (status === STATUS.SKIPPED || action === ACTIONS.CLOSE) {
        if (currentModule) {
          const nextDismissed = Array.from(new Set([...dismissedInSession, currentModule])) as TourModule[];
          setDismissedInSession(nextDismissed);
          writeStringArrayStorage(TOUR_STORAGE_KEYS.dismissedInSession, nextDismissed, true);
        }
        setRun(false);
        setStepIndex(0);
      }
    },
    [completedModules, currentModule, dismissedInSession],
  );

  const value = useMemo<TourContextValue>(
    () => ({
      activeModule,
      startTour,
      resetTours,
    }),
    [activeModule, resetTours, startTour],
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
      resetTours: () => undefined,
    };
  }
  return ctx;
}
