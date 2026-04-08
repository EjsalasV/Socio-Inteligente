"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

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

const STORAGE_KEYS = {
  visitedModules: "onboarding:v1:visited_modules",
  dismissed: "onboarding:v1:dismissed",
  welcomeSeen: "onboarding:v1:welcome_seen",
} as const;

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
    description: "Ordena areas por riesgo y define foco de pruebas.",
    href: (clienteId) => `/risk-engine/${clienteId}`,
  },
  {
    module: "areas",
    label: "Ejecutar en Workspace Areas",
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

function readVisitedModules(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEYS.visitedModules);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.map((x) => String(x));
  } catch {
    return [];
  }
}

function writeVisitedModules(modules: string[]): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEYS.visitedModules, JSON.stringify(Array.from(new Set(modules))));
}

function readBoolean(key: string): boolean {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(key) === "true";
}

function writeBoolean(key: string, value: boolean): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(key, value ? "true" : "false");
}

function isGuideModule(value: string): value is GuideModule {
  return ONBOARDING_STEPS.some((step) => step.module === value);
}

export function useOnboardingGuide(moduleKey: string): OnboardingGuideState {
  const [visitedModules, setVisitedModules] = useState<string[]>([]);
  const [dismissed, setDismissed] = useState<boolean>(false);
  const [welcomeSeen, setWelcomeSeen] = useState<boolean>(false);

  useEffect(() => {
    setVisitedModules(readVisitedModules());
    setDismissed(readBoolean(STORAGE_KEYS.dismissed));
    setWelcomeSeen(readBoolean(STORAGE_KEYS.welcomeSeen));
  }, []);

  useEffect(() => {
    if (!isGuideModule(moduleKey)) return;
    setVisitedModules((prev) => {
      if (prev.includes(moduleKey)) return prev;
      const next = [...prev, moduleKey];
      writeVisitedModules(next);
      return next;
    });
  }, [moduleKey]);

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
    setDismissed(true);
    writeBoolean(STORAGE_KEYS.dismissed, true);
  }, []);

  const showGuide = useCallback(() => {
    setDismissed(false);
    writeBoolean(STORAGE_KEYS.dismissed, false);
  }, []);

  const markWelcomeSeen = useCallback(() => {
    setWelcomeSeen(true);
    writeBoolean(STORAGE_KEYS.welcomeSeen, true);
  }, []);

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

