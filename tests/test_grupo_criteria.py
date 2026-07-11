from __future__ import annotations

from backend.services.grupo_criteria_service import (
    build_analysis_criteria_block,
    build_grupo_context_block,
    detect_grupos_from_accounts,
    get_grupo_criteria,
    list_grupos,
    load_mapa,
    resolve_grupo,
)


def test_mapa_carga_y_tiene_grupos_universales():
    mapa = load_mapa()
    assert isinstance(mapa, dict)
    grupos = mapa.get("grupos")
    assert isinstance(grupos, dict)
    for esperado in ["inventarios", "nomina", "ingresos", "costo_ventas_gastos", "impuestos_activos"]:
        assert esperado in grupos, f"grupo {esperado} falta en el mapa"


def test_list_grupos_expone_normas_y_estado():
    grupos = list_grupos()
    assert grupos["inventarios"]["normas"], "inventarios debe tener normas"
    assert grupos["inventarios"]["estado"] == "construido"


def test_resolve_grupo_por_codigo():
    assert resolve_grupo(area_codigo="150") == "inventarios"
    assert resolve_grupo(area_codigo="140") == "efectivo"
    assert resolve_grupo(area_codigo="130") == "cxc"
    # prefijo en ambas direcciones: "1500" del TB del cliente → "150" del mapa
    assert resolve_grupo(area_codigo="1500") == "inventarios"


def test_resolve_grupo_por_nombre_de_cuenta():
    assert resolve_grupo(area_nombre="Inventario de mercadería") == "inventarios"
    assert resolve_grupo(area_nombre="Sueldos y salarios") == "nomina"
    assert resolve_grupo(area_nombre="Décimo tercer sueldo por pagar") == "nomina"
    assert resolve_grupo(area_nombre="Jubilación patronal") == "beneficios_empleados"
    assert resolve_grupo(area_nombre="Costo de ventas") == "costo_ventas_gastos"
    assert resolve_grupo(area_nombre="cuenta rara sin match") == ""


def test_get_grupo_criteria_carga_modulo_construido():
    data = get_grupo_criteria("inventarios")
    assert data["found"] is True
    assert "NIC 2" in str(data["normas"])
    assert "Riesgos recurrentes" in data["content"]
    vinculos_activos = [v for v in data["vinculos"] if v["activo"]]
    assert len(vinculos_activos) >= 2, "inventarios debe tener vínculos activos"


def test_get_grupo_criteria_ingresos_usa_override_niif15():
    data = get_grupo_criteria("ingresos")
    assert data["found"] is True
    assert "niif15" in data["source_path"]
    assert "NIIF 15" in data["content"]


def test_get_grupo_criteria_pendiente_no_rompe():
    data = get_grupo_criteria("ppe")
    assert data["found"] is False
    assert isinstance(data["vinculos"], list)


def test_build_grupo_context_block_incluye_vinculos_activos():
    block = build_grupo_context_block("inventarios")
    assert "CHEQUEOS CRUZADOS OBLIGATORIOS" in block
    assert "ingresos" in block
    assert len(block) <= 6100


def test_detect_grupos_desde_cuentas_de_tb():
    cuentas = [
        "Caja general",
        "Bancos",
        "Inventario de producto terminado",
        "Inventario materia prima",
        "Sueldos por pagar",
        "Ventas locales",
        "Costo de ventas",
        "Impuesto a la renta por pagar",
    ]
    grupos = detect_grupos_from_accounts(cuentas)
    assert "inventarios" in grupos
    assert "nomina" in grupos or "ingresos" in grupos


def test_build_analysis_criteria_block_para_analizador():
    cuentas = ["Inventario mercadería", "Ventas", "Sueldos", "Costo de ventas"]
    block = build_analysis_criteria_block(cuentas)
    assert "EXPERT AUDIT CRITERIA" in block
    assert "CHEQUEOS CRUZADOS" in block
    assert len(block) <= 15000


def test_build_analysis_criteria_block_vacio_sin_match():
    assert build_analysis_criteria_block([]) == ""
    assert build_analysis_criteria_block(["cuenta inexistente xyz"]) == ""


def test_analyzer_formatea_con_criterio():
    from backend.services.intelligent_analyzer_service import (
        _format_financial_data_for_analysis,
    )

    data = {
        "sector": "comercial",
        "balance_trial": {
            "Inventario de mercadería": 150000.0,
            "Ventas": -420000.0,
            "Costo de ventas": 260000.0,
            "Sueldos y beneficios": 80000.0,
        },
    }
    formatted = _format_financial_data_for_analysis(data)
    assert "EXPERT AUDIT CRITERIA" in formatted
    assert "TOP ACCOUNTS" in formatted


def test_chat_enriquece_contexto_con_grupo():
    from backend.services.rag_chat_service import _enrich_context_with_expert_criteria

    context, used = _enrich_context_with_expert_criteria(
        "", "", "", query="¿Cómo audito el inventario de este cliente?"
    )
    assert used is True
    assert "GRUPO DEL BALANCE" in context
