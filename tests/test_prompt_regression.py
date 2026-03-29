from backend.services.prompt_service import render_prompt, validate_minimum_output


def test_prompt_render_chat_v1_injects_query_and_context() -> None:
    prompt, meta = render_prompt(
        "chat",
        query="Analiza riesgo de corte en ingresos",
        context="NIA 315 y NIA 330 aplican al area de ingresos.",
    )
    assert "Analiza riesgo de corte en ingresos" in prompt
    assert "NIA 315 y NIA 330" in prompt
    assert meta.get("prompt_version") == "v1"
    assert meta.get("prompt_id")


def test_prompt_regression_chat_minimum_output() -> None:
    output = (
        "Criterio: Existe riesgo de corte en ingresos.\n"
        "Accion inmediata: 1) Revisar facturas post-cierre. 2) Verificar devengo.\n"
        "Evidencia clave: contratos, facturas y guias de despacho."
    )
    ok, missing = validate_minimum_output(output, mode="chat")
    assert ok is True
    assert missing == []


def test_prompt_regression_memo_minimum_output() -> None:
    output = (
        "Riesgo global: medio.\n"
        "Materialidad: 120000.\n"
        "Recomendaciones: cerrar pruebas de detalle y confirmar coberturas."
    )
    ok, missing = validate_minimum_output(output, mode="memo")
    assert ok is True
    assert missing == []
