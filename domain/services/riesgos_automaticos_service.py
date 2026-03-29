from __future__ import annotations

from typing import Any

import pandas as pd


def _to_float(v: Any) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def _first_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols = set(df.columns)
    for c in candidates:
        if c in cols:
            return c
    return None


def detectar_riesgos_area(ws_base: dict) -> list[dict]:
    """
    ws_base: workspace del area generado por prepare_area_workspace.
    No rompe contratos existentes.
    """
    riesgos: list[dict] = []

    if not isinstance(ws_base, dict):
        return riesgos

    df = ws_base.get("area_df")
    area = ws_base.get("area_info", {}) if isinstance(ws_base.get("area_info", {}), dict) else {}
    materialidad_desempeno = _to_float(
        ws_base.get("materialidad_desempeno", ws_base.get("materialidad_ejecucion", 0))
    )

    perfil = ws_base.get("perfil", {}) if isinstance(ws_base.get("perfil", {}), dict) else {}
    sector = str(
        ws_base.get("sector")
        or perfil.get("cliente", {}).get("sector")
        or perfil.get("sector")
        or ""
    ).lower()

    # ==============================
    # 1. Activo con saldo negativo
    # ==============================
    if isinstance(df, pd.DataFrame) and not df.empty:
        tipo_col = _first_col(df, ["tipo", "tipo_cuenta", "grupo"])
        saldo_col = _first_col(df, ["saldo", "saldo_actual", "saldo_2025", "saldo_preliminar"])
        if tipo_col and saldo_col:
            tipo = df[tipo_col].astype(str).str.upper().str.strip()
            saldo = pd.to_numeric(df[saldo_col], errors="coerce").fillna(0.0)
            activos_negativos = df[(tipo == "ACTIVO") & (saldo < 0)]
            if not activos_negativos.empty:
                riesgos.append(
                    {
                        "nivel": "ALTO",
                        "tipo": "CLASIFICACION",
                        "descripcion": "Existen cuentas de activo con saldo acreedor.",
                        "accion_sugerida": "Revisar reclasificacion y deterioro conforme NIC 1 y NIIF aplicables.",
                    }
                )

    # ==============================
    # 2. Pasivo con saldo positivo
    # ==============================
    if isinstance(df, pd.DataFrame) and not df.empty:
        tipo_col = _first_col(df, ["tipo", "tipo_cuenta", "grupo"])
        saldo_col = _first_col(df, ["saldo", "saldo_actual", "saldo_2025", "saldo_preliminar"])
        if tipo_col and saldo_col:
            tipo = df[tipo_col].astype(str).str.upper().str.strip()
            saldo = pd.to_numeric(df[saldo_col], errors="coerce").fillna(0.0)
            pasivos_positivos = df[(tipo == "PASIVO") & (saldo > 0)]
            if not pasivos_positivos.empty:
                riesgos.append(
                    {
                        "nivel": "ALTO",
                        "tipo": "CLASIFICACION",
                        "descripcion": "Existen cuentas de pasivo con saldo deudor.",
                        "accion_sugerida": "Validar compensaciones indebidas o errores de registro.",
                    }
                )

    # ==============================
    # 3. Variacion > 30%
    # ==============================
    variacion = area.get("variacion_pct", ws_base.get("variacion_pct", 0))
    try:
        variacion = float(variacion)
    except Exception:
        variacion = 0.0

    if abs(variacion) > 0.30:
        riesgos.append(
            {
                "nivel": "MEDIO",
                "tipo": "VARIACION",
                "descripcion": f"Variacion significativa del {variacion:.2%}.",
                "accion_sugerida": "Solicitar explicacion a la administracion y validar con evidencia.",
            }
        )

    # ==============================
    # 4. Saldo alto sin cobertura
    # ==============================
    saldo = abs(_to_float(area.get("saldo", ws_base.get("saldo_total", 0))))
    cobertura = _to_float(area.get("cobertura", ws_base.get("coverage", 0)))

    if materialidad_desempeno > 0 and saldo > (3 * materialidad_desempeno) and cobertura == 0:
        riesgos.append(
            {
                "nivel": "ALTO",
                "tipo": "COBERTURA",
                "descripcion": "Area material sin procedimientos ejecutados.",
                "accion_sugerida": "Disenar procedimientos sustantivos o pruebas de control inmediatamente.",
            }
        )

    # ==============================
    # 5. Area esperada NO_PRESENTE
    # ==============================
    codigo_ls = str(area.get("codigo_ls", ws_base.get("codigo_ls", ""))).strip()
    estado = str(area.get("estado", ws_base.get("estado_presencia", ""))).strip().upper()

    areas_esperadas = {
        "holding": ["14", "200"],
        "comercial": ["110", "1500", "1600"],
        "servicios": ["1500", "1600"],
    }

    if estado in {"NO_PRESENTE", "ABSENT"} and codigo_ls in areas_esperadas.get(sector, []):
        riesgos.append(
            {
                "nivel": "MEDIO",
                "tipo": "OMISION",
                "descripcion": f"Area {codigo_ls} no presente pero esperada para sector {sector}.",
                "accion_sugerida": "Validar si existe omision en el TB o clasificacion incorrecta.",
            }
        )

    return riesgos
