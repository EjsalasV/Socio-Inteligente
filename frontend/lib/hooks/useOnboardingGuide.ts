"use client";

import { useCallback, useEffect, useMemo } from "react";

import { useUserPreferences } from "../../components/providers/UserPreferencesProvider";

type GuideModule =
  | "perfil"
  | "trial-balance"
  | "risk-engine"
  | "areas"
  | "papeles-trabajo"
  | "reportes";

type OnboardingStep = {
  module: GuideModule;
  label: string;
  description: string;
  href: (clienteId: string) => string;
};

type OnboardingGuideState = {
  steps: Array<OnboardingStep & { done: boolean }>;
  completedCount: number;
  totalCount: number;
  progressPct: number;
  nextStep: (OnboardingStep & { done: boolean }) | null;
  dismissed: boolean;
  welcomeSeen: boolean;
  dismissGuide: () => void;
  showGuide: () => void;
  markWelcomeSeen: () => void;
};

const ONBOARDING_STEPS: OnboardingStep[] = [
  {
    module: "perfil",
    label: "Completar Perfil",
    description: "Define marco, materialidad y datos base del encargo.",
    href: (clienteId) => `/perfil/${clienteId}`,
  },
  {
    module: "trial-balance",
    label: "Revisar Trial Balance",
    description: "Valida saldos, variaciones y alertas iniciales.",
    href: (clienteId) => `/trial-balance/${clienteId}`,
  },
  {
    module: "risk-engine",
    label: "Priorizar en Risk Engine",
    description: "Ordena áreas por riesgo y define foco de pruebas.",
    href: (clienteId) => `/risk-engine/${clienteId}`,
  },
  {
    module: "areas",
    label: "Ejecutar en Workspace Áreas",
    description: "Genera briefing, consulta y estructura hallazgos.",
    href: (clienteId) => `/areas/${clienteId}`,
  },
  {
    module: "papeles-trabajo",
    label: "Consolidar Papeles",
    description: "Marca evidencia y revisa quality gates.",
    href: (clienteId) => `/papeles-trabajo/${clienteId}`,
  },
  {
    module: "reportes",
    label: "Emitir Reportes",
    description: "Genera borrador/final con trazabilidad.",
    href: (clienteId) => `/reportes/${clienteId}`,
  },
];

function isGuideModule(value: string): value is GuideModule {
  return ONBOARDING_STEPS.some((step) => step.module === value);
}

export function useOnboardingGuide(moduleKey: string): OnboardingGuideState {
  const { preferences, patchPreferences, loading } = useUserPreferences();
  const visitedModules = useMemo(() => {
    const raw = preferences.onboarding_ui?.visited_modules_ui;
    if (!Array.isArray(raw)) return [];
    const unique = new Set<string>();
    for (const value of raw) {
      const clean = String(value || "").trim();
      if (!clean) continue;
      unique.add(clean);
    }
    return Array.from(unique);
  }, [preferences.onboarding_ui?.visited_modules_ui]);
  const dismissed = Boolean(preferences.onboarding_ui?.dismissed);
  const welcomeSeen = Boolean(preferences.onboarding_ui?.welcome_seen);

  useEffect(() => {
    if (loading) return;
    if (!isGuideModule(moduleKey)) return;
    if (visitedModules.includes(moduleKey)) return;
    const nextVisited = [...visitedModules, moduleKey];
    void patchPreferences({
      onboarding_ui: {
        visited_modules_ui: nextVisited,
      },
    });
  }, [loading, moduleKey, patchPreferences, visitedModules]);

  const steps = useMemo(
    () =>
      ONBOARDING_STEPS.map((step) => ({
        ...step,
        done: visitedModules.includes(step.module),
      })),
    [visitedModules],
  );
  const completedCount = useMemo(() => steps.filter((step) => step.done).length, [steps]);
  const totalCount = steps.length;
  const progressPct = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;
  const nextStep = steps.find((step) => !step.done) ?? null;

  const dismissGuide = useCallback(() => {
    void patchPreferences({
      onboarding_ui: {
        dismissed: true,
      },
    });
  }, [patchPreferences]);

  const showGuide = useCallback(() => {
    void patchPreferences({
      onboarding_ui: {
        dismissed: false,
      },
    });
  }, [patchPreferences]);

  const markWelcomeSeen = useCallback(() => {
    void patchPreferences({
      onboarding_ui: {
        welcome_seen: true,
      },
    });
  }, [patchPreferences]);

  return {
    steps,
    completedCount,
    totalCount,
    progressPct,
    nextStep,
    dismissed,
    welcomeSeen,
    dismissGuide,
    showGuide,
    markWelcomeSeen,
  };
}
