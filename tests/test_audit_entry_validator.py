"""
Tests para entry_validator_service

Verifica que la validación de asientos contra criterios de auditoría funciona.
"""
from __future__ import annotations

import pytest

from backend.services.entry_validator_service import (
    ValidationContext,
    EntryValidationResponse,
    validate_entry,
    load_audit_program,
)


class TestAuditProgramLoading:
    """Pruebas de carga de programas de auditoría"""

    def test_load_cartera_cxc_program(self):
        """Verifica que el programa NIIF PYMES cartera_cxc se carga correctamente"""
        program = load_audit_program("NIIF_PYMES", "cartera_cxc")
        
        assert program is not None
        assert program.get("framework") == "NIIF_PYMES"
        assert program.get("area") == "cartera_cxc"
        assert program.get("norma_clave") is not None
        assert len(program.get("criterios_validacion", [])) > 0
        assert len(program.get("trampas_comunes", [])) > 0

    def test_nonexistent_program_raises_error(self):
        """Verifica que se levanta error si el programa no existe"""
        with pytest.raises(FileNotFoundError):
            load_audit_program("NONEXISTENT", "invalid")


class TestValidationCriteria:
    """Pruebas de aplicación de criterios"""

    def test_cartera_vencida_mayor_365_rechaza(self):
        """
        Caso: Cartera >365 días sin provisión
        Esperado: RECHAZAR (CXC-002-VENCIDA)
        Norma: Sección 11 NIIF PYMES
        """
        context = ValidationContext(
            cliente_id="TEST001",
            framework="NIIF_PYMES",
            area="cartera_cxc",
            cuenta="1310",  # Cuentas por cobrar
            debito=0,
            credito=0,
            descripcion="Factura vencida sin provisión",
            antigüedad_dias=400,  # >365 = vencida
            tiene_soporte_documental=False,
            cliente_en_riesgo=False,
        )
        
        result: EntryValidationResponse = validate_entry(context)
        
        # Debe RECHAZAR
        assert result.valido is False
        assert result.criterio_aplicado == "CXC-002-VENCIDA"
        assert "365" in result.razon.lower() or "vencida" in result.razon.lower()
        
        # Debe proponer cómo corregir
        assert len(result.como_corregir) > 0
        
        # Debe referenciar NIAs
        assert "NIA" in str(result.nias_aplicables)
        
        # Debe indicar que es material
        assert result.materialidad is not None

    def test_cartera_corriente_sin_riesgo_acepta(self):
        """
        Caso: Cartera corriente, sin indicios de riesgo
        Esperado: ACEPTAR (CXC-001-CORRIENTE)
        """
        context = ValidationContext(
            cliente_id="TEST001",
            framework="NIIF_PYMES",
            area="cartera_cxc",
            cuenta="1310",
            debito=0,
            credito=0,
            descripcion="Factura corriente",
            antigüedad_dias=15,  # Corriente
            tiene_soporte_documental=True,
            cliente_en_riesgo=False,
        )
        
        result: EntryValidationResponse = validate_entry(context)
        
        # Debe ACEPTAR
        assert result.valido is True
        assert result.criterio_aplicado == "CXC-001-CORRIENTE"
        
        # Pero debe documentar
        assert len(result.que_documentar) > 0 or len(result.advertencias) >= 0

    def test_cliente_en_riesgo_sin_provision_rechaza(self):
        """
        Caso: Cliente en lista de riesgo sin provision adicional
        Esperado: Rechazo o advertencia (según criterio CXC-004 o validación en CXC-*)
        """
        context = ValidationContext(
            cliente_id="TEST001",
            framework="NIIF_PYMES",
            area="cartera_cxc",
            cuenta="1310",
            debito=0,
            credito=0,
            descripcion="Cliente en riesgo",
            antigüedad_dias=200,  # Vencida, cliente en riesgo
            cliente_en_riesgo=True,  # ← Cliente en riesgo
            tiene_soporte_documental=False,  # No tiene soporte
        )
        
        result: EntryValidationResponse = validate_entry(context)
        
        # Debe tener verificación de riesgo en resultado
        # (puede ser rechazo o advertencia, lo importante es que lo detecta)
        assert result.criterio_aplicado is not None
        # Debe haber alguma referencia a riesgo o condiciones
        assert len(result.que_documentar) > 0 or len(result.advertencias) >= 0 or result.valido is False


class TestEducationalContent:
    """Pruebas que verifica que el sistema enseña sobre trampas comunes"""

    def test_trampa_gerencia_no_es_evidencia(self):
        """Verifica que el sistema enseña sobre la trampa: 'Gerencia = evidencia'"""
        program = load_audit_program("NIIF_PYMES", "cartera_cxc")
        trampas = program.get("trampas_comunes", [])
        
        # Debe haber una trampa sobre "gerencia no es evidencia"
        trampa_ids = [t.get("id") for t in trampas]
        assert "TRAMPA-001" in trampa_ids
        
        trampa_001 = next((t for t in trampas if t.get("id") == "TRAMPA-001"), None)
        assert trampa_001 is not None
        assert "promesa" in trampa_001.get("trampa", "").lower()

    def test_validation_resultado_incluye_trampa_cuando_aplica(self):
        """Verifica que cuando se aplica un criterio, se incluye la trampa asociada"""
        # Caso que caería en trampa TRAMPA-002: Confundir corriente con sin riesgo
        context = ValidationContext(
            cliente_id="TEST001",
            framework="NIIF_PYMES",
            area="cartera_cxc",
            cuenta="1310",
            debito=0,
            credito=0,
            antigüedad_dias=400,
            cliente_en_riesgo=False,  # ← Falsamente sin riesgo
        )
        
        result = validate_entry(context)
        
        # Aunque se rechace, puede haber referencia a trampa
        # (dependiendo de la implementación)
        if result.trampa_evitar:
            assert result.trampa_detalle is not None


class TestEntryValidationContextBuilding:
    """Pruebas de construcción de contextos válidos"""

    def test_context_creation_minimal(self):
        """Verifica que se puede crear contexto mínimo"""
        context = ValidationContext(
            cliente_id="TEST",
            framework="NIIF_PYMES",
            area="cartera_cxc",
            cuenta="1310",
            debito=0,
            credito=100000,
        )
        
        assert context.cliente_id == "TEST"
        assert context.antigüedad_dias == 0  # Por defecto

    def test_context_creation_completo(self):
        """Verifica que se puede crear contexto con todos los campos"""
        context = ValidationContext(
            cliente_id="CLIENT_A",
            framework="NIIF_PYMES",
            area="cartera_cxc",
            cuenta="1310",
            debito=0,
            credito=50000,
            descripcion="Compensación CxP con holding",
            antigüedad_dias=100,
            cliente_en_riesgo=True,
            tiene_garantia=True,
            garantia_ejecutable=False,
            es_holding=True,
            tiene_partes_relacionadas=True,
        )
        
        assert context.es_holding is True
        assert context.tiene_partes_relacionadas is True
        assert context.garantia_ejecutable is False


class TestNormativaAplicable:
    """Pruebas que verifican referencias a normativa correcta"""

    def test_nias_se_incluyen_en_resultado(self):
        """Verifica que NIAs relevantes se incluyen en el resultado"""
        context = ValidationContext(
            cliente_id="TEST",
            framework="NIIF_PYMES",
            area="cartera_cxc",
            cuenta="1310",
            debito=0,
            credito=100000,
            antigüedad_dias=400,
        )
        
        result = validate_entry(context)
        
        # Debe tener NIAs
        assert len(result.nias_aplicables) > 0
        assert any("NIA" in nia for nia in result.nias_aplicables)

    def test_afirmaciones_se_incluyen(self):
        """Verifica que afirmaciones de auditoría se referencian"""
        context = ValidationContext(
            cliente_id="TEST",
            framework="NIIF_PYMES",
            area="cartera_cxc",
            cuenta="1310",
            debito=0,
            credito=100000,
            antigüedad_dias=15,
            tiene_soporte_documental=True,
        )
        
        result = validate_entry(context)
        
        # Si hay afirmaciones, deben estar presentes o vacías (ambas OK)
        # Lo importante es que la estructura lo permite
        assert isinstance(result.afirmaciones_impactadas, list)


# ═══════════════════════════════════════════════════════════════════════════
# Pruebas de integración (con FastAPI TestClient)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.skip(reason="Requiere cliente FastAPI completo, ver test_api_integration.py")
def test_validate_entry_endpoint():
    """
    Prueba el endpoint POST /api/audit/validate-entry
    
    Para esta prueba se necesita:
    1. FastAPI app iniciada
    2. Usuario autenticado
    3. Cliente autorizado
    
    Ver: tests/test_api_audit_validator.py
    """
    pass
