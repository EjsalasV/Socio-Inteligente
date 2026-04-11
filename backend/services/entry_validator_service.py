from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
AUDIT_PROGRAMS_PATH = ROOT / "backend" / "audit_programs"


class EntryValidationCriteria(BaseModel):
    """Representa un criterio de validación de asiento"""
    id: str
    regla: str
    es_permitido: Literal["true", "false", "conditional"]
    descripcion: str = ""
    cuando_aplica: list[str] = Field(default_factory=list)
    condiciones_aceptacion: list[str] = Field(default_factory=list)
    condiciones_rechazo: list[str] = Field(default_factory=list)
    que_validar: list[str] = Field(default_factory=list)
    que_pedir: list[str] = Field(default_factory=list)
    nias: list[str] = Field(default_factory=list)
    trampa_asociada: str | None = None


class TrapaComun(BaseModel):
    """Representa una trampa auditora común"""
    id: str
    trampa: str
    es_peligrosa: bool
    nia_violada: str
    caso_real: str
    criterio_socio: str | None = None


class EntryValidationResponse(BaseModel):
    """Respuesta de validación de asiento contra normativa"""
    valido: bool
    criterio_aplicado: str  # ID del criterio (ej: CXC-002-VENCIDA)
    razon: str | None = None
    
    # Contexto normativo
    framework: str
    norma: str
    area: str
    
    # Si es RECHAZADO:
    que_falta: list[str] = Field(default_factory=list)
    como_corregir: list[str] = Field(default_factory=list)
    nias_aplicables: list[str] = Field(default_factory=list)
    
    # Si es ACEPTADO con condiciones:
    advertencias: list[str] = Field(default_factory=list)
    que_documentar: list[str] = Field(default_factory=list)
    
    # Referencias a trampas para educación:
    trampa_evitar: str | None = None
    trampa_detalle: str | None = None
    
    # Insights adicionales
    materialidad: str | None = None
    afirmaciones_impactadas: list[str] = Field(default_factory=list)


@dataclass
class ValidationContext:
    """Contexto para validar un asiento"""
    cliente_id: str
    framework: str  # "NIIF_PYMES", "NIIF_FULL"
    area: str  # "cartera_cxc", "ppe", "provisiones"
    
    # Datos de la transacción
    cuenta: str
    debito: float
    credito: float
    descripcion: str = ""
    
    # Contexto de riesgo (specific a cada área)
    antigüedad_dias: int = 0  # Para CxC
    monto_original: float = 0.0  # Para provisiones
    tiene_soporte_documental: bool = False
    cliente_en_riesgo: bool = False
    tiene_garantia: bool = False
    garantia_ejecutable: bool = False
    
    # Contexto empresa
    es_holding: bool = False
    tiene_partes_relacionadas: bool = False


def load_audit_program(framework: str, area: str) -> dict[str, Any]:
    """
    Carga el YAML de criterios para un framework + área.
    
    Args:
        framework: "NIIF_PYMES", "NIIF_FULL", "holdings"
        area: "cartera_cxc", "ppe", "provisiones", "intercompany"
    
    Returns:
        Dict con estructura del programa
    
    Raises:
        FileNotFoundError si no existe el programa
    """
    program_path = AUDIT_PROGRAMS_PATH / framework.lower() / f"{area}.yml"
    
    if not program_path.exists():
        raise FileNotFoundError(
            f"Audit program not found: {program_path}. "
            f"Available frameworks: {list(AUDIT_PROGRAMS_PATH.iterdir())}"
        )
    
    with open(program_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _extract_trampas(program: dict[str, Any]) -> dict[str, TrapaComun]:
    """Extrae las trampas comunes del programa para referencias educativas"""
    trampas = {}
    for trampa_data in program.get("trampas_comunes", []):
        trampa = TrapaComun(**trampa_data)
        trampas[trampa.id] = trampa
    return trampas


def _applies_to_entry(
    criterion: dict[str, Any],
    context: ValidationContext,
) -> bool:
    """
    Evalúa si un criterio aplica a este asiento específico.
    
    Lógica:
    - CXC-001 (corriente): Aplica si es CxC y < 31 días vencimiento
    - CXC-002 (vencida): Aplica si es CxC y > 365 días vencimiento
    - CXC-003 (provision): Aplica si hay provisión registrada
    - CXC-004 (cliente riesgo): Aplica si cliente está en riesgo
    """
    criterion_id = criterion.get("id", "")
    
    # Verificar si es cuenta de CxC (comienzan con 13, 1305, 1310, etc)
    es_cxc = context.cuenta.startswith("13")
    
    if "CXC" not in criterion_id:
        return True  # Aplica genéricamente
    
    if not es_cxc:
        return False  # Criterio CxC no aplica si no es cuenta de CxC
    
    # Lógica específica por criterio de CxC (ORDEN IMPORTA: de más crítico a menos)
    
    # PRIMERO: Verificar crítico - Cliente en riesgo
    if criterion_id == "CXC-004-CLIENTE-RIESGO":
        return context.cliente_en_riesgo
    
    # SEGUNDO: Verificar vencida mayor a 365
    if criterion_id == "CXC-002-VENCIDA":
        return context.antigüedad_dias > 365
    
    # TERCERO: Verificar corriente (0-31 días)
    if criterion_id == "CXC-001-CORRIENTE":
        return 0 <= context.antigüedad_dias <= 31
    
    # CUARTO: Verificar provisión insuficiente (>180, lo que incluiría >365)
    if criterion_id == "CXC-005-PROVISION-INSUFICIENTE":
        return context.antigüedad_dias > 180
    
    # QUINTO: Provision por porcentaje (genérica)
    if criterion_id == "CXC-003-PROVISION-PORCENTAJE":
        # Aplica a cualquier CxC con antigüedad > 0
        return context.antigüedad_dias >= 0
    
    return True


def _check_conditions(
    criterion: dict[str, Any],
    context: ValidationContext,
) -> dict[str, Any]:
    """
    Verifica si se cumplen las condiciones para aceptar un criterio 'conditional'.
    
    Returns:
        {"ok": bool, "missing": list[str], "warnings": list[str]}
    """
    missing = []
    warnings = []
    
    # Validar condiciones de RECHAZO
    for rechazo in criterion.get("condiciones_rechazo", []):
        
        if "lista de riesgo" in rechazo.lower():
            if context.cliente_en_riesgo:
                missing.append(f"❌ {rechazo} (Cliente ID: {context.cliente_id} está en riesgo)")
        
        if "sin soporte" in rechazo.lower():
            if not context.tiene_soporte_documental:
                missing.append(f"❌ {rechazo} (No hay comprobante/factura)")
        
        if ">365" in rechazo or "mayor 365" in rechazo.lower():
            if context.antigüedad_dias > 365:
                missing.append(f"❌ {rechazo} (Antigüedad: {context.antigüedad_dias} días)")
        
        if "selectiva" in rechazo.lower():
            # Esta es una validación que requeriría más contexto
            # Por ahora ser conservador
            warnings.append(f"⚠️ Verificar: {rechazo}")
    
    # Validar condiciones de ACEPTACIÓN
    aceptacion_gaps = []
    for aceptacion in criterion.get("condiciones_aceptacion", []):
        
        if "100% últimos 24" in aceptacion or "historial cobranza" in aceptacion.lower():
            if context.antigüedad_dias > 730:  # 2 años
                aceptacion_gaps.append(f"⚠️ Revisar: {aceptacion} (Cliente tiene saldos muy antiguos)")
        
        if "NO en lista" in aceptacion or "no en riesgo" in aceptacion.lower():
            if context.cliente_en_riesgo:
                missing.append(f"❌ {aceptacion}")
    
    return {
        "ok": len(missing) == 0,
        "missing": missing,
        "warnings": warnings + aceptacion_gaps,
    }


def validate_entry(context: ValidationContext) -> EntryValidationResponse:
    """
    Valida un asiento contra los criterios de auditoría del framework.
    
    Args:
        context: Contexto completo de la validación
    
    Returns:
        EntryValidationResponse con veredicto y detalles
    
    Raises:
        FileNotFoundError si el programa de auditoría no existe
    """
    
    # 1. Cargar criterios del programa
    program = load_audit_program(context.framework, context.area)
    trampas_map = _extract_trampas(program)
    
    # 2. Evaluar CADA criterio en orden de importancia
    for criterion in program.get("criterios_validacion", []):
        criterion_id = criterion.get("id", "")
        applies = _applies_to_entry(criterion, context)
        
        # Solo evaluar si aplica al tipo de asiento
        if not applies:
            continue
        
        es_permitido = criterion.get("es_permitido", "true")
        
        # ▼ CASO 1: RECHAZAR SIEMPRE (es_permitido = false)
        if es_permitido is False or es_permitido == "false":
            trampa_id = criterion.get("trampa_asociada")
            trampa_detalle = None
            if trampa_id and trampa_id in trampas_map:
                trampa = trampas_map[trampa_id]
                trampa_detalle = f"TRAMPA: {trampa.trampa}\nCaso real: {trampa.caso_real}"
            
            return EntryValidationResponse(
                valido=False,
                criterio_aplicado=criterion_id,
                razon=criterion.get("regla", ""),
                framework=context.framework,
                norma=program.get("norma_clave", ""),
                area=context.area,
                que_falta=criterion.get("que_pedir", []),
                como_corregir=criterion.get("que_hacer", []),
                nias_aplicables=criterion.get("nias", []),
                trampa_evitar=criterion.get("trampa_asociada"),
                trampa_detalle=trampa_detalle,
                materialidad=criterion.get("materialidad", "Material"),
            )
        
        # ▼ CASO 2: CONDICIONAL - Verificar condiciones
        elif es_permitido is True or es_permitido == "true" or es_permitido == "conditional":
            conditions = _check_conditions(criterion, context)
            
            if not conditions["ok"]:
                # Falló condiciones de aceptación
                trampa_id = criterion.get("trampa_asociada")
                trampa_detalle = None
                if trampa_id and trampa_id in trampas_map:
                    trampa = trampas_map[trampa_id]
                    trampa_detalle = f"TRAMPA: {trampa.trampa}\nCaso real: {trampa.caso_real}"
                
                return EntryValidationResponse(
                    valido=False,
                    criterio_aplicado=criterion_id,
                    razon=criterion.get("regla", ""),
                    framework=context.framework,
                    norma=program.get("norma_clave", ""),
                    area=context.area,
                    que_falta=conditions["missing"],
                    como_corregir=criterion.get("que_hacer", []),
                    nias_aplicables=criterion.get("nias", []),
                    trampa_evitar=criterion.get("trampa_asociada"),
                    trampa_detalle=trampa_detalle,
                )
            else:
                # Pasó condiciones, pero documentar avisos
                return EntryValidationResponse(
                    valido=True,
                    criterio_aplicado=criterion_id,
                    razon=criterion.get("regla", ""),
                    framework=context.framework,
                    norma=program.get("norma_clave", ""),
                    area=context.area,
                    advertencias=conditions["warnings"],
                    que_documentar=criterion.get("que_documentar", []),
                    nias_aplicables=criterion.get("nias", []),
                    afirmaciones_impactadas=program.get("afirmaciones_auditoria", {}).keys() or [],
                )
    
    # 3. Si pasó TODOS los criterios aplicables, es válido genéricamente
    return EntryValidationResponse(
        valido=True,
        criterio_aplicado="GENERIC_PASS",
        framework=context.framework,
        norma=program.get("norma_clave", ""),
        area=context.area,
        nias_aplicables=program.get("nias_generales", []),
        que_documentar=["Aplicado criterio genérico auditoría"],
    )


def explain_framework_difference(
    transaccion: str,
    framework1: str = "NIIF_FULL",
    framework2: str = "NIIF_PYMES",
) -> dict[str, Any]:
    """
    Explica diferencias entre frameworks para misma transacción.
    
    Ejemplo: ¿Cómo se audita intangible indefinido en NIIF FULL vs PYMES?
    
    Returns:
        {
            "transaccion": "Intangible con vida indefinida",
            "framework1": {"permitido": False, "razon": "..."},
            "framework2": {"permitido": True, "razon": "..."}
        }
    """
    # Esto se complementaría con una tabla de equivalencias
    # Por ahora es stub para futuro
    return {
        "transaccion": transaccion,
        "nota": "Consulta implementable cuando se tengan ambos programas",
    }
