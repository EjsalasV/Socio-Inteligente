"""
Route para análisis de cascada de holdings

Endpoint: POST /api/audit/holdings-cascade/analyze
Analiza estructuras multi-nivel de tenencia accionaria y calcula
flujos de dividendos, detección de ciclos, y riesgos de consolidación.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from backend.auth import get_current_user
from backend.schemas import ApiResponse, UserContext
from backend.services.holdings_cascade_service import (
    HoldingEntity,
    OwnershipLink,
    analyze_holdings_cascade,
)

LOGGER = logging.getLogger("socio_ai.holdings_cascade")

router = APIRouter(prefix="/api/audit", tags=["holdings-cascade"])


class HoldingEntityRequest(BaseModel):
    """Entidad en estructura de holdings"""

    entity_id: str = Field(..., description="Identificador único, ej: 'parent', 'subsidiary_a'")
    name: str = Field(..., description="Nombre comercial de la entidad")
    ownership_type: str = Field(
        "subsidiary",
        description="Type: 'parent', 'subsidiary', 'joint_venture'",
    )
    tax_jurisdiction: str = Field(
        ..., description="País de residencia fiscal, ej: 'COL', 'MEX', 'ESP'"
    )
    balance: float = Field(
        0.0, description="Saldo de CxC/CxP con otros holdings (negativo = CxP)"
    )


class OwnershipLinkRequest(BaseModel):
    """Relación de propiedad entre entidades"""

    owner_id: str = Field(..., description="Entidad que posee")
    subsidiary_id: str = Field(..., description="Entidad que es poseída")
    ownership_percentage: float = Field(
        ..., ge=0, le=100, description="% de tenencia, 0-100"
    )
    voting_rights: float = Field(
        100.0, ge=0, le=100, description="% de derechos de voto (puede diferir)"
    )
    direct_control: bool = Field(
        True, description="¿Es tenencia directa o a través de otra?"
    )


class HoldingsCascadeAnalysisRequest(BaseModel):
    """Solicitud para análisis de cascada de holdings"""

    entities: list[HoldingEntityRequest] = Field(
        ..., description="Lista de entidades en la estructura"
    )
    ownership_links: list[OwnershipLinkRequest] = Field(
        ..., description="Relaciones de propiedad"
    )
    declared_dividends: dict[str, float] = Field(
        default_factory=dict,
        description="entity_id → monto dividendo declarado",
    )
    tax_rates: dict[str, float] = Field(
        ..., description="country_code → tasa impositiva (0.0-1.0)"
    )
    cliente_id: str = Field(..., description="Identificador del cliente/empresa")


@router.post(
    "/holdings-cascade/analyze",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
)
async def analyze_holdings_cascade_endpoint(
    request: HoldingsCascadeAnalysisRequest,
    current_user: UserContext = None,  # User context could be added via depend
) -> ApiResponse:
    """
    Analiza cascada de dividendos en estructura multi-nivel de holdings.

    Calcula:
    - Flujos de dividendos en cascada con ajustes impositivos
    - Detección de ciclos en estructura de propiedad (A→B→A)
    - Eliminaciones en consolidado
    - Riesgos: ciclos, arbitraje fiscal, complejidad, offsets sin acuerdo

    Ejemplo de caso: Parent (60%) → Subsidiary A (80%) → Subsidiary B ($100 dividendo)
    - Subsidiary A recibe: 80% × $100 - impuesto = $68
    - Parent recibe: 60% × $68 - impuesto = $40.8
    - Consolidado elimina: $100 inter-company

    Returns:
        {
            "status": "success",
            "data": {
                "parent_entity": "parent",
                "total_entities": 3,
                "has_cycles": false,
                "cascades": [...],
                "eliminations": [...],
                "risks_identified": [...]
            }
        }
    """

    try:
        # Convertir requests a domain objects
        entities = [
            HoldingEntity(
                entity_id=e.entity_id,
                name=e.name,
                ownership_type=e.ownership_type,
                tax_jurisdiction=e.tax_jurisdiction,
                balance=e.balance,
            )
            for e in request.entities
        ]

        ownership_links = [
            OwnershipLink(
                owner_id=ol.owner_id,
                subsidiary_id=ol.subsidiary_id,
                ownership_percentage=ol.ownership_percentage,
                voting_rights=ol.voting_rights,
                direct_control=ol.direct_control,
            )
            for ol in request.ownership_links
        ]

        # Ejecutar análisis
        analysis = analyze_holdings_cascade(
            entities=entities,
            ownership_links=ownership_links,
            declared_dividends=request.declared_dividends,
            tax_rates=request.tax_rates,
        )

        LOGGER.info(
            f"Holdings cascade analysis completed for {request.cliente_id}: "
            f"{analysis.total_entities} entities, cycles={analysis.has_cycles}"
        )

        return ApiResponse(
            status="success",
            data={
                "parent_entity": analysis.parent_entity,
                "total_entities": analysis.total_entities,
                "total_ownership_links": analysis.total_ownership_links,
                "has_cycles": analysis.has_cycles,
                "cycles_detected": analysis.cycles_detected,
                "cascades": [
                    {
                        "declaring_entity": c.declaring_entity,
                        "dividend_amount": c.dividend_amount,
                        "recipient_entity": c.recipient_entity,
                        "ownership_percentage": c.ownership_percentage,
                        "tax_rate": c.tax_rate,
                        "received_amount": c.received_amount,
                        "consolidation_elimination": c.consolidation_elimination,
                    }
                    for c in analysis.cascades
                ],
                "eliminations": [
                    {
                        "elimination_type": e.elimination_type,
                        "amount": e.amount,
                        "debit_account": e.debit_account,
                        "credit_account": e.credit_account,
                        "reason": e.reason,
                    }
                    for e in analysis.eliminations
                ],
                "risks_identified": analysis.risks_identified,
            },
        )

    except ValueError as e:
        LOGGER.error(f"Validation error in holdings cascade: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid holdings structure: {str(e)}",
        )
    except Exception as e:
        LOGGER.error(f"Error analyzing holdings cascade: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error analyzing holdings structure",
        )
