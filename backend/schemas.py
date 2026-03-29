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
    details: dict[str, Any] | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class UserContext(BaseModel):
    sub: str
    org_id: str
    allowed_clientes: list[str]
    role: str


class ClienteSummary(BaseModel):
    cliente_id: str
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
    fase_actual: str = ""


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


class RiskEngineResponse(BaseModel):
    cliente_id: str
    eje_x: str = "Impacto"
    eje_y: str = "Frecuencia"
    quadrants: list[list[RiskMatrixCell]]
    areas_criticas: list[RiskCriticalArea]


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


class AreaConclusionRequest(BaseModel):
    conclusion: str


class AreaCheckRequest(BaseModel):
    checked: bool


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    cliente_id: str
    answer: str
    context_sources: list[str]


class MetodoRequest(BaseModel):
    area: str


class MetodoResponse(BaseModel):
    cliente_id: str
    area: str
    explanation: str
    context_sources: list[str]


class PdfSummaryResponse(BaseModel):
    cliente_id: str
    report_name: str
    generated_at: datetime
    path: str
