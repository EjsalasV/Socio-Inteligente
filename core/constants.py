"""
Constantes globales de SocioAI.
Punto único de verdad para valores fijos del sistema.
"""
from __future__ import annotations

# ── Versión ──────────────────────────────────────────────────
APP_NAME = "SocioAI"
APP_VERSION = "1.0.0"

# ── Etapas de auditoría ──────────────────────────────────────
ETAPAS_VALIDAS = {"planificacion", "ejecucion", "cierre"}
ETAPA_DEFAULT = "planificacion"

# ── Niveles de riesgo ────────────────────────────────────────
NIVEL_ALTO = "alto"
NIVEL_MEDIO = "medio"
NIVEL_BAJO = "bajo"
NIVELES_VALIDOS = {NIVEL_ALTO, NIVEL_MEDIO, NIVEL_BAJO}

SCORE_RIESGO_ALTO = 70
SCORE_RIESGO_MEDIO = 40

# ── Estados de área ──────────────────────────────────────────
ESTADO_NO_INICIADA = "no_iniciada"
ESTADO_EN_REVISION = "en_revision"
ESTADO_PENDIENTE_CLIENTE = "pendiente_cliente"
ESTADO_LISTA_CIERRE = "lista_para_cierre"
ESTADO_CERRADA = "cerrada"
ESTADOS_AREA_VALIDOS = {
    ESTADO_NO_INICIADA,
    ESTADO_EN_REVISION,
    ESTADO_PENDIENTE_CLIENTE,
    ESTADO_LISTA_CIERRE,
    ESTADO_CERRADA,
}

# ── Estados de procedimientos ────────────────────────────────
PROC_EJECUTADO = "ejecutado"
PROC_COMPLETADO = "completado"
PROC_CERRADO = "cerrado"
PROC_EN_PROCESO = "en_proceso"
PROC_PLANIFICADO = "planificado"
PROC_PENDIENTE = "pendiente"
PROC_NO_APLICA = "no_aplicable"

ESTADOS_PROCEDIMIENTO_DONE = {
    PROC_EJECUTADO, PROC_COMPLETADO, PROC_CERRADO, PROC_NO_APLICA
}

# ── Decisiones de cierre ─────────────────────────────────────
DECISION_CERRAR = "cerrar"
DECISION_NO_CERRAR = "no_cerrar"
DECISION_REQUIERE_REVISION = "requiere_revision"

# ── Niveles de hallazgo ──────────────────────────────────────
HALLAZGO_ALTO = "alto"
HALLAZGO_MEDIO = "medio"
HALLAZGO_BAJO = "bajo"

# ── Materialidad (NIA 320) ───────────────────────────────────
FACTOR_DESEMPENO = 0.75
FACTOR_ERROR_TRIVIAL = 0.05

# ── Rutas base ───────────────────────────────────────────────
DATA_ROOT = "data"
CLIENTES_PATH = "data/clientes"
CATALOGOS_PATH = "data/catalogos"
EXPORTS_PATH = "data/exports"
LOGS_PATH = "logs"

# ── Encoding ─────────────────────────────────────────────────
DEFAULT_ENCODING = "utf-8"

# ── LLM ──────────────────────────────────────────────────────
LLM_PROVIDER_DEEPSEEK = "deepseek"
LLM_PROVIDER_OPENAI = "openai"
LLM_FALLBACK_MSG = "[Sin respuesta del modelo]"
