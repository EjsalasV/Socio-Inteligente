"""
Tests para Holdings Cascade Analysis Engine

Casos:
1. Simple cascade: Parent (60%) → Sub A (80%) → Sub B declara $100
2. Cycle detection: A owns B, B owns A
3. Multi-level cascade with tax adjustments
4. Offset validation
5. Risk identification
"""

import pytest
from backend.services.holdings_cascade_service import (
    HoldingEntity,
    OwnershipLink,
    analyze_holdings_cascade,
    validate_offset_agreement,
)


class TestSimpleDividendCascade:
    """Caso: Parent → Subsidiary A → Subsidiary B (declara dividendo)"""
    
    def test_simple_cascade_calculation(self):
        """Calcula dividendo en cascada con impuestos"""
        
        entities = [
            HoldingEntity(
                entity_id="parent",
                name="Parent Corp",
                ownership_type="parent",
                tax_jurisdiction="COL",
            ),
            HoldingEntity(
                entity_id="sub_a",
                name="Subsidiary A",
                ownership_type="subsidiary",
                tax_jurisdiction="MEX",
            ),
            HoldingEntity(
                entity_id="sub_b",
                name="Subsidiary B",
                ownership_type="subsidiary",
                tax_jurisdiction="ESP",
            ),
        ]
        
        ownership_links = [
            OwnershipLink(
                owner_id="parent",
                subsidiary_id="sub_a",
                ownership_percentage=60.0,
            ),
            OwnershipLink(
                owner_id="sub_a",
                subsidiary_id="sub_b",
                ownership_percentage=80.0,
            ),
        ]
        
        declared_dividends = {"sub_b": 100.0}
        tax_rates = {
            "COL": 0.10,  # Colombia 10%
            "MEX": 0.15,  # Mexico 15%
            "ESP": 0.20,  # Spain 20%
        }
        
        analysis = analyze_holdings_cascade(
            entities, ownership_links, declared_dividends, tax_rates
        )
        
        # Sub B declara 100, Sub A recibe 80% = 80
        assert len(analysis.cascades) >= 1
        sub_a_cascade = [c for c in analysis.cascades if c.recipient_entity == "sub_a"]
        assert len(sub_a_cascade) == 1
        assert sub_a_cascade[0].consolidation_elimination == 80.0  # 80% of 100
        assert sub_a_cascade[0].received_amount == 68.0  # 80 * (1 - 0.15 Mexican tax)
        
        # Sub A declara su parte (net), Parent recibe
        # Parent should receive cascade from Sub A if Sub A declares
        # (in this test we only declared Sub B)
    
    def test_consolidation_eliminations(self):
        """Elimina inter-company dividends en consolidado"""
        
        entities = [
            HoldingEntity("parent", "Parent", "parent", "COL"),
            HoldingEntity("sub_a", "Sub A", "subsidiary", "MEX"),
        ]
        
        ownership_links = [
            OwnershipLink(
                owner_id="parent",
                subsidiary_id="sub_a",
                ownership_percentage=100.0,
            ),
        ]
        
        declared_dividends = {"sub_a": 50.0}
        tax_rates = {"COL": 0.0, "MEX": 0.0}
        
        analysis = analyze_holdings_cascade(
            entities, ownership_links, declared_dividends, tax_rates
        )
        
        # Debe haber una eliminación por $50
        assert len(analysis.eliminations) > 0
        eliminations = [e for e in analysis.eliminations if e.amount == 50.0]
        assert len(eliminations) >= 1
        assert eliminations[0].elimination_type == "dividend_cascade"


class TestCycleDetection:
    """Detección de ciclos en ownership (A owns B, B owns A)"""
    
    def test_cycle_detection_simple(self):
        """Detecta ciclo simple: A → B → A"""
        
        entities = [
            HoldingEntity("entity_a", "Entity A", "subsidiary", "COL"),
            HoldingEntity("entity_b", "Entity B", "subsidiary", "MEX"),
        ]
        
        ownership_links = [
            OwnershipLink("entity_a", "entity_b", 50.0),
            OwnershipLink("entity_b", "entity_a", 50.0),  # Ciclo!
        ]
        
        declared_dividends = {}
        tax_rates = {}
        
        analysis = analyze_holdings_cascade(
            entities, ownership_links, declared_dividends, tax_rates
        )
        
        # Debe detectar ciclo
        assert analysis.has_cycles is True
        assert len(analysis.cycles_detected) > 0


class TestOffsetValidation:
    """Valida offset de dividendo contra obligación"""
    
    def test_offset_valid(self):
        """Offset válido cuando hay acuerdo documentado"""
        
        is_valid, reason = validate_offset_agreement(
            dividend_receivable=100.0,
            cxp_payable=100.0,
            offset_allowed=True,
        )
        
        assert is_valid is True
        assert "valid" in reason.lower()
    
    def test_offset_without_agreement(self):
        """Offset rechazado sin acuerdo"""
        
        is_valid, reason = validate_offset_agreement(
            dividend_receivable=100.0,
            cxp_payable=100.0,
            offset_allowed=False,
        )
        
        assert is_valid is False
        assert "agreement" in reason.lower()
    
    def test_offset_with_mismatched_amounts(self):
        """Offset rechazado cuando montos no coinciden"""
        
        is_valid, reason = validate_offset_agreement(
            dividend_receivable=100.0,
            cxp_payable=80.0,
            offset_allowed=True,
        )
        
        assert is_valid is False
        assert "don't match" in reason.lower()


class TestRiskIdentification:
    """Identifica riesgos en estructura"""
    
    def test_identifies_tax_arbitrage_risk(self):
        """Identifica alta carga fiscal en recipient"""
        
        entities = [
            HoldingEntity("parent", "Parent", "parent", "ESP", balance=0),  # High tax recipient
            HoldingEntity("sub", "Sub", "subsidiary", "COL", balance=0),
        ]
        
        ownership_links = [
            OwnershipLink("parent", "sub", 50.0),
        ]
        
        declared_dividends = {"sub": 100.0}
        tax_rates = {
            "COL": 0.05,
            "ESP": 0.40,  # 40% tax en España - recipient has high tax
        }
        
        analysis = analyze_holdings_cascade(
            entities, ownership_links, declared_dividends, tax_rates
        )
        
        # Debe identificar alto impuesto
        tax_risks = [r for r in analysis.risks_identified if "alto" in r.lower()]
        assert len(tax_risks) > 0
    
    def test_identifies_offset_without_agreement_risk(self):
        """Identifica riesgo: CxP y dividendo sin acuerdo offset"""
        
        entities = [
            HoldingEntity("parent", "Parent", "parent", "COL", balance=-50.0),  # CxP
        ]
        
        ownership_links = [
            HoldingEntity("sub", "Sub", "subsidiary", "MEX", balance=0),
        ]
        
        declared_dividends = {"sub": 50.0}  # Dividendo que recibirá parent
        tax_rates = {"COL": 0.0, "MEX": 0.0}
        
        # El análisis debería notar que Parent tiene CxP y recibirá dividendo
        # → Podría haberse offseteado (validar si hay acuerdo)


class TestMultiLevelCascade:
    """Cascada compleja: Parent → Sub A → Sub B → Sub C"""
    
    def test_three_level_cascade(self):
        """Cascada en 3 niveles de propiedad"""
        
        entities = [
            HoldingEntity("parent", "Parent", "parent", "COL"),
            HoldingEntity("sub_a", "Sub A", "subsidiary", "MEX"),
            HoldingEntity("sub_b", "Sub B", "subsidiary", "ESP"),
            HoldingEntity("sub_c", "Sub C", "subsidiary", "ARG"),
        ]
        
        ownership_links = [
            OwnershipLink("parent", "sub_a", 70.0),
            OwnershipLink("sub_a", "sub_b", 80.0),
            OwnershipLink("sub_b", "sub_c", 60.0),
        ]
        
        declared_dividends = {"sub_c": 100.0}
        tax_rates = {
            "COL": 0.10,
            "MEX": 0.15,
            "ESP": 0.20,
            "ARG": 0.25,
        }
        
        analysis = analyze_holdings_cascade(
            entities, ownership_links, declared_dividends, tax_rates
        )
        
        # Debe haber cascade desde Sub C → Sub B
        assert len(analysis.cascades) > 0
        cascades_to_b = [c for c in analysis.cascades if c.recipient_entity == "sub_b"]
        assert len(cascades_to_b) >= 1
        # Sub B recibe 60% de 100 = 60
        assert cascades_to_b[0].consolidation_elimination == 60.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
