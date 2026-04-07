"use client";

import type { Step } from "react-joyride";

export const TOUR_MODULES = [
  "clientes",
  "perfil",
  "dashboard",
  "risk-engine",
  "trial-balance",
  "estados-financieros",
  "areas",
  "papeles-trabajo",
  "reportes",
  "socio-chat",
  "client-memory",
] as const;

export type TourModule = (typeof TOUR_MODULES)[number];

export const TOUR_STORAGE_KEYS = {
  completedModules: "tour:v1:completed_modules",
  welcomeSeen: "tour:v1:welcome_seen",
  dismissedInSession: "tour:v1:dismissed_modules_session",
} as const;

export const TOUR_STEPS: Record<TourModule, Step[]> = {
  clientes: [
    {
      target: '[data-tour="clientes-title"]',
      content: "Aqui gestionas la cartera de clientes. Desde esta pantalla arranca cada encargo.",
      skipBeacon: true,
      placement: "bottom",
    },
    {
      target: '[data-tour="clientes-search"]',
      content: "Usa este buscador para encontrar rapido un cliente por nombre, sector o ID.",
      placement: "bottom",
    },
    {
      target: '[data-tour="clientes-open-dashboard-link"]',
      content: "Desde aqui abres el dashboard del cliente para iniciar analisis y priorizacion.",
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
  perfil: [
    {
      target: '[data-tour="sidebar-perfil"]',
      content: "Perfil Cliente concentra datos base del encargo y parametros del trabajo.",
      skipBeacon: true,
      placement: "right",
    },
    {
      target: '[data-tour="perfil-title"]',
      content: "Aqui validas identidad del cliente, marco contable y responsables.",
      placement: "bottom",
    },
    {
      target: '[data-tour="perfil-marco"]',
      content: "Define marco contable y norma de auditoria para alinear todo el flujo.",
      placement: "bottom",
    },
    {
      target: '[data-tour="perfil-save"]',
      content: "Guarda cambios antes de continuar para no perder contexto.",
      placement: "left",
    },
    {
      target: '[data-tour="sidebar-dashboard"]',
      content: "Despues pasa a Dashboard para revisar riesgo global y prioridades.",
      placement: "right",
    },
  ],
  dashboard: [
    {
      target: '[data-tour="sidebar-dashboard"]',
      content: "Este es tu centro ejecutivo por cliente.",
      skipBeacon: true,
      placement: "right",
    },
    {
      target: '[data-tour="dashboard-title"]',
      content: "Aqui ves contexto general, periodo y estado del encargo.",
      placement: "bottom",
    },
    {
      target: '[data-tour="dashboard-kpis"]',
      content: "Estos KPIs resumen avance, materialidad, riesgo y estado de balance.",
      placement: "bottom",
    },
    {
      target: '[data-tour="dashboard-risk-ranking"]',
      content: "Usa este ranking para decidir en que areas empezar trabajo de campo.",
      placement: "top",
    },
    {
      target: '[data-tour="sidebar-risk-engine"]',
      content: "Abre Risk Engine para profundizar la priorizacion de riesgos.",
      placement: "right",
    },
  ],
  "risk-engine": [
    {
      target: '[data-tour="sidebar-risk-engine"]',
      content: "Este modulo prioriza riesgos para decidir donde empezar el trabajo.",
      skipBeacon: true,
      placement: "right",
    },
    {
      target: '[data-tour="risk-title"]',
      content: "Este encabezado resume el objetivo: mapa de calor y exposicion de auditoria.",
      placement: "bottom",
    },
    {
      target: '[data-tour="risk-matrix"]',
      content: "La matriz cruza impacto y frecuencia para ubicar areas criticas.",
      placement: "left",
    },
    {
      target: '[data-tour="risk-critical"]',
      content: "Aqui revisas las areas criticas detectadas por score y nivel de riesgo.",
      placement: "left",
    },
    {
      target: '[data-tour="sidebar-areas"]',
      content: "Luego abre Workspace Areas para ejecutar procedimientos en las areas priorizadas.",
      placement: "right",
    },
  ],
  "trial-balance": [
    {
      target: '[data-tour="sidebar-trial-balance"]',
      content: "Trial Balance sirve para revisar saldos, variaciones y alertas.",
      skipBeacon: true,
      placement: "right",
    },
    {
      target: '[data-tour="trial-title"]',
      content: "Empieza validando cliente, periodo y corte cargado.",
      placement: "bottom",
    },
    {
      target: '[data-tour="trial-area-select"]',
      content: "Cambia de area para revisar cuentas especificas rapidamente.",
      placement: "bottom",
    },
    {
      target: '[data-tour="trial-table"]',
      content: "Aqui identificas variaciones relevantes y cuentas para pruebas.",
      placement: "top",
    },
    {
      target: '[data-tour="trial-ai-guide"]',
      content: "Este panel resume riesgos por aseveracion para la area activa.",
      placement: "left",
    },
  ],
  "estados-financieros": [
    {
      target: '[data-tour="sidebar-estados-financieros"]',
      content: "Este modulo compara estados financieros y materialidad.",
      skipBeacon: true,
      placement: "right",
    },
    {
      target: '[data-tour="estados-title"]',
      content: "Revisa el analisis comparativo del cliente y su periodo.",
      placement: "bottom",
    },
    {
      target: '[data-tour="estados-materialidad"]',
      content: "Aqui ves MP, ME y umbral trivial para evaluar desviaciones.",
      placement: "bottom",
    },
    {
      target: '[data-tour="estados-table"]',
      content: "Tabla central para variaciones y partidas con mayor impacto.",
      placement: "top",
    },
    {
      target: '[data-tour="estados-alertas"]',
      content: "Alertas IA para enfocar pruebas en integridad y valuacion.",
      placement: "right",
    },
  ],
  areas: [
    {
      target: '[data-tour="sidebar-areas"]',
      content: "Ya estas en Workspace Areas: aqui ejecutas y documentas trabajo tecnico.",
      skipBeacon: true,
      placement: "right",
    },
    {
      target: '[data-tour="area-title"]',
      content: "Confirma codigo y nombre de area antes de iniciar pruebas.",
      placement: "bottom",
    },
    {
      target: '[data-tour="area-lead-schedule"]',
      content: "En el lead schedule validas cuentas, saldos y checks de revision.",
      placement: "right",
    },
    {
      target: '[data-tour="btn-generar-briefing"]',
      content: "Genera briefing para obtener procedimientos y normativa activada para esta area.",
      placement: "left",
    },
    {
      target: '[data-tour="hallazgo-block"]',
      content: "Si detectas desviaciones, estructura el hallazgo con criterio tecnico aqui.",
      placement: "left",
    },
    {
      target: '[data-tour="tiempo-block"]',
      content: "Registra tiempo manual vs AI para medir ahorro real del equipo.",
      placement: "left",
    },
  ],
  "papeles-trabajo": [
    {
      target: '[data-tour="sidebar-papeles-trabajo"]',
      content: "Aqui controlas papeles de trabajo, calidad y avance por tarea.",
      skipBeacon: true,
      placement: "right",
    },
    {
      target: '[data-tour="papeles-title"]',
      content: "Vista central de ejecucion con gates y control de cumplimiento.",
      placement: "bottom",
    },
    {
      target: '[data-tour="papeles-gates"]',
      content: "Estos quality gates muestran bloqueos que debes resolver.",
      placement: "bottom",
    },
    {
      target: '[data-tour="papeles-avance"]',
      content: "Monitorea avance y cambia de fase cuando cumples condiciones.",
      placement: "top",
    },
    {
      target: '[data-tour="papeles-tareas"]',
      content: "Aqui registras evidencia por tarea y estado de ejecucion.",
      placement: "top",
    },
  ],
  reportes: [
    {
      target: '[data-tour="sidebar-reportes"]',
      content: "Reportes concentra emision, trazabilidad y gobierno documental.",
      skipBeacon: true,
      placement: "right",
    },
    {
      target: '[data-tour="reportes-title"]',
      content: "Desde aqui gestionas borradores y emision final.",
      placement: "bottom",
    },
    {
      target: '[data-tour="reportes-gates"]',
      content: "Valida gates antes de intentar emitir un informe final.",
      placement: "bottom",
    },
    {
      target: '[data-tour="reportes-actions"]',
      content: "Acciones rapidas para generar PDF, memo y descargas.",
      placement: "top",
    },
    {
      target: '[data-tour="reportes-history"]',
      content: "Historial de artefactos para trazabilidad y control de versiones.",
      placement: "top",
    },
  ],
  "socio-chat": [
    {
      target: '[data-tour="sidebar-socio-chat"]',
      content: "Socio Chat te asiste con criterio tecnico sobre el cliente activo.",
      skipBeacon: true,
      placement: "right",
    },
    {
      target: '[data-tour="sociochat-conversaciones"]',
      content: "Panel izquierdo con consultas recientes del cliente.",
      placement: "right",
    },
    {
      target: '[data-tour="sociochat-chat"]',
      content: "Aqui ves respuestas, fuentes y nivel de confianza.",
      placement: "left",
    },
    {
      target: '[data-tour="sociochat-input"]',
      content: "Escribe consultas tecnicas y usa prompts rapidos cuando convenga.",
      placement: "top",
    },
    {
      target: '[data-tour="sociochat-referencias"]',
      content: "Referencias tecnicas usadas por la ultima respuesta.",
      placement: "left",
    },
  ],
  "client-memory": [
    {
      target: '[data-tour="sidebar-client-memory"]',
      content: "Client Memory guarda contexto historico del cliente.",
      skipBeacon: true,
      placement: "right",
    },
    {
      target: '[data-tour="memory-title"]',
      content: "Resumen maestro del expediente del cliente.",
      placement: "bottom",
    },
    {
      target: '[data-tour="memory-perfil"]',
      content: "Perfil operativo para mantener referencia de industria y marco.",
      placement: "bottom",
    },
    {
      target: '[data-tour="memory-documentos"]',
      content: "Sube y revisa documentos para soporte y contexto del encargo.",
      placement: "top",
    },
    {
      target: '[data-tour="memory-hallazgos"]',
      content: "Historial de hallazgos para reutilizar aprendizaje por cliente.",
      placement: "left",
    },
  ],
};
