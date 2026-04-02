from __future__ import annotations

import textwrap

from core import configuracion


def _write_config(tmp_path, content: str) -> str:
    path = tmp_path / "config.test.yaml"
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return str(path)


def _reset(monkeypatch, path: str) -> None:
    monkeypatch.setenv("SOCIOAI_CONFIG", path)
    configuracion._CONFIG = None


def test_obtener_logging_config_normaliza_alias_legacy(tmp_path, monkeypatch):
    path = _write_config(
        tmp_path,
        """
        app:
          name: SocioAI
          version: "1.0.0"
          environment: development
          debug: true
        logging:
          nivel: warning
          archivo: logs/legacy.log
        materialidad:
          minimum_threshold: 1000
        rag:
          retrieval_method: similarity
          top_k: 5
          min_score: 0.6
        audit_areas:
          - code: "130"
            name: "CxC"
            weight: 0.5
        """,
    )
    _reset(monkeypatch, path)

    out = configuracion.obtener_logging_config()
    assert out["level"] == "WARNING"
    assert out["file"] == "logs/legacy.log"


def test_obtener_app_config_fuerza_debug_false_en_produccion(tmp_path, monkeypatch):
    path = _write_config(
        tmp_path,
        """
        app:
          name: SocioAI
          version: "1.0.0"
          environment: production
          debug: true
        logging:
          level: INFO
          file: logs/app.log
        materialidad:
          minimum_threshold: 1000
        rag:
          retrieval_method: similarity
          top_k: 5
          min_score: 0.6
        audit_areas:
          - code: "130"
            name: "CxC"
            weight: 0.5
        """,
    )
    _reset(monkeypatch, path)
    monkeypatch.delenv("SOCIOAI_DEBUG", raising=False)

    app_cfg = configuracion.obtener_app_config()
    assert app_cfg["environment"] == "production"
    assert app_cfg["debug"] is False


def test_obtener_audit_areas_config_lee_weight(tmp_path, monkeypatch):
    path = _write_config(
        tmp_path,
        """
        app:
          name: SocioAI
          version: "1.0.0"
          environment: development
          debug: false
        logging:
          level: INFO
          file: logs/app.log
        materialidad:
          minimum_threshold: 1000
        rag:
          retrieval_method: similarity
          top_k: 5
          min_score: 0.6
        audit_areas:
          - code: "130"
            name: "Cuentas por Cobrar"
            weight: 0.8
          - code: "200"
            name: "Patrimonio"
            weight: 0.6
        """,
    )
    _reset(monkeypatch, path)

    areas = configuracion.obtener_audit_areas_config()
    assert areas == [
        {"code": "130", "name": "Cuentas por Cobrar", "weight": 0.8},
        {"code": "200", "name": "Patrimonio", "weight": 0.6},
    ]


def test_cargar_config_falla_si_hay_codigo_duplicado_en_audit_areas(tmp_path, monkeypatch):
    path = _write_config(
        tmp_path,
        """
        app:
          name: SocioAI
          version: "1.0.0"
          environment: development
          debug: false
        logging:
          level: INFO
          file: logs/app.log
        materialidad:
          minimum_threshold: 1000
        rag:
          retrieval_method: similarity
          top_k: 5
          min_score: 0.6
        audit_areas:
          - code: "130"
            name: "CxC"
            weight: 0.5
          - code: "130"
            name: "Duplicado"
            weight: 0.4
        """,
    )
    _reset(monkeypatch, path)

    try:
        configuracion.cargar_config()
        assert False, "debio fallar por codigos duplicados"
    except ValueError as exc:
        assert "duplicate code values" in str(exc)


def test_cargar_config_falla_si_weight_fuera_de_rango(tmp_path, monkeypatch):
    path = _write_config(
        tmp_path,
        """
        app:
          name: SocioAI
          version: "1.0.0"
          environment: development
          debug: false
        logging:
          level: INFO
          file: logs/app.log
        materialidad:
          minimum_threshold: 1000
        rag:
          retrieval_method: similarity
          top_k: 5
          min_score: 0.6
        audit_areas:
          - code: "130"
            name: "CxC"
            weight: 1.5
        """,
    )
    _reset(monkeypatch, path)

    try:
        configuracion.cargar_config()
        assert False, "debio fallar por weight fuera de rango"
    except ValueError as exc:
        assert "less than or equal to 1" in str(exc)


def test_obtener_app_config_prioriza_socioai_env(tmp_path, monkeypatch):
    path = _write_config(
        tmp_path,
        """
        app:
          name: SocioAI
          version: "1.0.0"
          environment: development
          debug: false
        logging:
          level: INFO
          file: logs/app.log
        materialidad:
          minimum_threshold: 1000
        rag:
          retrieval_method: similarity
          top_k: 5
          min_score: 0.6
        audit_areas:
          - code: "130"
            name: "CxC"
            weight: 0.5
        """,
    )
    _reset(monkeypatch, path)
    monkeypatch.setenv("SOCIOAI_ENV", "production")

    app_cfg = configuracion.obtener_app_config()
    assert app_cfg["environment"] == "production"
