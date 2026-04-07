"use client";

import type { Step } from "react-joyride";

export type TourModule = "clientes" | "risk-engine" | "areas";

export const TOUR_STORAGE_KEYS = {
  completedModules: "tour:v1:completed_modules",
  welcomeSeen: "tour:v1:welcome_seen",
  dismissedInSession: "tour:v1:dismissed_modules_session",
} as const;

export const TOUR_STEPS: Record<TourModule, Step[]> = {
  clientes: [
    {
      target: '[data-tour="clientes-title"]',
      content: "Aquí gestionas la cartera de clientes. Desde esta pantalla arrancas cada encargo.",
      skipBeacon: true,
      placement: "bottom",
    },
    {
      target: '[data-tour="clientes-search"]',
      content: "Usa este buscador para encontrar rápido un cliente por nombre, sector o ID.",
      placement: "bottom",
    },
    {
      target: '[data-tour="clientes-open-dashboard-link"]',
      content: "Desde aquí abres el dashboard del cliente para iniciar análisis y priorización.",
      placement: "left",
    },
    {
      target: '[data-tour="clientes-onboarding-link"]',
      content: "Si el cliente es nuevo o falta contexto, entra a Onboarding antes de auditar.",
      placement: "left",
    },
    {
      target: '[data-tour="clientes-form"]',
      content: "En este bloque puedes crear un cliente nuevo y continuar directo al onboarding.",
      placement: "left",
    },
  ],
  "risk-engine": [
    {
      target: '[data-tour="sidebar-risk-engine"]',
      content: "Este módulo prioriza riesgos para decidir dónde empezar el trabajo.",
      skipBeacon: true,
      placement: "right",
    },
    {
      target: '[data-tour="risk-title"]',
      content: "Este encabezado resume el objetivo: mapa de calor y exposición de auditoría.",
      placement: "bottom",
    },
    {
      target: '[data-tour="risk-matrix"]',
      content: "La matriz cruza impacto y frecuencia para ubicar áreas críticas.",
      placement: "left",
    },
    {
      target: '[data-tour="risk-critical"]',
      content: "Aquí revisas las áreas críticas detectadas por score y nivel de riesgo.",
      placement: "left",
    },
    {
      target: '[data-tour="sidebar-areas"]',
      content: "Luego abre Workspace Áreas para ejecutar procedimientos en las áreas priorizadas.",
      placement: "right",
    },
  ],
  areas: [
    {
      target: '[data-tour="sidebar-areas"]',
      content: "Ya estás en Workspace Áreas: aquí ejecutas y documentas trabajo técnico.",
      skipBeacon: true,
      placement: "right",
    },
    {
      target: '[data-tour="area-title"]',
      content: "Confirma código y nombre de área antes de iniciar pruebas.",
      placement: "bottom",
    },
    {
      target: '[data-tour="area-lead-schedule"]',
      content: "En el lead schedule validas cuentas, saldos y checks de revisión.",
      placement: "right",
    },
    {
      target: '[data-tour="btn-generar-briefing"]',
      content: "Genera briefing para obtener procedimientos y normativa activada para esta área.",
      placement: "left",
    },
    {
      target: '[data-tour="hallazgo-block"]',
      content: "Si detectas desviaciones, estructura el hallazgo con criterio técnico aquí.",
      placement: "left",
    },
    {
      target: '[data-tour="tiempo-block"]',
      content: "Registra tiempo manual vs AI para medir ahorro real del equipo.",
      placement: "left",
    },
  ],
};
