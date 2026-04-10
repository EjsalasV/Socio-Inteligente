from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


class ApiMeta(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApiResponse(BaseModel):
    status: Literal["ok", "error"] = "ok"
    data: Any
    meta: ApiMeta = Field(default_factory=ApiMeta)


class ApiError(BaseModel):
    status: Literal["error"] = "error"
    code: str
    message: str
    action_hint: str = ""
    retryable: bool = False
    details: dict[str, Any] | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    csrf_token: str = ""


class UserContext(BaseModel):
    sub: str
    org_id: str
    allowed_clientes: list[str]
    role: str
    user_id: str = ""
    display_name: str = ""


class AuthMeResponse(BaseModel):
    sub: str
    user_id: str = ""
    display_name: str = ""
    role: str
    org_id: str
    allowed_clientes: list[str] = Field(default_factory=list)


class ClienteSummary(BaseModel):
    cliente_id: str
    nombre: str
    sector: str | None = None


class ClienteCreateRequest(BaseModel):
    cliente_id: str | None = None
    nombre: str
    sector: str | None = None


class ClienteProfile(BaseModel):
    cliente_id: str
    perfil: dict[str, Any]


class BalanceKPIs(BaseModel):
    activo: float = Field(0.0, description="Total activos")
    pasivo: float = Field(0.0, description="Total pasivos")
    patrimonio: float = Field(0.0, description="Patrimonio neto")
    ingresos: float = Field(0.0, description="Ingresos del periodo")
    gastos: float = Field(0.0, description="Gastos del periodo")


class ProgresoEncargo(BaseModel):
    pct_completado: int = Field(0, ge=0, le=100)
    areas_completas: int = 0
    areas_en_proceso: int = 0
    areas_no_iniciadas: int = 0
    total_areas: int = 0


class AreaRiesgo(BaseModel):
    codigo: str
    nombre: str
    score_riesgo: float
    prioridad: str
    saldo_total: float
    con_saldo: bool


class DashboardWorkflowGate(BaseModel):
    code: str
    title: str
    status: Literal["ok", "blocked"]
    detail: str


class DashboardMaterialidadDetalle(BaseModel):
    nia_base: str = "NIA 320"
    base_usada: str = ""
    base_valor: float = 0.0
    porcentaje_aplicado: float = 0.0
    porcentaje_rango_min: float = 0.0
    porcentaje_rango_max: float = 0.0
    criterio_seleccion_pct: str = ""
    origen_regla: str = ""
    minimum_threshold_aplicado: float = 0.0
    minimum_threshold_origen: str = ""


class DashboardResponse(BaseModel):
    cliente_id: str
    nombre_cliente: str
    periodo: str
    sector: str
    riesgo_global: str
    balance: BalanceKPIs
    progreso: ProgresoEncargo
    top_areas: list[AreaRiesgo]
    materialidad_global: float = 0.0
    materialidad_ejecucion: float = 0.0
    umbral_trivial: float = 0.0
    materialidad_origen: str = ""
    tb_stage: str = "sin_saldos"
    fase_actual: str = ""
    workflow_phase: str = "planificacion"
    workflow_gates: list[DashboardWorkflowGate] = Field(default_factory=list)
    balance_status: Literal["cuadrado", "resultado_periodo", "descuadrado"] = "cuadrado"
    resultado_periodo: float = 0.0
    balance_delta: float = 0.0
    materialidad_detalle: DashboardMaterialidadDetalle = Field(default_factory=DashboardMaterialidadDetalle)
    top_areas_page: int = 1
    top_areas_page_size: int = 8
    top_areas_total: int = 0
    top_areas_has_more: bool = False


class RiskItem(BaseModel):
    area: str
    score: float
    nivel: str


class RiskMatrixCell(BaseModel):
    row: int
    col: int
    frecuencia: int
    impacto: int
    score: float
    nivel: str
    area_id: str | None = None
    area_nombre: str | None = None


class RiskCriticalArea(BaseModel):
    area_id: str
    area_nombre: str
    score: float
    nivel: str
    frecuencia: int
    impacto: int
    hallazgos_abiertos: int
    drivers: list[str] = Field(default_factory=list)
    score_components: dict[str, float] = Field(default_factory=dict)


class RiskStrategyTest(BaseModel):
    test_id: str
    test_type: Literal["control", "sustantiva"]
    area_id: str
    area_nombre: str
    nia_ref: str
    title: str
    description: str
    where_to_execute: Literal["workpapers"] = "workpapers"
    priority: Literal["alta", "media", "baja"] = "media"
    workpaper_linkable: bool = True


class RiskStrategyResponse(BaseModel):
    approach: str
    control_pct: int = Field(ge=0, le=100)
    substantive_pct: int = Field(ge=0, le=100)
    rationale: str
    control_tests: list[RiskStrategyTest] = Field(default_factory=list)
    substantive_tests: list[RiskStrategyTest] = Field(default_factory=list)


class RiskEngineResponse(BaseModel):
    cliente_id: str
    eje_x: str = "Impacto"
    eje_y: str = "Frecuencia"
    quadrants: list[list[RiskMatrixCell]]
    areas_criticas: list[RiskCriticalArea]
    strategy: RiskStrategyResponse
    recommended_tests: list[RiskStrategyTest] = Field(default_factory=list)


class AreaResponse(BaseModel):
    cliente_id: str
    area_ls: str
    data: dict[str, Any]


class AreaLeadRow(BaseModel):
    cuenta: str
    nombre: str
    actual: float
    anterior: float
    variacion_monto: float
    variacion_pct: float
    nivel: int = 2


class AreaRisk(BaseModel):
    nivel: str
    titulo: str
    descripcion: str


class AreaAseveracion(BaseModel):
    nombre: str
    descripcion: str
    riesgo_tipico: str
    procedimiento_clave: str


class AreaSaldos(BaseModel):
    actual_year: str
    previous_year: str
    actual_total: float
    previous_total: float


class AreaVariaciones(BaseModel):
    monto: float
    porcentaje: float


class AreaDetailResponse(BaseModel):
    cliente_id: str
    area_ls: str
    area_name: str
    saldos: AreaSaldos
    variaciones: AreaVariaciones
    riesgos: list[AreaRisk]
    aseveraciones: list[AreaAseveracion]
    lead_schedule: list[AreaLeadRow]


class AreaEncabezado(BaseModel):
    area_code: str
    nombre: str
    responsable: str
    estatus: str
    actual_year: str
    anterior_year: str


class AreaCuentaItem(BaseModel):
    codigo: str
    nombre: str
    saldo_actual: float
    saldo_anterior: float
    nivel: int = 2
    checked: bool = False


class AreaWorkspaceResponse(BaseModel):
    encabezado: AreaEncabezado
    cuentas: list[AreaCuentaItem]
    aseveraciones: list[AreaAseveracion]
    briefing_context: dict[str, Any] = Field(default_factory=dict)


class AreaConclusionRequest(BaseModel):
    conclusion: str


class AreaCheckRequest(BaseModel):
    checked: bool


class ChatRequest(BaseModel):
    message: str


class BriefingAreaRequest(BaseModel):
    cliente_id: str
    area_codigo: str
    area_nombre: str
    marco: str
    riesgo: str
    afirmaciones_criticas: list[str] = Field(default_factory=list)
    materialidad: float = 0.0
    patrones_historicos: list[str] = Field(default_factory=list)
    hallazgos_previos: list[str] = Field(default_factory=list)
    etapa: str = "ejecucion"


class BriefingChunkUsed(BaseModel):
    norma: str
    fuente: str
    excerpt: str


class TraceabilityItem(BaseModel):
    norma: str
    fuente_chunk: str
    chunk_id: str
    area_codigo: str
    paper_id: str | None = None
    timestamp: str


class BriefingAreaResponse(BaseModel):
    area_codigo: str
    area_nombre: str
    briefing: str
    normas_activadas: list[str] = Field(default_factory=list)
    chunks_usados: list[BriefingChunkUsed] = Field(default_factory=list)
    trazabilidad: list[TraceabilityItem] = Field(default_factory=list)
    generado_en: str


class HallazgoEstructurarRequest(BaseModel):
    cliente_id: str
    area_codigo: str
    area_nombre: str
    marco: str
    riesgo: str
    afirmaciones_criticas: list[str] = Field(default_factory=list)
    etapa: str = "ejecucion"
    condicion_detectada: str
    monto_estimado: float | None = None
    causa_preliminar: str = ""
    efecto_preliminar: str = ""
    guardar_en_hallazgos: bool = False


class HallazgoEstructurarResponse(BaseModel):
    area_codigo: str
    area_nombre: str
    hallazgo: str
    normas_activadas: list[str] = Field(default_factory=list)
    chunks_usados: list[BriefingChunkUsed] = Field(default_factory=list)
    trazabilidad: list[TraceabilityItem] = Field(default_factory=list)
    generado_en: str


class BriefingTiempoLogRequest(BaseModel):
    cliente_id: str
    area_codigo: str
    area_nombre: str
    tiempo_manual_min: float = 0.0
    tiempo_ai_min: float = 0.0
    notas: str = ""


class BriefingTiempoLogResponse(BaseModel):
    saved: bool = True
    delta_min: float = 0.0
    ahorro_pct: float = 0.0


class UserPreferencesResponse(BaseModel):
    learning_role: str = "semi"
    tour_completed_modules: list[str] = Field(default_factory=list)
    tour_welcome_seen: bool = False
    onboarding_ui: dict[str, Any] = Field(default_factory=dict)
    preferences_version: str = "v1.2.1"


class UserPreferencesPatchRequest(BaseModel):
    learning_role: str | None = None
    tour_completed_modules: list[str] | None = None
    tour_welcome_seen: bool | None = None
    onboarding_ui: dict[str, Any] | None = None
    preferences_version: str | None = None


class AdminUserSummary(BaseModel):
    user_id: str
    username: str
    display_name: str
    role: str
    active: bool = True
    cliente_ids: list[str] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class AdminUserCreateRequest(BaseModel):
    username: str
    password: str
    role: str = "auditor"
    display_name: str = ""
    active: bool = True
    cliente_ids: list[str] = Field(default_factory=list)


class AdminUserPatchRequest(BaseModel):
    display_name: str | None = None
    role: str | None = None
    active: bool | None = None
    password: str | None = None


class AdminUserAssignClientesRequest(BaseModel):
    cliente_ids: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    cliente_id: str
    answer: str
    context_sources: list[str]
    citations: list[dict[str, str]] = Field(default_factory=list)
    confidence: float = 0.0
    prompt_id: str = ""
    prompt_version: str = ""
    mode_used: str = "chat"


class MetodoRequest(BaseModel):
    area: str


class MetodoResponse(BaseModel):
    cliente_id: str
    area: str
    explanation: str
    context_sources: list[str]
    citations: list[dict[str, str]] = Field(default_factory=list)
    confidence: float = 0.0
    prompt_id: str = ""
    prompt_version: str = ""


class PdfSummaryResponse(BaseModel):
    cliente_id: str
    report_name: str
    generated_at: datetime
    path: str
    file_hash: str = ""
    size_bytes: int = 0


class ReportMemoResponse(BaseModel):
    cliente_id: str
    memo: str
    generated_at: datetime
    source: str = "motor"


class InternalControlLetterRequest(BaseModel):
    recipient: str = "Gerencia General"
    include_management_response: bool = True
    max_findings: int = Field(10, ge=1, le=25)


class GenerationMetadata(BaseModel):
    source: Literal["llm", "fallback"] = "fallback"
    provider: str = "fallback"
    model: str = ""
    prompt_id: str = ""
    prompt_version: str = ""
    document_type: str = ""
    template_mode: Literal["custom", "default", "fallback"] = "fallback"
    template_version: str = "v1-default"
    placeholders_supported: list[str] = Field(default_factory=list)
    required_sections: list[str] = Field(default_factory=list)
    optional_sections: list[str] = Field(default_factory=list)
    generated_at: datetime
    requested_by: str = ""
    input_payload: dict[str, Any] = Field(default_factory=dict)


class GeneratedArtifact(BaseModel):
    artifact_type: Literal["markdown", "docx"] = "markdown"
    artifact_path: str
    artifact_hash: str
    template_version: str = "v1-default"
    size_bytes: int = 0


class InternalControlLetterResponse(BaseModel):
    cliente_id: str
    generated_at: datetime
    recipient: str
    findings_count: int
    source: str = "fallback"
    document_version: int = 1
    supersedes_version: int | None = None
    is_current: bool = True
    state: Literal["draft", "reviewed", "approved", "issued"] = "draft"
    diff_from_previous: dict[str, Any] = Field(default_factory=dict)
    document: dict[str, Any] = Field(default_factory=dict)
    generation_metadata: GenerationMetadata
    artifacts: list[GeneratedArtifact] = Field(default_factory=list)
    content: str
    path: str = ""


class NIIFPymesDraftRequest(BaseModel):
    ifrs_for_smes_version: Literal["2015", "2025"] = "2025"
    early_adoption: bool = False
    include_policy_section: bool = True


class NIIFPymesDraftResponse(BaseModel):
    cliente_id: str
    generated_at: datetime
    period_end: str
    ifrs_for_smes_version: str
    early_adoption: bool
    source: str = "fallback"
    document_version: int = 1
    supersedes_version: int | None = None
    is_current: bool = True
    state: Literal["draft", "reviewed", "approved", "issued"] = "draft"
    diff_from_previous: dict[str, Any] = Field(default_factory=dict)
    document: dict[str, Any] = Field(default_factory=dict)
    generation_metadata: GenerationMetadata
    artifacts: list[GeneratedArtifact] = Field(default_factory=list)
    content: str
    path: str = ""


class ReportStatusResponse(BaseModel):
    cliente_id: str
    gates: list["QualityGateItem"] = Field(default_factory=list)
    missing_sections: list[str] = Field(default_factory=list)
    can_emit_draft: bool = True
    can_emit_final: bool = False
    coverage_summary: "CoverageSummary" = Field(default_factory=lambda: CoverageSummary())


class ClienteDocumento(BaseModel):
    id: str
    name: str
    kind: str
    uploaded_at: datetime
    path: str


class WorkflowAdvanceRequest(BaseModel):
    target_phase: str | None = None


class WorkflowStateResponse(BaseModel):
    cliente_id: str
    previous_phase: str
    current_phase: str
    changed: bool
    gates: list["QualityGateItem"]


class WorkflowFieldHistoryRequest(BaseModel):
    phase: str
    field: str
    old_value: Any = None
    new_value: Any = None


class WorkpaperTask(BaseModel):
    id: str
    area_code: str
    area_name: str
    title: str
    nia_ref: str
    prioridad: str
    required: bool = True
    done: bool = False
    evidence_note: str = ""


class WorkpaperTaskUpdateRequest(BaseModel):
    done: bool
    evidence_note: str = ""


class WorkpaperTaskCreateRequest(BaseModel):
    area_code: str
    area_name: str
    title: str
    nia_ref: str = ""
    prioridad: str = "media"
    required: bool = True
    evidence_note: str = ""


class QualityGateItem(BaseModel):
    code: str
    title: str
    status: Literal["ok", "blocked"]
    detail: str


class CoverageSummary(BaseModel):
    total_assertions: int = 0
    covered_assertions: int = 0
    coverage_pct: float = 0.0
    missing_by_area: dict[str, list[str]] = Field(default_factory=dict)


class WorkpaperPlanResponse(BaseModel):
    cliente_id: str
    tasks: list[WorkpaperTask]
    gates: list[QualityGateItem]
    completion_pct: float
    coverage_summary: CoverageSummary = Field(default_factory=CoverageSummary)
    tasks_page: int = 1
    tasks_page_size: int = 0
    tasks_total: int = 0
    tasks_total_all: int = 0
    tasks_has_more: bool = False
