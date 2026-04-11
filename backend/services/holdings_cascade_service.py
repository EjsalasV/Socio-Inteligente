"""
Holdings Subsidiary Cascade Analysis Engine

Valida flujos de dividendos en estructuras multi-nivel de holdings.

Ejemplo:
    Parent (60%) → Subsidiary A (80%) → Subsidiary B
    
    Subsidiary B declara dividendo $100:
    - Subsidiary A recibe: 80% × $100 = $80 (menos impuesto)
    - Parent recibe: 60% × $80 (neto) = $48 (menos impuestos)
    
    En consolidado: $100 se elimina (es inter-company)
    En individual: validar que cálculo es correcto
"""

from dataclasses import dataclass, field
from typing import Optional
from pydantic import BaseModel


@dataclass
class HoldingEntity:
    """Representa una entidad en la estructura de holdings"""
    entity_id: str  # Ej: "subsidiary_a"
    name: str  # Ej: "Subsidiary A Corp"
    ownership_type: str  # "parent", "subsidiary", "joint_venture"
    tax_jurisdiction: str  # "COL", "MEX", "ESP"
    balance: float = 0.0  # CxC/CxP con otros holdings


@dataclass
class OwnershipLink:
    """Representa relación de propiedad entre entidades"""
    owner_id: str  # Quién posee
    subsidiary_id: str  # La que se posee
    ownership_percentage: float  # 0-100
    voting_rights: float = 100.0  # Puede diferir de ownership
    direct_control: bool = True  # Vs. indirect through another


class DividendCascade(BaseModel):
    """Flujo de dividendo en cascada"""
    declaring_entity: str
    dividend_amount: float
    recipient_entity: str
    ownership_percentage: float
    tax_rate: float = 0.0
    received_amount: float  # After tax
    consolidation_elimination: float  # Amount to eliminate


class ConsolidationElimination(BaseModel):
    """Eliminación requerida en consolidado"""
    elimination_type: str  # "dividend", "cxc_balance", "goodwill"
    amount: float
    debit_account: str  # Account affected
    credit_account: str
    reason: str


class HoldingsStructureAnalysis(BaseModel):
    """Análisis completo de estructura de holdings"""
    parent_entity: str
    total_entities: int
    total_ownership_links: int
    has_cycles: bool  # SÍ si hay circular ownership
    cycles_detected: list[list[str]] = field(default_factory=list)
    cascades: list[DividendCascade] = field(default_factory=list)
    eliminations: list[ConsolidationElimination] = field(default_factory=list)
    risks_identified: list[str] = field(default_factory=list)


def analyze_holdings_cascade(
    entities: list[HoldingEntity],
    ownership_links: list[OwnershipLink],
    declared_dividends: dict[str, float],
    tax_rates: dict[str, float],
) -> HoldingsStructureAnalysis:
    """
    Analiza estructura de holdings y calcula cascadas de dividendos.
    
    Args:
        entities: Lista de entidades
        ownership_links: Relaciones de propiedad
        declared_dividends: {entity_id: dividend_amount}
        tax_rates: {jurisdiction: tax_rate}
    
    Returns:
        Análisis completo con cascadas y eliminaciones
    """
    
    # Detectar cycles
    cycles = _detect_cycles(ownership_links)
    
    # Calcular cascadas de dividendos
    cascades = _calculate_dividend_cascades(
        entities, ownership_links, declared_dividends, tax_rates
    )
    
    # Calcular eliminaciones de consolidación
    eliminations = _calculate_consolidation_eliminations(cascades)
    
    # Identificar riesgos
    risks = _identify_risks(
        entities, ownership_links, cascades, cycles
    )
    
    return HoldingsStructureAnalysis(
        parent_entity=_find_parent_entity(ownership_links),
        total_entities=len(entities),
        total_ownership_links=len(ownership_links),
        has_cycles=len(cycles) > 0,
        cycles_detected=cycles,
        cascades=cascades,
        eliminations=eliminations,
        risks_identified=risks,
    )


def _detect_cycles(ownership_links: list[OwnershipLink]) -> list[list[str]]:
    """Detecta ciclos en estructura de ownership (A owns B, B owns A)"""
    # Building adjacency list
    graph = {}
    for link in ownership_links:
        if link.owner_id not in graph:
            graph[link.owner_id] = []
        graph[link.owner_id].append(link.subsidiary_id)
    
    cycles = []
    
    def dfs(node, path, visited):
        if node in visited:
            if node in path:
                # Encontró ciclo
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
            return
        
        visited.add(node)
        path.append(node)
        
        for neighbor in graph.get(node, []):
            dfs(neighbor, path.copy(), visited.copy())
    
    for entity_id in graph:
        dfs(entity_id, [], set())
    
    # Deduplicate cycles
    unique_cycles = []
    for cycle in cycles:
        # Normalize cycle
        normalized = sorted(cycle[:-1])
        is_duplicate = False
        for existing in unique_cycles:
            if sorted(existing[:-1]) == normalized:
                is_duplicate = True
                break
        if not is_duplicate:
            unique_cycles.append(cycle)
    
    return unique_cycles


def _calculate_dividend_cascades(
    entities: list[HoldingEntity],
    ownership_links: list[OwnershipLink],
    declared_dividends: dict[str, float],
    tax_rates: dict[str, float],
) -> list[DividendCascade]:
    """Calcula cascada de dividendos a través de estructura"""
    
    cascades = []
    entity_dict = {e.entity_id: e for e in entities}
    
    # Para cada dividendo declarado
    for declaring_entity, dividend_amount in declared_dividends.items():
        declaring_entity_obj = entity_dict.get(declaring_entity)
        if not declaring_entity_obj:
            continue
        
        # Encontrar todos los owners de esta entidad (directos e indirectos)
        # Direct owners
        direct_owners = [
            link for link in ownership_links
            if link.subsidiary_id == declaring_entity
        ]
        
        for owner_link in direct_owners:
            owner_entity = entity_dict.get(owner_link.owner_id)
            if not owner_entity:
                continue
            
            # Calcular monto recibido (post-tax)
            tax_rate = tax_rates.get(
                owner_entity.tax_jurisdiction, 0.0
            )
            received_amount = dividend_amount * owner_link.ownership_percentage / 100 * (1 - tax_rate)
            
            # Monto a eliminar en consolidado (es inter-company)
            consolidated_elimination = dividend_amount * owner_link.ownership_percentage / 100
            
            cascade = DividendCascade(
                declaring_entity=declaring_entity,
                dividend_amount=dividend_amount,
                recipient_entity=owner_link.owner_id,
                ownership_percentage=owner_link.ownership_percentage,
                tax_rate=tax_rate,
                received_amount=received_amount,
                consolidation_elimination=consolidated_elimination,
            )
            cascades.append(cascade)
    
    return cascades


def _calculate_consolidation_eliminations(
    cascades: list[DividendCascade],
) -> list[ConsolidationElimination]:
    """Calcula eliminaciones necesarias en consolidado"""
    
    eliminations = []
    
    for cascade in cascades:
        # Inter-company CxC debe eliminarse
        elimination = ConsolidationElimination(
            elimination_type="dividend_cascade",
            amount=cascade.consolidation_elimination,
            debit_account="280 - Dividends Payable (to parent)",  # Subsidiary side
            credit_account="4105 - Dividend Income (parent)",  # Parent side
            reason=f"Inter-company dividend: {cascade.declaring_entity} → {cascade.recipient_entity}",
        )
        eliminations.append(elimination)
    
    return eliminations


def _find_parent_entity(ownership_links: list[OwnershipLink]) -> str:
    """Encuentra la entidad parent (no es subsidiary de nadie)"""
    subsidiaries = {link.subsidiary_id for link in ownership_links}
    owners = {link.owner_id for link in ownership_links}
    
    # Parent es quien es owner pero no subsidiary
    potential_parents = owners - subsidiaries
    return list(potential_parents)[0] if potential_parents else "unknown"


def _identify_risks(
    entities: list[HoldingEntity],
    ownership_links: list[OwnershipLink],
    cascades: list[DividendCascade],
    cycles: list[list[str]],
) -> list[str]:
    """Identifica riesgos en estructura de holdings"""
    
    risks = []
    
    # Risk 1: Ciclos de ownership
    if cycles:
        risks.append(
            f"🚨 CICLOS DETECTADOS: {cycles} - Puede causar confusión en consolidación"
        )
    
    # Risk 2: Dividendos sin justificación (entidad sin ganancia pero declara)
    for cascade in cascades:
        if cascade.consolidation_elimination > 0 and cascade.received_amount < 0:
            risks.append(
                f"⚠️ {cascade.declaring_entity} declara dividendo pero recibe cantidad negativa"
            )
    
    # Risk 3: Tax arbitrage (alta tasa en recipient)
    high_tax_recipients = [
        c for c in cascades if c.tax_rate > 0.30  # >30% tax
    ]
    if high_tax_recipients:
        risks.append(
            f"⚠️ Alto impuesto en recipients: {[c.recipient_entity for c in high_tax_recipients]}"
        )
    
    # Risk 4: Complex multi-level (>3 levels) puede ser fraud risk
    def count_levels(entity_id, links, visited=None):
        if visited is None:
            visited = set()
        if entity_id in visited:
            return 0
        visited.add(entity_id)
        
        owners = [l.owner_id for l in links if l.subsidiary_id == entity_id]
        if not owners:
            return 1
        return 1 + max(count_levels(o, links, visited) for o in owners)
    
    # Risk 5: Offset without clear agreement
    entity_balances = {e.entity_id: e.balance for e in entities}
    for cascade in cascades:
        if cascade.received_amount > 0 and cascade.recipient_entity in entity_balances:
            balance = entity_balances[cascade.recipient_entity]
            if balance < 0 and abs(balance) >= cascade.received_amount * 0.5:
                risks.append(
                    f"⚠️ {cascade.recipient_entity} tiene CxP ({balance}) y recibirá dividendo ({cascade.received_amount}): Validar offset agreement"
                )
    
    return risks


def validate_offset_agreement(
    dividend_receivable: float,
    cxp_payable: float,
    offset_allowed: bool,
) -> tuple[bool, str]:
    """
    Valida si offset de dividendo contra obligación es permitido.
    
    Returns:
        (is_valid, reason)
    """
    
    if not offset_allowed:
        return False, "No offset agreement documented"
    
    if dividend_receivable <= 0:
        return False, "Dividend amount must be positive"
    
    if cxp_payable <= 0:
        return False, "CxP amount must be positive"
    
    if abs(dividend_receivable - cxp_payable) > 0.01:  # Allow rounding
        return False, f"Amounts don't match: dividend {dividend_receivable} vs CxP {cxp_payable}"
    
    return True, "Offset is valid"
