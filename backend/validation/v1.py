from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError

VALID_SCHEMA_VERSION = "v1"


@dataclass
class ValidationFailure:
    message: str
    errors: list[str]


class PerfilClienteBlock(BaseModel):
    nombre_legal: str = ""
    sector: str = ""


class PerfilEncargoBlock(BaseModel):
    anio_activo: int | str | None = None
    marco_referencial: str = ""
    fase_actual: str = "planificacion"


class PerfilMaterialidadFinal(BaseModel):
    materialidad_planeacion: float | None = None
    materialidad_ejecucion: float | None = None
    umbral_trivialidad: float | None = None


class PerfilMaterialidadBlock(BaseModel):
    estado_materialidad: str = "preliminar"
    final: PerfilMaterialidadFinal = Field(default_factory=PerfilMaterialidadFinal)


class PerfilRiesgoBlock(BaseModel):
    nivel: str = "medio"


class PerfilCuestionarioBlock(BaseModel):
    nomina: bool = False
    inventarios: bool = False
    ingresos_complejos: bool = False
    partes_relacionadas: bool = False
    multi_moneda: bool = False


class PerfilV1(BaseModel):
    schema_version: Literal["v1"] = "v1"
    cliente: PerfilClienteBlock = Field(default_factory=PerfilClienteBlock)
    encargo: PerfilEncargoBlock = Field(default_factory=PerfilEncargoBlock)
    materialidad: PerfilMaterialidadBlock = Field(default_factory=PerfilMaterialidadBlock)
    riesgo_global: PerfilRiesgoBlock = Field(default_factory=PerfilRiesgoBlock)
    cuestionario_auditoria: PerfilCuestionarioBlock = Field(default_factory=PerfilCuestionarioBlock)


class AfirmacionCoverage(BaseModel):
    nombre: str
    covered: bool = False
    evidencia: str = ""


class AreaV1(BaseModel):
    schema_version: Literal["v1"] = "v1"
    codigo: str
    nombre: str
    estado_area: Literal["pendiente", "en_proceso", "en_ejecucion", "concluida"] = "pendiente"
    riesgo: Literal["bajo", "medio", "alto", "critico"] = "medio"
    afirmaciones_criticas: list[str] = Field(default_factory=list)
    afirmaciones_coverage: list[AfirmacionCoverage] = Field(default_factory=list)
    procedimientos: list[dict[str, Any]] = Field(default_factory=list)
    hallazgos_abiertos: list[dict[str, Any]] = Field(default_factory=list)
    conclusion: str = ""
    revision_checks: dict[str, bool] = Field(default_factory=dict)


class WorkflowGateState(BaseModel):
    code: str
    status: Literal["ok", "blocked"]
    detail: str = ""


class WorkflowTransition(BaseModel):
    at: str
    from_phase: str
    to_phase: str
    user_id: str = ""


class WorkflowV1(BaseModel):
    schema_version: Literal["v1"] = "v1"
    cliente_id: str
    phase: Literal["planificacion", "ejecucion", "informe"] = "planificacion"
    gates: list[WorkflowGateState] = Field(default_factory=list)
    transitions: list[WorkflowTransition] = Field(default_factory=list)


class WorkpaperTaskV1(BaseModel):
    id: str
    area_code: str
    area_name: str
    title: str
    nia_ref: str = ""
    prioridad: Literal["baja", "media", "alta", "critica"] = "media"
    required: bool = True
    done: bool = False
    evidence_note: str = ""


class WorkpapersV1(BaseModel):
    schema_version: Literal["v1"] = "v1"
    cliente_id: str
    tasks: list[WorkpaperTaskV1] = Field(default_factory=list)


def _fase_normalizada(raw: str) -> str:
    value = (raw or "").strip().lower()
    if "inform" in value or "cier" in value:
        return "informe"
    if "ejec" in value or "visita" in value:
        return "ejecucion"
    return "planificacion"


def normalize_perfil_doc_v1(doc: dict[str, Any]) -> dict[str, Any]:
    data = dict(doc or {})
    data["schema_version"] = VALID_SCHEMA_VERSION
    if not isinstance(data.get("cliente"), dict):
        data["cliente"] = {}
    if not isinstance(data.get("encargo"), dict):
        data["encargo"] = {}
    if not isinstance(data.get("materialidad"), dict):
        data["materialidad"] = {}
    if not isinstance(data.get("riesgo_global"), dict):
        data["riesgo_global"] = {}
    if not isinstance(data.get("cuestionario_auditoria"), dict):
        data["cuestionario_auditoria"] = {}
    # Backward compatibility: perfiles legacy pueden venir sin nivel de riesgo.
    if not str(data["riesgo_global"].get("nivel") or "").strip():
        data["riesgo_global"]["nivel"] = "medio"
    data["encargo"]["fase_actual"] = _fase_normalizada(str(data["encargo"].get("fase_actual", "")))
    return data


def normalize_area_doc_v1(doc: dict[str, Any], *, area_code: str) -> dict[str, Any]:
    data = dict(doc or {})
    data["schema_version"] = VALID_SCHEMA_VERSION
    data["codigo"] = str(data.get("codigo") or area_code)
    data["nombre"] = str(data.get("nombre") or f"Área {area_code}")
    estado = str(data.get("estado_area") or "pendiente").strip().lower()
    if estado not in {"pendiente", "en_proceso", "en_ejecucion", "concluida"}:
        estado = "pendiente"
    data["estado_area"] = estado

    riesgo = str(data.get("riesgo") or "medio").strip().lower()
    if riesgo not in {"bajo", "medio", "alto", "critico"}:
        riesgo = "medio"
    data["riesgo"] = riesgo
    for key, default in [
        ("afirmaciones_criticas", []),
        ("afirmaciones_coverage", []),
        ("procedimientos", []),
        ("hallazgos_abiertos", []),
        ("conclusion", ""),
        ("revision_checks", {}),
    ]:
        if not isinstance(data.get(key), type(default)):
            data[key] = default
    return data


def normalize_workflow_doc_v1(doc: dict[str, Any], *, cliente_id: str, phase: str) -> dict[str, Any]:
    data = dict(doc or {})
    data["schema_version"] = VALID_SCHEMA_VERSION
    data["cliente_id"] = str(data.get("cliente_id") or cliente_id)
    data["phase"] = _fase_normalizada(str(data.get("phase") or phase))
    if not isinstance(data.get("gates"), list):
        data["gates"] = []
    if not isinstance(data.get("transitions"), list):
        data["transitions"] = []
    return data


def normalize_workpapers_doc_v1(doc: dict[str, Any], *, cliente_id: str) -> dict[str, Any]:
    data = dict(doc or {})
    data["schema_version"] = VALID_SCHEMA_VERSION
    data["cliente_id"] = str(data.get("cliente_id") or cliente_id)
    tasks = data.get("tasks")
    data["tasks"] = tasks if isinstance(tasks, list) else []
    normalized_tasks: list[dict[str, Any]] = []
    for task in data["tasks"]:
        if not isinstance(task, dict):
            continue
        row = dict(task)
        prioridad = str(row.get("prioridad") or "media").strip().lower()
        if prioridad not in {"baja", "media", "alta", "critica"}:
            prioridad = "media"
        row["prioridad"] = prioridad
        normalized_tasks.append(row)
    data["tasks"] = normalized_tasks
    return data


def _format_validation_errors(exc: ValidationError) -> list[str]:
    out: list[str] = []
    for err in exc.errors():
        loc = ".".join([str(x) for x in err.get("loc", [])])
        msg = str(err.get("msg", "error"))
        out.append(f"{loc}: {msg}" if loc else msg)
    return out


def validate_perfil_doc_v1(doc: dict[str, Any]) -> tuple[bool, list[str]]:
    normalized = normalize_perfil_doc_v1(doc)
    errors: list[str] = []
    try:
        PerfilV1(**normalized)
    except ValidationError as exc:
        errors.extend(_format_validation_errors(exc))

    cliente = normalized.get("cliente", {})
    encargo = normalized.get("encargo", {})
    materialidad = normalized.get("materialidad", {})
    riesgo = normalized.get("riesgo_global", {})

    if not str(cliente.get("nombre_legal") or "").strip():
        errors.append("cliente.nombre_legal es obligatorio")
    if not str(cliente.get("sector") or "").strip():
        errors.append("cliente.sector es obligatorio")
    if not str(encargo.get("anio_activo") or "").strip():
        errors.append("encargo.anio_activo es obligatorio")
    if not str(encargo.get("marco_referencial") or "").strip():
        errors.append("encargo.marco_referencial es obligatorio")
    if not str(riesgo.get("nivel") or "").strip():
        errors.append("riesgo_global.nivel es obligatorio")

    estado_mat = str(materialidad.get("estado_materialidad") or "").strip().lower()
    final = materialidad.get("final", {}) if isinstance(materialidad.get("final"), dict) else {}
    if estado_mat == "final":
        if float(final.get("materialidad_planeacion") or 0) <= 0:
            errors.append("materialidad.final.materialidad_planeacion debe ser > 0 cuando estado_materialidad=final")
        if float(final.get("materialidad_ejecucion") or 0) <= 0:
            errors.append("materialidad.final.materialidad_ejecucion debe ser > 0 cuando estado_materialidad=final")
        if float(final.get("umbral_trivialidad") or 0) <= 0:
            errors.append("materialidad.final.umbral_trivialidad debe ser > 0 cuando estado_materialidad=final")
    return len(errors) == 0, errors


def validate_area_doc_v1(doc: dict[str, Any], *, area_code: str) -> tuple[bool, list[str]]:
    normalized = normalize_area_doc_v1(doc, area_code=area_code)
    errors: list[str] = []
    try:
        AreaV1(**normalized)
    except ValidationError as exc:
        errors.extend(_format_validation_errors(exc))
    if not str(normalized.get("codigo") or "").strip():
        errors.append("codigo es obligatorio")
    if not str(normalized.get("nombre") or "").strip():
        errors.append("nombre es obligatorio")
    return len(errors) == 0, errors


def validate_workflow_doc_v1(doc: dict[str, Any], *, cliente_id: str, phase: str) -> tuple[bool, list[str]]:
    normalized = normalize_workflow_doc_v1(doc, cliente_id=cliente_id, phase=phase)
    try:
        WorkflowV1(**normalized)
        return True, []
    except ValidationError as exc:
        return False, _format_validation_errors(exc)


def validate_workpapers_doc_v1(doc: dict[str, Any], *, cliente_id: str) -> tuple[bool, list[str]]:
    normalized = normalize_workpapers_doc_v1(doc, cliente_id=cliente_id)
    try:
        WorkpapersV1(**normalized)
        return True, []
    except ValidationError as exc:
        return False, _format_validation_errors(exc)
