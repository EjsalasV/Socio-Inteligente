from __future__ import annotations

import logging
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from backend.auth import authorize_cliente_access, get_current_user
from backend.repositories.file_repository import append_audit_log
from backend.schemas import ApiResponse, UserContext
from backend.services.entry_validator_service import (
    ValidationContext,
    validate_entry,
    EntryValidationResponse,
)

LOGGER = logging.getLogger("socio_ai.audit_validator")

router = APIRouter(prefix="/api/audit", tags=["audit-validator"])


class AuditEntryRequest(BaseModel):
    """Solicitud de validación de asiento contra normativa auditora"""
    
    # Datos del asiento
    cuenta: str = Field(..., description="Código de cuenta, ej: 2205, 1310")
    debito: float = Field(0.0, ge=0, description="Monto en débito")
    credito: float = Field(0.0, ge=0, description="Monto en crédito")
    descripcion: str = Field("", description="Descripción del asiento")
    
    # Contexto de auditoría
    framework: Literal["NIIF_PYMES", "NIIF_FULL", "holdings"] = Field(
        "NIIF_PYMES",
        description="Marco normativo aplicable",
    )
    area: str = Field(
        "cartera_cxc",
        description="Área de auditoría: cartera_cxc, ppe, provisiones, intercompany, etc.",
    )
    cliente_id: str = Field(..., description="Identificador del cliente/empresa")
    
    # Datos de riesgo específicos (varían por área)
    antigüedad_dias: int = Field(
        0,
        ge=0,
        description="Para CxC: Días desde fecha de vencimiento de factura",
    )
    monto_original: float = Field(
        0.0,
        ge=0,
        description="Para provisiones: Monto original de estimación",
    )
    tiene_soporte_documental: bool = Field(
        False,
        description="¿Existe comprobante/factura/contrato de soporte?",
    )
    cliente_en_riesgo: bool = Field(
        False,
        description="¿Cliente está en lista de riesgos crediticios o legales?",
    )
    tiene_garantia: bool = Field(
        False,
        description="¿Existe garantía sobre el activo/pasivo?",
    )
    garantia_ejecutable: bool = Field(
        False,
        description="¿La garantía es real y ejecutable (libre de gravámenes)?",
    )
    
    # Contexto de empresa
    es_holding: bool = Field(
        False,
        description="¿La empresa es holding (inversiones en filiales)?",
    )
    tiene_partes_relacionadas: bool = Field(
        False,
        description="¿Hay transacciones con partes relacionadas?",
    )


    holdings_entities: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Estructura de entidades holdings para analisis de cascada",
    )
    ownership_links: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Relaciones owner -> subsidiary con porcentaje",
    )
    declared_dividends: dict[str, float] = Field(
        default_factory=dict,
        description="Dividendos declarados por entidad (entity_id -> monto)",
    )
    tax_rates: dict[str, float] = Field(
        default_factory=dict,
        description="Tasas fiscales por jurisdiccion (jurisdiccion -> tasa)",
    )
    offset_allowed: bool = Field(
        False,
        description="Si existe acuerdo formal para offset de dividendos/deudas",
    )
    offset_dividend_receivable: float = Field(
        0.0,
        ge=0,
        description="Monto de dividendo por cobrar (para validar offset)",
    )
    offset_cxp_payable: float = Field(
        0.0,
        ge=0,
        description="Monto de CxP a accionista/relacionada (para validar offset)",
    )
class AuditValidationResult(BaseModel):
    """Respuesta completa de validación de asiento"""
    
    # Veredicto
    valido: bool = Field(..., description="¿El asiento es aceptable bajo normativa?")
    criterio_aplicado: str = Field(..., description="ID del criterio que se aplicó")
    
    # Contexto normativo
    framework: str
    norma: str
    area: str
    
    # Si FALLA validación
    razon: str | None = Field(None, description="Razón específica del rechazo")
    que_falta: list[str] = Field(default_factory=list, description="Evidencia faltante")
    como_corregir: list[str] = Field(default_factory=list, description="Pasos para corregir")
    
    # Si PASA pero con condiciones
    advertencias: list[str] = Field(
        default_factory=list,
        description="Cosas a tener cuidado o documentar",
    )
    que_documentar: list[str] = Field(
        default_factory=list,
        description="Evidencia que DEBE quedar en papeles de trabajo",
    )
    
    # Normativa aplicable
    nias_aplicables: list[str] = Field(
        default_factory=list,
        description="NIAs relevantes para este criterio",
    )
    
    # Educación: Trampa a evitar
    trampa_evitar: str | None = Field(None, description="ID de trampa común evitada")
    trampa_detalle: str | None = Field(
        None,
        description="Detalles de la trampa: caso real, criterio auditor senior",
    )
    
    # Materialidad
    materialidad: str | None = Field(None, description="Consideración de materialidad")
    afirmaciones_impactadas: list[str] = Field(
        default_factory=list,
        description="Afirmaciones de auditoría impactadas (existencia, valuación, etc.)",
    )


@router.post(
    "/validate-entry",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Validar asiento contra criterios de auditoría",
    description="Valida un asiento contable contra los criterios de auditoría del framework normativo. Retorna veredicto normativo + educación sobre trampas comunes.",
)
def post_validate_entry(
    request: Request,
    payload: AuditEntryRequest,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    """
    Valida un asiento contable contra criterios de auditoría específicos del framework.
    
    **Ejemplo de uso:**
    
    ```json
    {
        "cuenta": "2205",
        "debito": 0,
        "credito": 100000,
        "descripcion": "Compensación CxP Subsidiaria con VPP",
        "framework": "NIIF_PYMES",
        "area": "cartera_cxc",
        "cliente_id": "holding_xcorp",
        "antigüedad_dias": 400,
        "cliente_en_riesgo": false,
        "tiene_soporte_documental": false
    }
    ```
    
    **Respuesta si FALLA:**
    
    ```json
    {
        "status": "ok",
        "data": {
            "valido": false,
            "criterio_aplicado": "CXC-002-VENCIDA",
            "razon": "Cartera >365 días sin provisión",
            "que_falta": [
                "❌ Requiere provisión por deterioro (Antigüedad: 400 días)"
            ],
            "como_corregir": [
                "RECHAZAR: Requiere provisión por deterioro",
                "Solicitar plan de pago escrito del cliente",
                "Calcular ECL basado en probabilidad de cobro real"
            ],
            "nias_aplicables": ["NIA 500", "NIA 315"],
            "trampa_evitar": "TRAMPA-002",
            "trampa_detalle": "TRAMPA: Confundir CORRIENTE con SIN RIESGO..."
        }
    }
    ```
    
    **Respuesta si PASA pero con condiciones:**
    
    ```json
    {
        "status": "ok",
        "data": {
            "valido": true,
            "criterio_aplicado": "CXC-001-CORRIENTE",
            "advertencias": [
                "⚠️ Revisar: Aplicación consistente a toda cartera"
            ],
            "que_documentar": [
                "Tasa futura usada EN LA PROVISIÓN",
                "Ratios de cobranza histórica (últimos 3 años)"
            ],
            "nias_aplicables": ["NIA 500", "NIA 580"]
        }
    }
    ```
    """
    
    try:
        # Autorizar acceso del usuario al cliente
        authorize_cliente_access(user, payload.cliente_id)
    except HTTPException as e:
        LOGGER.warning(
            f"Unauthorized audit validation: user={user.sub}, cliente={payload.cliente_id}",
        )
        raise e
    
    try:
        # Construir contexto de validación
        context = ValidationContext(
            cliente_id=payload.cliente_id,
            framework=payload.framework,
            area=payload.area,
            cuenta=payload.cuenta,
            debito=payload.debito,
            credito=payload.credito,
            descripcion=payload.descripcion,
            antigüedad_dias=payload.antigüedad_dias,
            monto_original=payload.monto_original,
            tiene_soporte_documental=payload.tiene_soporte_documental,
            cliente_en_riesgo=payload.cliente_en_riesgo,
            tiene_garantia=payload.tiene_garantia,
            garantia_ejecutable=payload.garantia_ejecutable,
            es_holding=payload.es_holding,
            tiene_partes_relacionadas=payload.tiene_partes_relacionadas,
            holdings_entities=payload.holdings_entities,
            ownership_links=payload.ownership_links,
            declared_dividends=payload.declared_dividends,
            tax_rates=payload.tax_rates,
            offset_allowed=payload.offset_allowed,
            offset_dividend_receivable=payload.offset_dividend_receivable,
            offset_cxp_payable=payload.offset_cxp_payable,
        )
        
        # Ejecutar validación
        validation_result: EntryValidationResponse = validate_entry(context)
        
        # Convertir a resultado para API
        result = AuditValidationResult(**validation_result.model_dump())
        
        # Registrar en audit log
        append_audit_log(
            payload.cliente_id,
            {
                "tipo": "audit_validation",
                "usuario": user.sub,
                "framework": payload.framework,
                "area": payload.area,
                "cuenta": payload.cuenta,
                "resultado": "valido" if result.valido else "rechazado",
                "criterio": result.criterio_aplicado,
            },
        )
        
        LOGGER.info(
            f"Entry validation: cliente={payload.cliente_id}, "
            f"area={payload.area}, resultado={result.valido}",
        )
        
        return ApiResponse(data=result.model_dump())
    
    except FileNotFoundError as e:
        # Programa de auditoría no existe para ese framework/área
        LOGGER.error(f"Audit program not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Programa de auditoría no disponible: {payload.framework}/{payload.area}",
        )
    
    except Exception as e:
        LOGGER.exception(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al validar asiento",
        )


@router.get(
    "/frameworks",
    response_model=ApiResponse,
    summary="Listar frameworks disponibles",
)
def get_available_frameworks(
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    """
    Retorna lista de frameworks disponibles para validación.
    
    Respuesta:
    ```json
    {
        "status": "ok",
        "data": {
            "frameworks": ["NIIF_PYMES", "NIIF_FULL", "holdings"]
        }
    }
    ```
    """
    from pathlib import Path
    
    audit_prog_path = (
        Path(__file__).resolve().parents[2] / "backend" / "audit_programs"
    )
    
    frameworks = []
    if audit_prog_path.exists():
        frameworks = [d.name for d in audit_prog_path.iterdir() if d.is_dir()]
    
    return ApiResponse(
        data={
            "frameworks": sorted(frameworks),
            "total": len(frameworks),
        },
    )


@router.get(
    "/areas/{framework}",
    response_model=ApiResponse,
    summary="Listar áreas disponibles para un framework",
)
def get_available_areas(
    framework: str,
    user: UserContext = Depends(get_current_user),
) -> ApiResponse:
    """
    Retorna lista de áreas de auditoría disponibles para un framework.
    
    Ejemplo: GET /api/audit/areas/NIIF_PYMES
    
    Respuesta:
    ```json
    {
        "status": "ok",
        "data": {
            "framework": "NIIF_PYMES",
            "areas": ["cartera_cxc", "ppe", "provisiones"]
        }
    }
    ```
    """
    from pathlib import Path
    
    audit_prog_path = (
        Path(__file__).resolve().parents[2] / "backend" / "audit_programs"
    )
    framework_path = audit_prog_path / framework.lower()
    
    if not framework_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Framework not found: {framework}",
        )
    
    areas = []
    for yml_file in framework_path.glob("*.yml"):
        areas.append(yml_file.stem)
    
    return ApiResponse(
        data={
            "framework": framework,
            "areas": sorted(areas),
            "total": len(areas),
        },
    )
