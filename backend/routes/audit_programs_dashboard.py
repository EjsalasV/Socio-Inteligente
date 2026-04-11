"""
API Routes for Audit Programs Discovery & Dashboard

Endpoints:
- GET /api/audit-programs/frameworks - List all available frameworks
- GET /api/audit-programs/summary - Overall system summary
- GET /api/audit-programs/{framework}/{area} - Detailed area program info
- GET /api/audit-programs/{framework} - All programs for framework
"""

from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/audit-programs", tags=["audit-programs"])

ROOT = Path(__file__).resolve().parents[2]
AUDIT_PROGRAMS_PATH = ROOT / "backend" / "audit_programs"


class CriterionSummary(BaseModel):
    """Resumen de un criterio de validación"""
    id: str
    regla: str
    es_permitido: str
    descripcion: str


class TrappaSummary(BaseModel):
    """Resumen de una trampa educativa"""
    id: str
    trampa: str
    es_peligrosa: bool = True


class AuditProgramSummary(BaseModel):
    """Resumen de un programa de auditoría"""
    framework: str
    area: str
    norma_clave: str
    criterios_count: int
    trampas_count: int
    nias: list[str] = Field(default_factory=list)
    afirmaciones: list[str] = Field(default_factory=list)


class FrameworkOverview(BaseModel):
    """Visión general de un framework"""
    framework: str
    total_areas: int
    total_criteria: int
    total_trappas: int
    areas: list[dict] = Field(default_factory=list)


class SystemSummary(BaseModel):
    """Resumen completo del sistema de auditoría"""
    total_frameworks: int
    total_areas: int
    total_criteria: int
    total_trappas: int
    frameworks: list[dict] = Field(default_factory=list)


def _load_program(framework: str, area: str) -> dict:
    """Load audit program from YAML"""
    program_path = AUDIT_PROGRAMS_PATH / framework.lower() / f"{area}.yml"
    
    if not program_path.exists():
        raise HTTPException(status_code=404, detail=f"Program not found: {framework}/{area}")
    
    with open(program_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@router.get("/frameworks", response_model=list[str])
def list_frameworks() -> list[str]:
    """
    List all available audit frameworks
    
    Example response:
    ["NIIF_PYMES", "NIIF_FULL", "holdings"]
    """
    frameworks = set()
    
    if AUDIT_PROGRAMS_PATH.exists():
        for framework_dir in AUDIT_PROGRAMS_PATH.iterdir():
            if framework_dir.is_dir():
                frameworks.add(framework_dir.name)
    
    return sorted(list(frameworks))


@router.get("/{framework}/areas", response_model=list[str])
def list_areas(framework: str) -> list[str]:
    """
    Listar todas las áreas de auditoría disponibles en un framework
    
    Example: GET /api/audit-programs/NIIF_PYMES/areas
    Response: ["cartera_cxc", "ppe", "provisiones", "holdings_intercompany", "ingresos"]
    """
    framework_path = AUDIT_PROGRAMS_PATH / framework.lower()
    
    if not framework_path.exists():
        raise HTTPException(status_code=404, detail=f"Framework not found: {framework}")
    
    areas = []
    for yml_file in framework_path.glob("*.yml"):
        areas.append(yml_file.stem)
    
    return sorted(areas)


@router.get("/{framework}/summary", response_model=FrameworkOverview)
def get_framework_summary(framework: str) -> FrameworkOverview:
    """
    Get comprehensive summary for a framework
    
    Includes:
    - Total criteria count
    - Total trampas count
    - Area-by-area breakdown
    """
    framework_path = AUDIT_PROGRAMS_PATH / framework.lower()
    
    if not framework_path.exists():
        raise HTTPException(status_code=404, detail=f"Framework not found: {framework}")
    
    total_criteria = 0
    total_trappas = 0
    areas_info = []
    
    for yml_file in sorted(framework_path.glob("*.yml")):
        with open(yml_file, encoding="utf-8") as f:
            program = yaml.safe_load(f) or {}
            
            area_criteria = len(program.get("criterios_validacion", []))
            area_trappas = len(program.get("trampas_comunes", []))
            total_criteria += area_criteria
            total_trappas += area_trappas
            
            areas_info.append({
                "area": yml_file.stem,
                "norma": program.get("norma_clave", "").split("-")[0].strip(),
                "criteria_count": area_criteria,
                "trappas_count": area_trappas,
                "nias": program.get("nias", []),
            })
    
    return FrameworkOverview(
        framework=framework,
        total_areas=len(areas_info),
        total_criteria=total_criteria,
        total_trappas=total_trappas,
        areas=areas_info,
    )


@router.get("/summary", response_model=SystemSummary)
def get_system_summary() -> SystemSummary:
    """
    Get overall system summary
    
    Shows:
    - Total frameworks, areas, criteria, trappas
    - Framework-level breakdown
    """
    total_criteria = 0
    total_trappas = 0
    frameworks_info = []
    
    for framework_dir in sorted(AUDIT_PROGRAMS_PATH.iterdir()):
        if not framework_dir.is_dir():
            continue
        
        framework = framework_dir.name
        framework_criteria = 0
        framework_trappas = 0
        areas_count = 0
        
        for yml_file in framework_dir.glob("*.yml"):
            areas_count += 1
            with open(yml_file, encoding="utf-8") as f:
                program = yaml.safe_load(f) or {}
                c = len(program.get("criterios_validacion", []))
                t = len(program.get("trampas_comunes", []))
                framework_criteria += c
                framework_trappas += t
        
        total_criteria += framework_criteria
        total_trappas += framework_trappas
        
        frameworks_info.append({
            "framework": framework,
            "areas_count": areas_count,
            "criteria_count": framework_criteria,
            "trappas_count": framework_trappas,
        })
    
    return SystemSummary(
        total_frameworks=len(frameworks_info),
        total_areas=sum(f["areas_count"] for f in frameworks_info),
        total_criteria=total_criteria,
        total_trappas=total_trappas,
        frameworks=frameworks_info,
    )


@router.get("/{framework}/{area}/criteria", response_model=list[CriterionSummary])
def get_area_criteria(framework: str, area: str) -> list[CriterionSummary]:
    """
    Get all criteria for a specific audit area
    
    Example: GET /api/audit-programs/NIIF_PYMES/cartera_cxc/criteria
    """
    program = _load_program(framework, area)
    
    criteria = []
    for crit_data in program.get("criterios_validacion", []):
        criteria.append(
            CriterionSummary(
                id=crit_data.get("id", ""),
                regla=crit_data.get("regla", ""),
                es_permitido=crit_data.get("es_permitido", "false"),
                descripcion=crit_data.get("descripcion", ""),
            )
        )
    
    return criteria


@router.get("/{framework}/{area}/trampas", response_model=list[TrappaSummary])
def get_area_trappas(framework: str, area: str) -> list[TrappaSummary]:
    """
    Get all educational trappas for a specific audit area
    
    Example: GET /api/audit-programs/NIIF_PYMES/cartera_cxc/trampas
    """
    program = _load_program(framework, area)
    
    trappas = []
    for trampa_data in program.get("trampas_comunes", []):
        trappas.append(
            TrappaSummary(
                id=trampa_data.get("id", ""),
                trampa=trampa_data.get("trampa", ""),
                es_peligrosa=trampa_data.get("es_peligrosa", True),
            )
        )
    
    return trappas


@router.get("/{framework}/{area}", response_model=AuditProgramSummary)
def get_program_summary(framework: str, area: str) -> AuditProgramSummary:
    """
    Get full summary for an audit program
    
    Example: GET /api/audit-programs/NIIF_PYMES/cartera_cxc
    """
    program = _load_program(framework, area)
    
    return AuditProgramSummary(
        framework=program.get("framework", framework),
        area=program.get("area", area),
        norma_clave=program.get("norma_clave", ""),
        criterios_count=len(program.get("criterios_validacion", [])),
        trampas_count=len(program.get("trampas_comunes", [])),
        nias=program.get("nias", []),
        afirmaciones=program.get("afirmaciones", []),
    )
